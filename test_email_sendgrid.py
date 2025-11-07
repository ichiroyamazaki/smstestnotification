import requests
import json
from datetime import datetime

# --- SendGrid Email setup (FREE TIER: 100 emails/day) ---
SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY_HERE"  # Replace with your SendGrid API key
SENDGRID_SENDER_EMAIL = "your_email@example.com"  # Replace with your verified sender email
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

def send_test_email():
    """
    Send a test email using SendGrid API
    """
    # Test email (replace with your own email)
    test_email = "test@example.com"  # Replace with your test email
    test_student_name = "John Doe"
    test_grade = "Grade 10"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Prepare email data for SendGrid API
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": test_email}],
                    "subject": f"Test Email - School Attendance Alert - {test_student_name}"
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
                                <p><strong>Student Name:</strong> {test_student_name}</p>
                                <p><strong>Grade Level:</strong> {test_grade}</p>
                                <p><strong>Check-in Time:</strong> {timestamp}</p>
                            </div>
                            
                            <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <p style="margin: 0; color: #2980b9;">
                                    <strong>📱 RFID System:</strong> This is a TEST notification from your RFID attendance system using SendGrid.
                                </p>
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                                <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                    This is a test message from the School RFID Attendance System.<br>
                                    If you received this email, SendGrid integration is working correctly! 🎉
                                </p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                }
            ]
        }
        
        print("Sending test email via SendGrid API...")
        print(f"From: {SENDGRID_SENDER_EMAIL}")
        print(f"To: {test_email}")
        print(f"Subject: Test Email - School Attendance Alert")
        print("-" * 50)
        
        # Send email via SendGrid API
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(SENDGRID_URL, headers=headers, data=json.dumps(email_data))
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 202:
            print("✅ Test email sent successfully!")
            print("Check your inbox (and spam folder) for the test email.")
            return True
        else:
            print(f"❌ SendGrid Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        return False

def setup_instructions():
    """
    Display setup instructions for SendGrid
    """
    print("SendGrid Setup Instructions")
    print("=" * 50)
    print("1. Sign up for free at sendgrid.com")
    print("2. Verify your sender email address")
    print("3. Generate an API key in Settings > API Keys")
    print("4. Replace SENDGRID_API_KEY with your actual API key")
    print("5. Replace SENDGRID_SENDER_EMAIL with your verified email")
    print("6. Free tier includes 100 emails per day")
    print("=" * 50)
    print()

if __name__ == "__main__":
    print("SendGrid Email Test Script for RFID Attendance System")
    print("=" * 60)
    print("This script tests email notifications using SendGrid API (FREE: 100 emails/day)")
    print()
    
    # Check if credentials are still placeholders
    if (SENDGRID_API_KEY == "YOUR_SENDGRID_API_KEY_HERE" or 
        SENDGRID_SENDER_EMAIL == "your_email@example.com"):
        print("❌ Please update your SendGrid credentials first!")
        print()
        setup_instructions()
    else:
        send_test_email()



