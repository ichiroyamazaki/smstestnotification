import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import requests
import json

print("Starting Combined Email + SMS Test...")

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"
EMAIL_PASSWORD = "sluj vevq hzxd jvze"
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- SMS setup (PhilSMS API) ---
PHILSMS_API_TOKEN = "3204|0BG5TE9eSFQabJsqdliilcgtG90CqcaSZW8sEDel"
PHILSMS_SENDER_NAME = "PhilSMS"
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"

print("Initializing Firebase...")
# --- Firebase setup ---
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://school-attendance-63ead-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")

def send_email_simple(to_email, student_name, grade, timestamp):
    """Send email notification"""
    try:
        print(f"📧 Preparing email to {to_email}...")
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = f"Check-in Student {student_name}"
        
        body = f"""
        <html>
        <body>
            <h2>Student Check-in Notification</h2>
            <p><strong>Student Name:</strong> {student_name}</p>
            <p><strong>Grade Level:</strong> {grade}</p>
            <p><strong>Check-in Time:</strong> {timestamp}</p>
            <p>Powered by AI-niform Technology</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        print("📧 Connecting to Gmail SMTP...")
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        
        print("📧 Sending email...")
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False

def send_sms_simple(to_phone, student_name, grade, timestamp):
    """Send SMS notification"""
    try:
        print(f"📱 Preparing SMS to {to_phone}...")
        
        # Format phone number
        if not to_phone.startswith('+63'):
            if to_phone.startswith('0'):
                to_phone = '+63' + to_phone[1:]
            else:
                to_phone = '+63' + to_phone
        
        message = f"Hi {student_name}! You checked in at {timestamp}. Welcome to STI College Balagtas. Powered by AI-niform Technology"
        
        data = {
            'recipient': to_phone,
            'sender_id': PHILSMS_SENDER_NAME,
            'type': 'plain',
            'message': message
        }
        
        headers = {
            'Authorization': f'Bearer {PHILSMS_API_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        print("📱 Sending SMS...")
        response = requests.post(PHILSMS_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ SMS sent successfully to {to_phone}")
                print(f"Message ID: {result.get('message_id', 'N/A')}")
                return True
            else:
                print(f"❌ SMS failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ SMS HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ SMS error: {str(e)}")
        return False

# Test data
destination_email = "ichiroyamazaki123@gmail.com"
destination_phone = "09123456789"  # Replace with real phone number
student_name = "Ichiro Yamazaki"
student_grade = "Grade 10"

ph_tz = pytz.timezone('Asia/Manila')
timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S GMT+8")

print(f"\nTest Data:")
print(f"Email: {destination_email}")
print(f"Phone: {destination_phone}")
print(f"Student: {student_name} ({student_grade})")
print(f"Time: {timestamp}")
print("-" * 50)

# Send both notifications
print("\n🚀 Sending notifications...")

print("\n1. Sending EMAIL...")
email_success = send_email_simple(destination_email, student_name, student_grade, timestamp)

print("\n2. Sending SMS...")
sms_success = send_sms_simple(destination_phone, student_name, student_grade, timestamp)

# Results
print(f"\n" + "=" * 50)
print("RESULTS:")
print("=" * 50)
print(f"Email: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
print(f"SMS: {'✅ SUCCESS' if sms_success else '❌ FAILED'}")

if email_success and sms_success:
    print("\n🎉 Both notifications sent successfully!")
elif email_success or sms_success:
    print("\n⚠️  Partial success - one notification failed!")
else:
    print("\n❌ Both notifications failed!")

print("\nScript completed!")
