import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

def send_test_email():
    """
    Send a test email using Gmail SMTP
    """
    # Ask user for destination email
    print("Enter the destination email address:")
    test_email = input("Email: ").strip()
    
    # Validate email format (basic check)
    if "@" not in test_email or "." not in test_email:
        print("❌ Invalid email format. Please enter a valid email address.")
        return False
    
    test_student_name = "John Doe"
    test_grade = "Grade 10"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = test_email
        msg['Subject'] = f"Test Email - School Attendance Alert - {test_student_name}"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2c3e50; text-align: center;">🏫 School Attendance Notification</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #27ae60; margin-top: 0;">✅ Student Checked In</h3>
                    <p><strong>Student Name:</strong> {test_student_name}</p>
                    <p><strong>Grade Level:</strong> {test_grade}</p>
                    <p><strong>Check-in Time:</strong> {timestamp}</p>
                </div>
                
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2980b9;">
                        <strong>📱 RFID System:</strong> This is a TEST notification from your RFID attendance system.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                        This is a test message from the School RFID Attendance System.<br>
                        If you received this email, the system is working correctly! 🎉
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        print("Sending test email via Gmail SMTP...")
        print(f"From: {EMAIL_SENDER}")
        print(f"To: {test_email}")
        print(f"Subject: Test Email - School Attendance Alert")
        print("-" * 50)
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()  # Enable encryption
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, test_email, text)
        server.quit()
        
        print("Test email sent successfully!")
        print("Check your inbox (and spam folder) for the test email.")
        return True
        
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're using your Gmail address")
        print("2. Use an App Password instead of your regular Gmail password")
        print("3. Enable 2-Factor Authentication on your Gmail account")
        print("4. Check if 'Less secure app access' is enabled (if not using App Password)")
        return False

def setup_instructions():
    """
    Display setup instructions for Gmail SMTP
    """
    print("Gmail SMTP Setup Instructions")
    print("=" * 50)
    print("1. Use your Gmail address as EMAIL_SENDER")
    print("2. Generate an App Password:")
    print("   - Go to Google Account settings")
    print("   - Security > 2-Step Verification > App passwords")
    print("   - Generate a password for 'Mail'")
    print("   - Use this password as EMAIL_PASSWORD")
    print("3. Enable 2-Factor Authentication on your Gmail account")
    print("4. Update the credentials in this script")
    print("=" * 50)
    print()

if __name__ == "__main__":
    print("Email Test Script for RFID Attendance System")
    print("=" * 60)
    print("This script tests email notifications using Gmail SMTP (FREE)")
    print()
    
    # Check if credentials are still placeholders
    if EMAIL_SENDER == "your_email@gmail.com" or EMAIL_PASSWORD == "your_app_password":
        print("Please update your Gmail credentials first!")
        print()
        setup_instructions()
    else:
        send_test_email()
