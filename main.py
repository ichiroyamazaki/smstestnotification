import requests
import json

# --- PhilSMS setup ---
PHILSMS_API_TOKEN = "3204|0BG5TE9eSFQabJsqdliilcgtG90CqcaSZW8sEDel"  # PhilSMS API Token
PHILSMS_SENDER_NAME = "PhilSMS"  # Replace with your approved sender name
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"  # PhilSMS API endpoint

def send_sms(to, message):
    """
    Send SMS using PhilSMS API
    """
    # Format phone number for Philippines (add +63 if needed)
    if not to.startswith('+63'):
        if to.startswith('0'):
            to = '+63' + to[1:]  # Remove leading 0 and add +63
        elif to.startswith('63'):
            to = '+' + to  # Add + if missing
        else:
            to = '+63' + to  # Add +63 prefix
    
    # Prepare data for PhilSMS API
    data = {
        'recipient': to,
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
                print(f"✅ SMS sent to {to}: {message}")
                print(f"Message ID: {result.get('message_id', 'N/A')}")
                print(f"Cost: {result.get('cost', 'N/A')}")
            else:
                print(f"❌ SMS failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending SMS: {str(e)}")

# --- Main loop ---
print("SMS Test System")
print("=" * 40)
print("This will send a test SMS notification")

# Ask for phone number
print("\nEnter the destination phone number:")
phone = input("Phone: ").strip()

# Ask for test message
print("\nEnter the test message:")
message = input("Message: ").strip()

print(f"\nSending SMS to: {phone}")
print(f"Message: {message}")
print("-" * 40)

# Send SMS
send_sms(phone, message)
