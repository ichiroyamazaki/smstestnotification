import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import os
import requests
import json

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- SMS setup (PhilSMS API) ---
PHILSMS_API_TOKEN = "3204|0BG5TE9eSFQabJsqdliilcgtG90CqcaSZW8sEDel"  # PhilSMS API Token
PHILSMS_SENDER_NAME = "PhilSMS"  # Replace with your approved sender name
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"  # PhilSMS API endpoint


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
        
        # Set subject based on action type
        msg['Subject'] = f"Student {action_type.title()} - {student_name}"
        
        # Email body
        if action_type == "check-in":
            action_text = "Successfully Checked In"
            action_color = "#27ae60"
        else:
            action_text = "Successfully Checked Out"
            action_color = "#e74c3c"
        
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
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {action_color};">
                    <h3 style="color: {action_color}; margin-top: 0;">{'You have successfully' if recipient_type == 'student' else 'Your child has successfully'} {'checked in' if action_type == 'check-in' else 'checked out'}</h3>
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

def send_sms(to_phone, student_name, grade, timestamp, action_type="check-in", recipient_type="student"):
    """
    Send SMS notification using PhilSMS API
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    """
    # Format phone number for Philippines (add +63 if needed)
    if not to_phone.startswith('+63'):
        if to_phone.startswith('0'):
            to_phone = '+63' + to_phone[1:]  # Remove leading 0 and add +63
        elif to_phone.startswith('63'):
            to_phone = '+' + to_phone  # Add + if missing
        else:
            to_phone = '+63' + to_phone  # Add +63 prefix
    
    # Create message based on recipient type and action
    if recipient_type == "student":
        if action_type == "check-in":
            message = f"Hi {student_name}! You have successfully checked in at {timestamp}. Welcome to STI College Balagtas\n\nPowered by AI-niform Technology"
        else:  # check-out
            message = f"Hi {student_name}! You have successfully checked out at {timestamp}. Have a great day!\n\nPowered by AI-niform Technology"
    else:  # parents
        if action_type == "check-in":
            message = f"Dear Parent, {student_name} ({grade}) has successfully checked in at {timestamp}. Your child is now at STI College Balagtas.\n\nPowered by AI-niform Technology"
        else:  # check-out
            message = f"Dear Parent, {student_name} ({grade}) has successfully checked out at {timestamp}. Your child has left STI College Balagtas.\n\nPowered by AI-niform Technology"
    
    # Prepare data for PhilSMS API
    data = {
        'recipient': to_phone,
        'sender_id': PHILSMS_SENDER_NAME,
        'type': 'plain',
        'message': message
    }
    
    # Authorization headers
    headers = {
        'Authorization': f'Bearer {PHILSMS_API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        # Send SMS via PhilSMS API
        response = requests.post(PHILSMS_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ SMS sent to {to_phone}: {student_name} ({grade}) {action_type} at {timestamp}")
                print(f"Message ID: {result.get('message_id', 'N/A')}")
                print(f"Cost: {result.get('cost', 'N/A')}")
                return True
            else:
                print(f"❌ SMS failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending SMS: {str(e)}")
        return False

def send_combined_notification(email, phone, student_name, grade, timestamp, action_type="check-in", recipient_type="parents"):
    """
    Send both email and SMS notifications simultaneously
    """
    print(f"\n📧 Sending EMAIL notification...")
    email_success = send_email(email, student_name, grade, timestamp, action_type)
    
    print(f"\n📱 Sending SMS notification...")
    sms_success = send_sms(phone, student_name, grade, timestamp, action_type, recipient_type)
    
    return email_success, sms_success

# --- Main execution ---
print("Combined Email + SMS Notification System")
print("=" * 50)
print("This will send both email and SMS notifications")

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

# Ask for destination phone number(s)
if recipient_type == "parents":
    print(f"\nEnter phone numbers for {recipient_type} {action_type} notification:")
    parent_phone = input("Parent Phone: ").strip()
    student_phone = input("Student Phone: ").strip()
    
    # Validate phone numbers (basic check)
    if len(parent_phone) < 10:
        print("❌ Invalid parent phone number. Please enter a valid phone number.")
        exit()
    if len(student_phone) < 10:
        print("❌ Invalid student phone number. Please enter a valid phone number.")
        exit()
    
    # Store both phones for sending
    destination_phones = [parent_phone, student_phone]
else:
    print(f"\nEnter the destination phone number for {recipient_type} {action_type} notification:")
    destination_phone = input("Phone: ").strip()
    
    # Validate phone number (basic check)
    if len(destination_phone) < 10:
        print("❌ Invalid phone number. Please enter a valid phone number.")
        exit()
    
    # Store single phone for sending
    destination_phones = [destination_phone]

# Ask for student information
print(f"\nEnter student information for {recipient_type} {action_type}:")
student_name = input("Student Name: ").strip()
student_grade = input("Grade Level: ").strip()

# Get current timestamp in Manila Time (Philippines timezone)
ph_tz = pytz.timezone('Asia/Manila')
timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S Manila Time")

if recipient_type == "parents":
    print(f"\nSending {recipient_type} {action_type} notifications to:")
    print(f"  📧 Parent Email: {parent_email}")
    print(f"  📧 Student Email: {student_email}")
    print(f"  📱 Parent Phone: {parent_phone}")
    print(f"  📱 Student Phone: {student_phone}")
else:
    print(f"\nSending {recipient_type} {action_type} notifications to:")
    print(f"  📧 Email: {destination_email}")
    print(f"  📱 Phone: {destination_phone}")

print(f"Student: {student_name} ({student_grade})")
print(f"Time: {timestamp}")
print("-" * 50)

# Send combined notifications
if recipient_type == "parents":
    # Send parent notifications
    print(f"\n📧 Sending PARENT EMAIL notification...")
    parent_email_success = send_email(parent_email, student_name, student_grade, timestamp, action_type, "parents")
    
    print(f"\n📧 Sending STUDENT EMAIL notification...")
    student_email_success = send_email(student_email, student_name, student_grade, timestamp, action_type, "student")
    
    print(f"\n📱 Sending PARENT SMS notification...")
    parent_sms_success = send_sms(parent_phone, student_name, student_grade, timestamp, action_type, "parents")
    
    print(f"\n📱 Sending STUDENT SMS notification...")
    student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, action_type, "student")
    
    email_success = parent_email_success and student_email_success
    sms_success = parent_sms_success and student_sms_success
else:
    # Send single notifications
    print(f"\n📧 Sending EMAIL notification...")
    email_success = send_email(destination_email, student_name, student_grade, timestamp, action_type, recipient_type)
    
    print(f"\n📱 Sending SMS notification...")
    sms_success = send_sms(destination_phone, student_name, student_grade, timestamp, action_type, recipient_type)

# Summary
print(f"\n" + "=" * 50)
print("NOTIFICATION SUMMARY")
print("=" * 50)
if email_success:
    print("✅ Email notification sent successfully!")
else:
    print("❌ Email notification failed!")

if sms_success:
    print("✅ SMS notification sent successfully!")
else:
    print("❌ SMS notification failed!")

if email_success and sms_success:
    print("\n🎉 All notifications sent successfully!")
elif email_success or sms_success:
    print("\n⚠️  Partial success - some notifications failed!")
else:
    print("\n❌ All notifications failed!")
