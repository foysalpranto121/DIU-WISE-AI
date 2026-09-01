import hashlib

import requests
from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import User, db


class PasswordResetService:
    """Issues, verifies and delivers password reset tokens.

    Tokens are signed with the app SECRET_KEY via itsdangerous, so nothing is
    stored in the database. Two properties matter:

    Expiry: enforced at verification time through max_age, configured by
    PASSWORD_RESET_MAX_AGE (1 hour by default).

    Single use: the token embeds a fingerprint of the user's current
    password_hash. Resetting the password changes the hash, which changes the
    fingerprint, so a token that has been used once can never verify again.
    The same mechanism also invalidates outstanding reset links whenever the
    password changes by any other means.

    Delivery goes over Brevo's HTTP API rather than their SMTP relay. Render's
    free instances block outbound traffic to SMTP ports 25, 465 and 587, so an
    SMTP connect from production is blackholed rather than refused and hangs
    until gunicorn kills the worker. The HTTP API is reached on 443, which is
    not blocked, and every request carries an explicit timeout.
    """

    SALT = "password-reset"
    ENDPOINT = "https://api.brevo.com/v3/smtp/email"

    def _serializer(self) -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=self.SALT)

    def _fingerprint(self, user: User) -> str:
        """Short digest of the current password hash, empty hash included."""
        material = (user.password_hash or "no-password").encode("utf-8")
        return hashlib.sha256(material).hexdigest()[:16]

    def generate_token(self, user: User) -> str:
        """Return a signed reset token for this user."""
        return self._serializer().dumps({"uid": user.id, "fp": self._fingerprint(user)})

    def verify_token(self, token: str):
        """Return the User the token belongs to, or None if it is invalid.

        Invalid covers: tampered or malformed tokens, tokens older than the
        configured max age, tokens for a deleted user, and tokens issued
        before the most recent password change.
        """
        max_age = current_app.config["PASSWORD_RESET_MAX_AGE"]
        try:
            data = self._serializer().loads(token, max_age=max_age)
        except (BadSignature, SignatureExpired):
            return None
        if not isinstance(data, dict):
            return None
        user = db.session.get(User, data.get("uid"))
        if user is None or data.get("fp") != self._fingerprint(user):
            return None
        return user

    def _body(self, user: User, reset_url: str) -> str:
        """Plain text of the reset email."""
        return (
            f"Hello {user.full_name},\n\n"
            f"Someone requested a password reset for your DIU WISE AI "
            f"account. If this was you, open the link below to choose a "
            f"new password. The link is valid for one hour and works "
            f"once.\n\n{reset_url}\n\n"
            f"If you did not request this, you can ignore this email. "
            f"Your password will not change.\n\n"
            f"DIU WISE AI, Daffodil International University"
        )

    def send_reset_email(self, user: User) -> bool:
        """Email the reset link. Returns True when Brevo accepted the message.

        With no BREVO_API_KEY configured nothing is sent. That is logged
        loudly, and in development the link itself is logged so the flow can
        be exercised without credentials.
        """
        token = self.generate_token(user)
        reset_url = url_for("auth.reset_password", token=token, _external=True)

        api_key = current_app.config["BREVO_API_KEY"]
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        if not api_key or not sender:
            current_app.logger.warning(
                "BREVO_API_KEY or MAIL_DEFAULT_SENDER is not configured. "
                "Password reset email to %s was NOT sent.",
                user.email,
            )
            if current_app.config.get("DEVELOPMENT"):
                current_app.logger.warning("Development reset link: %s", reset_url)
            return False

        payload = {
            "sender": {"email": sender, "name": "DIU WISE AI"},
            "to": [{"email": user.email, "name": user.full_name}],
            "subject": "Reset your DIU WISE AI password",
            "textContent": self._body(user, reset_url),
        }

        response = requests.post(
            self.ENDPOINT,
            json=payload,
            headers={"api-key": api_key, "accept": "application/json"},
            timeout=current_app.config["BREVO_API_TIMEOUT"],
        )
        # 201 is an immediate send, 202 a scheduled one. Anything else is a
        # failure and is raised so the caller can log it; the route swallows
        # it deliberately, to keep the response identical for every address.
        if response.status_code not in (201, 202):
            raise RuntimeError(
                f"Brevo API returned {response.status_code}: {response.text[:200]}"
            )
        return True
