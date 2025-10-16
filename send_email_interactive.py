import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

def send_email_to_address(destination_email, student_name="John Doe", grade="Grade 10"):
    """
    Send email to a specific address
    """
    # Get current time in GMT+8 (Philippines timezone)
    ph_tz = pytz.timezone('Asia/Manila')
    timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S GMT+8")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = destination_email
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
        server.sendmail(EMAIL_SENDER, destination_email, text)
        server.quit()
        
        print(f"Email sent to {destination_email}: {student_name} ({grade}) checked in at {timestamp}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def get_user_input():
    """
    Get email address and student info from user
    """
    print("Email Notification System")
    print("=" * 40)
    print("This will send a test email notification")
    print()
    
    # Ask for destination email
    while True:
        destination_email = input("Enter the destination email address: ").strip()
        if "@" in destination_email and "." in destination_email:
            break
        print("Invalid email format. Please enter a valid email address.")
    
    # Ask for student information
    print()
    student_name = input("Enter student name: ").strip() or "John Doe"
    student_grade = input("Enter grade level: ").strip() or "Grade 10"
    
    return destination_email, student_name, student_grade

if __name__ == "__main__":
    try:
        destination_email, student_name, student_grade = get_user_input()
        
        print(f"\nSending email to: {destination_email}")
        print(f"Student: {student_name} ({student_grade})")
        print("-" * 40)
        
        success = send_email_to_address(destination_email, student_name, student_grade)
        
        if success:
            print("Email sent successfully!")
            print("Check the recipient's inbox (and spam folder).")
        else:
            print("Failed to send email.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

