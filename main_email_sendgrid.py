import firebase_admin
from firebase_admin import credentials, db
import requests
from datetime import datetime
import json

# --- SendGrid Email setup (FREE TIER: 100 emails/day) ---
SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY_HERE"  # Replace with your SendGrid API key
SENDGRID_SENDER_EMAIL = "your_email@example.com"  # Replace with your verified sender email
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

# --- Firebase setup ---
cred = credentials.Certificate("serviceAccountKey.json")  # JSON file in your project folder
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://school-attendance-63ead-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

def send_email(to_email, student_name, grade, timestamp):
    """
    Send email notification using SendGrid API (FREE: 100 emails/day)
    """
    try:
        # Prepare email data for SendGrid API
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": f"School Attendance Alert - {student_name}"
                }
            ],
            "from": {
                "email": SENDGRID_SENDER_EMAIL,
                "name": "School RFID System"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                            <h2 style="color: #2c3e50; text-align: center;">🏫 School Attendance Notification</h2>
                            
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #27ae60; margin-top: 0;">✅ Student Checked In</h3>
                                <p><strong>Student Name:</strong> {student_name}</p>
                                <p><strong>Grade Level:</strong> {grade}</p>
                                <p><strong>Check-in Time:</strong> {timestamp}</p>
                            </div>
                            
                            <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <p style="margin: 0; color: #2980b9;">
                                    <strong>📱 RFID System:</strong> This notification was sent automatically when your child's RFID card was scanned at the school entrance.
                                </p>
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                                <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                    This is an automated message from the School RFID Attendance System.<br>
                                    Please do not reply to this email.
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                }
            ]
        }
        
        # Send email via SendGrid API
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(SENDGRID_URL, headers=headers, data=json.dumps(email_data))
        
        if response.status_code == 202:
            print(f"✅ Email sent to {to_email}: {student_name} ({grade}) checked in at {timestamp}")
            return True
        else:
            print(f"❌ SendGrid Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

# --- Main loop ---
print("Place your RFID card on the reader...")
print("Email notifications will be sent to parent contacts via SendGrid.")

while True:
    uid = input("Scan card: ").strip()  # USB RFID reader types UID like a keyboard

    student = db.reference("/students/" + uid).get()
    if student:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send email notification
        success = send_email(
            student["parent_contact"], 
            student['name'], 
            student['grade'], 
            timestamp
        )
        
        if success:
            print(f"📧 Email notification sent successfully!")
        else:
            print(f"❌ Failed to send email notification")
    else:
        print("No student found for UID:", uid)



