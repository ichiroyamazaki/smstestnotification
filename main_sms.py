import requests
import json
from datetime import datetime
import pytz

# --- PhilSMS setup ---
PHILSMS_API_TOKEN = "3204|0BG5TE9eSFQabJsqdliilcgtG90CqcaSZW8sEDel"  # PhilSMS API Token
PHILSMS_SENDER_NAME = "PhilSMS"  # Replace with your approved sender name
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"  # PhilSMS API endpoint

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

# --- Main loop ---
print("SMS Notification System")
print("=" * 40)
print("This will send a test SMS notification")

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
    print(f"\nSending {recipient_type} {action_type} SMS to:")
    print(f"  Parent: {parent_phone}")
    print(f"  Student: {student_phone}")
else:
    print(f"\nSending {recipient_type} {action_type} SMS to: {destination_phone}")

print(f"Student: {student_name} ({student_grade})")
print(f"Time: {timestamp}")
print("-" * 40)

# Send SMS notification(s)
if recipient_type == "parents":
    # Send parent SMS
    parent_success = send_sms(
        parent_phone, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        "parents"
    )
    
    # Send student SMS (same as student option)
    student_success = send_sms(
        student_phone, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        "student"
    )
    
    success = parent_success and student_success
else:
    # Send single SMS
    success = send_sms(
        destination_phone, 
        student_name, 
        student_grade, 
        timestamp,
        action_type,
        recipient_type
    )

if success:
    print(f"📱 SMS notification sent successfully!")
else:
    print(f"❌ Failed to send SMS notification")
