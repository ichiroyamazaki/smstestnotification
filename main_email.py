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

def send_email(to_email, student_name, grade, timestamp, action_type="check-in", recipient_type="student"):
    """
    Send email notification using Gmail SMTP (FREE)
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = f"Student {action_type.title()} - {student_name}"
        
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
                
                <h2 style="color: #2c3e50; text-align: center; margin-top: 0;">{'Student' if recipient_type == 'student' else 'Parent'} {action_type.title()} Notification</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {'#27ae60' if action_type == 'check-in' else '#e74c3c'};">
                    <h3 style="color: {'#27ae60' if action_type == 'check-in' else '#e74c3c'}; margin-top: 0;">{'You have successfully' if recipient_type == 'student' else 'Your child has successfully'} {'checked in' if action_type == 'check-in' else 'checked out'}</h3>
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Grade Level:</strong> {grade}</p>
                    <p><strong>{'Check-in' if action_type == 'check-in' else 'Check-out'} Time:</strong> {timestamp}</p>
                </div>
                
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2980b9;">
                    <p style="margin: 0; color: #2980b9;">
                        <strong>RFID System:</strong> This notification was sent automatically when {'your' if recipient_type == 'student' else 'your child\'s'} RFID card was scanned at the school {'entrance' if action_type == 'check-in' else 'exit'}.
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
        
        print(f"✅ Email sent to {to_email}: {student_name} ({grade}) {action_type} at {timestamp}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

# --- Main loop ---
print("Email Notification System")
print("=" * 40)
print("This will send a test email notification")

# Ask for recipient type (Student or Parents + Student)
print("\nSelect recipient type:")
print("1. Student")
print("2. Parents + Student")
while True:
    recipient_choice = input("Enter your choice (1 or 2): ").strip()
    if recipient_choice == "1":
        recipient_type = "student"
        break
    elif recipient_choice == "2":
        recipient_type = "parents"
        break
    else:
        print("❌ Invalid choice. Please enter 1 or 2.")

# Ask for action type (check-in or check-out)
print(f"\nSelect action type for {recipient_type}:")
print("1. Check-in")
print("2. Check-out")
while True:
    choice = input("Enter your choice (1 or 2): ").strip()
    if choice == "1":
        action_type = "check-in"
        break
    elif choice == "2":
        action_type = "check-out"
        break
    else:
        print("❌ Invalid choice. Please enter 1 or 2.")

# Ask for destination email(s)
if recipient_type == "parents":
    print(f"\nEnter email addresses for {recipient_type} {action_type} notification:")
    parent_email = input("Parent Email: ").strip()
    student_email = input("Student Email: ").strip()
    
    # Validate email formats (basic check)
    if "@" not in parent_email or "." not in parent_email:
        print("❌ Invalid parent email format. Please enter a valid email address.")
        exit()
    if "@" not in student_email or "." not in student_email:
        print("❌ Invalid student email format. Please enter a valid email address.")
        exit()
    
    # Store both emails for sending
    destination_emails = [parent_email, student_email]
else:
    print(f"\nEnter the destination email address for {recipient_type} {action_type} notification:")
    destination_email = input("Email: ").strip()
    
    # Validate email format (basic check)
    if "@" not in destination_email or "." not in destination_email:
        print("❌ Invalid email format. Please enter a valid email address.")
        exit()
    
    # Store single email for sending
    destination_emails = [destination_email]

# Ask for student information
print(f"\nEnter student information for {recipient_type} {action_type}:")
student_name = input("Student Name: ").strip()
student_grade = input("Grade Level: ").strip()

# Get current timestamp in Manila Time (Philippines timezone)
ph_tz = pytz.timezone('Asia/Manila')
timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S " "(Manila Time)")

if recipient_type == "parents":
    print(f"\nSending {recipient_type} {action_type} emails to:")
    print(f"  Parent: {parent_email}")
    print(f"  Student: {student_email}")
else:
    print(f"\nSending {recipient_type} {action_type} email to: {destination_email}")

print(f"Student: {student_name} ({student_grade})")
print(f"Time: {timestamp}")
print("-" * 40)

# Send email notification(s)
if recipient_type == "parents":
    # Send parent email
    parent_success = send_email(
        parent_email, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        "parents"
    )
    
    # Send student email (same as student option)
    student_success = send_email(
        student_email, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        "student"
    )
    
    success = parent_success and student_success
else:
    # Send single email
    success = send_email(
        destination_email, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        recipient_type
    )

if success:
    print(f"📧 Email notification sent successfully!")
else:
    print(f"❌ Failed to send email notification")
