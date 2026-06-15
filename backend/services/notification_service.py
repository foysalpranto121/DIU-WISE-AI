import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv("MAIL_SERVER", "localhost")
        self.smtp_port = int(os.getenv("MAIL_PORT", 1025))
        self.smtp_user = os.getenv("MAIL_USERNAME", "")
        self.smtp_password = os.getenv("MAIL_PASSWORD", "")
        self.university_email = os.getenv("UNIVERSITY_ALERT_EMAIL", "wellness-alerts@daffodilvarsity.edu.bd")
        
        # Ensure log folder exists for mock logging fallback
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def send_emergency_alert(self, user, journal_text, risk_reason):
        """Sends emergency notification email to student's guardian and university authority."""
        guardian_email = user.guardian_email
        guardian_name = user.guardian_name or "Guardian"
        student_name = user.full_name
        student_id = user.student_id or "N/A"
        
        subject = f"[DIU WISE] EMERGENCY WELLBEING ALERT: {student_name} ({student_id})"
        
        body_text = (
            f"Dear {guardian_name},\n\n"
            f"This is an automated emergency notification from the Daffodil International University (DIU) Student Wellbeing Portal.\n\n"
            f"Our student wellbeing system has flagged an entry submitted by {student_name} (ID: {student_id}) as representing a critical risk level.\n"
            f"Trigger Event / Reason: {risk_reason}\n"
            f"Journal Excerpt:\n\"{journal_text}\"\n\n"
            f"We strongly recommend checking in on {student_name} immediately.\n"
            f"If you are unable to contact them, please reach out to DIU Campus Security or the local crisis support hotline at 988.\n\n"
            f"Sincerely,\n"
            f"DIU Student Wellness & Mental Support Team"
        )
        
        recipients = [self.university_email]
        if guardian_email:
            recipients.append(guardian_email)
            
        # Try sending via SMTP
        sent_successfully = False
        if self.smtp_user and self.smtp_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_user
                msg['To'] = ", ".join(recipients)
                msg['Subject'] = subject
                msg.attach(MIMEText(body_text, 'plain'))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_port == 587:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, recipients, msg.as_string())
                sent_successfully = True
                print(f"[ALERT EMAIL] Successfully sent email to {recipients}")
            except Exception as e:
                print(f"[ALERT EMAIL] Failed to send via SMTP: {e}. Falling back to log file.")
        
        # Fallback to local logs (for local development or when credentials aren't set)
        if not sent_successfully:
            log_file_path = os.path.join(self.log_dir, "emergency_alerts.log")
            try:
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_entry = (
                        f"==================================================\n"
                        f"TIMESTAMP: {datetime.utcnow().isoformat()}\n"
                        f"FROM: DIU WISE System\n"
                        f"TO: {', '.join(recipients)}\n"
                        f"SUBJECT: {subject}\n"
                        f"BODY:\n{body_text}\n"
                        f"==================================================\n\n"
                    )
                    log_file.write(log_entry)
                print(f"[ALERT EMAIL] Logged emergency alert to {log_file_path}")
            except Exception as ex:
                print(f"[ALERT EMAIL] Double fallback logging failure: {ex}")
                
        return sent_successfully
