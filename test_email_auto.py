import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import os

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- Firebase setup ---
cred = credentials.Certificate("serviceAccountKey.json")  # JSON file in your project folder
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://school-attendance-63ead-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

def send_email(to_email, student_name, grade, timestamp):
    """
    Send email notification using Gmail SMTP (FREE)
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = f"Check-in Student {student_name}"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff;">
                <!-- AI-niform Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: bold;">AI-niform</h1>
                    <p style="color: #e8f4fd; margin: 5px 0 0 0; font-size: 14px;">Smart School Management System</p>
                </div>
                
                <h2 style="color: #2c3e50; text-align: center; margin-top: 0;">Student Check-in Notification</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
                    <h3 style="color: #27ae60; margin-top: 0;">Student Successfully Checked In</h3>
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Grade Level:</strong> {grade}</p>
                    <p><strong>Check-in Time:</strong> {timestamp}</p>
                </div>
                
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2980b9;">
                    <p style="margin: 0; color: #2980b9;">
                        <strong>RFID System:</strong> This notification was sent automatically when your child's RFID card was scanned at the school entrance.
                    </p>
                </div>
                
                <!-- AI-niform Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                        <strong>AI-niform School Management System</strong><br>
                        This is an automated message from the RFID Attendance System.<br>
                        Please do not reply to this email.
                    </p>
                    <p style="color: #667eea; font-size: 10px; margin: 10px 0 0 0;">
                        Powered by AI-niform Technology
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()  # Enable encryption
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        server.quit()
        
        print(f"✅ Email sent to {to_email}: {student_name} ({grade}) checked in at {timestamp}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

# --- Main execution with predefined values ---
print("Email Notification System")
print("=" * 40)
print("Sending test email notification with predefined values")

# Predefined test values
destination_email = "ichiroyamazaki123@gmail.com"
student_name = "Ichiro Yamazaki"
student_grade = "Grade 10"

# Get current timestamp in GMT+8 (Philippines timezone)
ph_tz = pytz.timezone('Asia/Manila')
timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S GMT+8")

print(f"\nSending email to: {destination_email}")
print(f"Student: {student_name} ({student_grade})")
print(f"Time: {timestamp}")
print("-" * 40)

# Send email notification
success = send_email(
    destination_email, 
    student_name, 
    student_grade, 
    timestamp
)

if success:
    print(f"📧 Email notification sent successfully!")
else:
    print(f"❌ Failed to send email notification")
