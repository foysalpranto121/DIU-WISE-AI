import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class AdvisorAlertService:
    def should_send(self, user) -> bool:
        if not user.advisor_alert_consent:
            return False
        if not user.faculty_advisor_email:
            return False
        # Rate-limit: once per 24 hours
        if user.advisor_alert_sent_at:
            if datetime.utcnow() - user.advisor_alert_sent_at < timedelta(hours=24):
                return False
        return True

    def send_alert(self, user, burnout_data: dict, db_session) -> bool:
        if not self.should_send(user):
            return False

        status = burnout_data.get("status", "Needs Support")
        confidence = burnout_data.get("confidence", 0)

        subject = f"[DIU WISE] Wellbeing Alert: {user.full_name} ({user.student_id or 'N/A'})"
        body = f"""Dear Faculty Advisor,

This is an automated wellbeing alert from the DIU WISE AI Platform.

Student Details
───────────────
Name        : {user.full_name}
Student ID  : {user.student_id or 'N/A'}
Department  : {user.department or 'N/A'}
Email       : {user.email}
Semester    : {user.semester or 'N/A'}

Detected Wellbeing Status : {status}
System Confidence         : {confidence:.0%}

The AI wellness system has flagged this student for elevated stress or burnout risk.
We recommend reaching out to check in on their academic and personal wellbeing.

This alert was sent with the student's explicit consent via the DIU WISE platform.
Please treat all information with full confidentiality.

— DIU WISE AI Platform
  Daffodil International University
"""
        sent = False
        try:
            mail_server = os.getenv("MAIL_SERVER")
            mail_user = os.getenv("MAIL_USERNAME")
            mail_pass = os.getenv("MAIL_PASSWORD")
            mail_port = int(os.getenv("MAIL_PORT", 587))

            if mail_server and mail_user and mail_pass:
                msg = MIMEMultipart()
                msg["From"] = mail_user
                msg["To"] = user.faculty_advisor_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                with smtplib.SMTP(mail_server, mail_port) as server:
                    server.starttls()
                    server.login(mail_user, mail_pass)
                    server.send_message(msg)
                sent = True
        except Exception as e:
            print(f"[AdvisorAlert] Email failed: {e}")

        # Always log, whether email succeeded or not
        os.makedirs("logs", exist_ok=True)
        with open("logs/advisor_alerts.log", "a", encoding="utf-8") as f:
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"[{ts}] {user.full_name} ({user.student_id}) "
                f"→ {user.faculty_advisor_email} | status={status} | email_sent={sent}\n"
            )

        user.advisor_alert_sent_at = datetime.utcnow()
        db_session.commit()
        return True
