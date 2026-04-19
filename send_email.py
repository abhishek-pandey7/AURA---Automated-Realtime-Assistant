import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email():
    # Configuration
    # Note: In a real scenario, use environment variables for security
    sender_email = os.environ.get("EMAIL_USER") or "your_email@gmail.com"
    sender_password = os.environ.get("EMAIL_PASS") or "your_app_password"
    receiver_email = "john@example.com"
    subject = "Meeting Tomorrow"
    body = "The standup is at 10am"

    # Create the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.send_message(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    send_email()
