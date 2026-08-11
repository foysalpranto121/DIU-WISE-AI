import hashlib

from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from extensions import mail
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
    """

    SALT = "password-reset"

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

    def send_reset_email(self, user: User) -> bool:
        """Email the reset link. Returns True when handed to the SMTP relay.

        With MAIL_SUPPRESS_SEND active (no Brevo credentials configured) no
        mail leaves the machine. That is logged loudly, and in development the
        link itself is logged so the flow can be exercised without SMTP.
        """
        token = self.generate_token(user)
        reset_url = url_for("auth.reset_password", token=token, _external=True)

        msg = Message(
            subject="Reset your DIU WISE AI password",
            recipients=[user.email],
            body=(
                f"Hello {user.full_name},\n\n"
                f"Someone requested a password reset for your DIU WISE AI "
                f"account. If this was you, open the link below to choose a "
                f"new password. The link is valid for one hour and works "
                f"once.\n\n{reset_url}\n\n"
                f"If you did not request this, you can ignore this email. "
                f"Your password will not change.\n\n"
                f"DIU WISE AI, Daffodil International University"
            ),
        )

        suppressed = current_app.config.get("MAIL_SUPPRESS_SEND", False)
        if suppressed:
            current_app.logger.warning(
                "Brevo SMTP credentials are not configured "
                "(BREVO_SMTP_LOGIN / BREVO_SMTP_PASSWORD). Password reset "
                "email to %s was NOT sent.",
                user.email,
            )
            if current_app.config.get("DEVELOPMENT"):
                current_app.logger.warning("Development reset link: %s", reset_url)

        mail.send(msg)
        return not suppressed
