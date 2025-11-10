import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import os
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- SMS setup (PhilSMS API) ---
PHILSMS_API_TOKEN = "3586|19fsJM7JYA9DHC6P9mXRjYzfUDZG67nmlL7df1M0"  # PhilSMS API Token
PHILSMS_SENDER_NAME = "PhilSMS"  # Replace with your approved sender name
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"  # PhilSMS API endpoint


def send_email(to_email, student_name, grade, timestamp, action_type="check-in", recipient_type="student", violation_type=None, violation_details=None, violation_count=None):
    """
    Send email notification using Gmail SMTP (FREE)
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    violation_type: "incomplete_uniform" or "missing_id" or None
    violation_details: string with details about incomplete uniform items (only for incomplete_uniform)
    violation_count: current violation count for the student
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        
        # Set subject based on action type
        if violation_type:
            msg['Subject'] = f"Student Check-in with Violation - {student_name}"
        else:
            msg['Subject'] = f"Student {action_type.title()} - {student_name}"
        
        # Email body
        if action_type == "check-in":
            if violation_type:
                action_text = "Checked In with Violation"
                action_color = "#f39c12"  # Orange for violation
            else:
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
                    <h3 style="color: {action_color}; margin-top: 0;">{'You have successfully' if recipient_type == 'student' else 'Your child has successfully'} {'checked in' if action_type == 'check-in' else 'checked out'}{' with a violation' if violation_type else ''}</h3>
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Grade Level:</strong> {grade}</p>
                    <p><strong>{'Check-in' if action_type == 'check-in' else 'Check-out'} Time:</strong> {timestamp}</p>
                    {f'<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #ffc107;"><p style="margin: 0; color: #856404;"><strong>⚠️ Violation Recorded:</strong></p><p style="margin: 5px 0 0 0; color: #856404;"><strong>Type:</strong> {"Incomplete Uniform" if violation_type == "incomplete_uniform" else "Missing ID"}</p>{"<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Details:</strong> " + violation_details + "</p>" if violation_details else ""}{"<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Total Violation Count:</strong> " + str(violation_count) + "</p>" if violation_count is not None else ""}</div>' if violation_type else ''}
                </div>
                
                {f'<div style="background-color: #dc3545; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #721c24;"><p style="margin: 0; color: #ffffff; font-size: 16px; font-weight: bold;"><strong>🚨 Important Message:</strong></p><p style="margin: 10px 0 0 0; color: #ffffff; font-size: 14px;">{"Your child has reached their 3rd Violation Warning. They need to complete Community Service. Their violation count will be reset after they complete the Community Service." if recipient_type == "parents" else "You have reached your 3rd Violation Warning. You need to complete Community Service. Your violation count will be reset after you complete the Community Service."}</p></div>' if violation_type and violation_count == 3 else ''}
                
                {f'<div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;"><p style="margin: 0; color: #721c24;"><strong>📋 Important Reminder:</strong></p><p style="margin: 5px 0 0 0; color: #721c24;">{"Your child is eligible to appeal their violation to the Guidance Office." if recipient_type == "parents" else "If you wish to appeal your violation, please visit the Guidance Office."}</p></div>' if violation_type and violation_count != 3 else ''}
                
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

def send_sms(to_phone, student_name, grade, timestamp, action_type="check-in", recipient_type="student", violation_type=None, violation_details=None, violation_count=None):
    """
    Send SMS notification using PhilSMS API
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    violation_type: "incomplete_uniform" or "missing_id" or None
    violation_details: string with details about incomplete uniform items (only for incomplete_uniform)
    violation_count: current violation count for the student
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
            if violation_type:
                violation_msg = f"Violation: {'Incomplete Uniform' if violation_type == 'incomplete_uniform' else 'Missing ID'}"
                if violation_details:
                    violation_msg += f" - {violation_details}"
                count_msg = f" Total Violations: {violation_count}" if violation_count is not None else ""
                
                # Special message for 3rd violation
                if violation_count == 3:
                    important_msg = " Important Message: You have reached your 3rd Violation Warning. You need to complete Community Service. Your violation count will be reset after you complete the Community Service."
                    reminder_msg = ""
                else:
                    important_msg = ""
                    reminder_msg = " If you wish to appeal, please visit the Guidance Office."
                
                message = f"Hi {student_name}! You have checked in at {timestamp} with a violation. {violation_msg}.{count_msg}{important_msg}{reminder_msg} Welcome to STI College Balagtas\n\nPowered by AI-niform Technology"
            else:
                message = f"Hi {student_name}! You have successfully checked in at {timestamp}. Welcome to STI College Balagtas\n\nPowered by AI-niform Technology"
        else:  # check-out
            message = f"Hi {student_name}! You have successfully checked out at {timestamp}. Have a great day!\n\nPowered by AI-niform Technology"
    else:  # parents
        if action_type == "check-in":
            if violation_type:
                violation_msg = f"Violation: {'Incomplete Uniform' if violation_type == 'incomplete_uniform' else 'Missing ID'}"
                if violation_details:
                    violation_msg += f" - {violation_details}"
                count_msg = f" Total Violations: {violation_count}" if violation_count is not None else ""
                
                # Special message for 3rd violation
                if violation_count == 3:
                    important_msg = " Important Message: Your child has reached their 3rd Violation Warning. They need to complete Community Service. Their violation count will be reset after they complete the Community Service."
                    reminder_msg = ""
                else:
                    important_msg = ""
                    reminder_msg = " Your child is eligible to appeal their violation to the Guidance Office."
                
                message = f"Dear Parent, {student_name} ({grade}) has checked in at {timestamp} with a violation. {violation_msg}.{count_msg}{important_msg}{reminder_msg} Your child is now at STI College Balagtas.\n\nPowered by AI-niform Technology"
            else:
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

def send_appeal_email(to_email, student_name, grade, timestamp, recipient_type="student"):
    """
    Send appeal notification email
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = f"Appeal Submitted - {student_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: bold;">AI-niform</h1>
                    <p style="color: #e8f4fd; margin: 5px 0 0 0; font-size: 14px;">Smart School Management System</p>
                </div>
                
                <h2 style="color: #2c3e50; text-align: center; margin-top: 0;">Appeal Submission Notification</h2>
                
                <div style="background-color: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <h3 style="color: #155724; margin-top: 0;">Appeal Submitted Successfully</h3>
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Grade Level:</strong> {grade}</p>
                    <p><strong>Submission Time:</strong> {timestamp}</p>
                    <p style="margin-top: 15px;"><strong>Status:</strong> {"Your child has" if recipient_type == "parents" else "You have"} successfully submitted an appeal to the Guidance Office.</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;"><strong>📋 Important Reminder:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #856404;">According to school policy, whether {"your child's" if recipient_type == "parents" else "your"} appeal is valid or not valid, {"your child's" if recipient_type == "parents" else "your"} violation count will remain unchanged and will still be counted.</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                        <strong>AI-niform School Management System</strong><br>
                        This is an automated message from the Appeal System.<br>
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
        
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        server.quit()
        
        print(f"✅ Appeal email sent to {to_email}: {student_name} ({grade})")
        return True
        
    except Exception as e:
        print(f"❌ Error sending appeal email: {str(e)}")
        return False

def send_appeal_sms(to_phone, student_name, grade, timestamp, recipient_type="student"):
    """
    Send appeal notification SMS
    """
    # Format phone number for Philippines
    if not to_phone.startswith('+63'):
        if to_phone.startswith('0'):
            to_phone = '+63' + to_phone[1:]
        elif to_phone.startswith('63'):
            to_phone = '+' + to_phone
        else:
            to_phone = '+63' + to_phone
    
    if recipient_type == "student":
        message = f"Hi {student_name}! Your appeal has been submitted to the Guidance Office at {timestamp}. Important Reminder: According to school policy, whether your appeal is valid or not valid, your violation count will remain unchanged and will still be counted.\n\nPowered by AI-niform Technology"
    else:  # parents
        message = f"Dear Parent, {student_name} ({grade}) has submitted an appeal to the Guidance Office at {timestamp}. Important Reminder: According to school policy, whether the appeal is valid or not valid, your child's violation count will remain unchanged and will still be counted.\n\nPowered by AI-niform Technology"
    
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
    
    try:
        response = requests.post(PHILSMS_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ Appeal SMS sent to {to_phone}: {student_name} ({grade})")
                return True
            else:
                print(f"❌ Appeal SMS failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending appeal SMS: {str(e)}")
        return False

def send_combined_notification(email, phone, student_name, grade, timestamp, action_type="check-in", recipient_type="parents", violation_type=None, violation_details=None, violation_count=None):
    """
    Send both email and SMS notifications simultaneously
    """
    print(f"\n📧 Sending EMAIL notification...")
    email_success = send_email(email, student_name, grade, timestamp, action_type, recipient_type, violation_type, violation_details, violation_count)
    
    print(f"\n📱 Sending SMS notification...")
    sms_success = send_sms(phone, student_name, grade, timestamp, action_type, recipient_type, violation_type, violation_details, violation_count)
    
    return email_success, sms_success

# --- Firebase setup ---
def initialize_firebase():
    """
    Initialize Firebase Admin SDK if not already initialized
    """
    try:
        firebase_admin.get_app()
        return firestore.client()
    except ValueError:
        # Not initialized, so initialize it
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        service_account_path = os.path.join(script_dir, "serviceAccountKey.json")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()

def fetch_students_from_firebase():
    """
    Fetch all students from Firebase 'students' collection
    Returns a list of student documents with their data
    """
    try:
        db = initialize_firebase()
        students_ref = db.collection("students")
        students_docs = students_ref.stream()
        
        students = []
        for doc in students_docs:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id  # Store document ID
            students.append(student_data)
        
        return students
    except Exception as e:
        print(f"[WARNING] Error fetching students from Firebase: {str(e)}")
        return []

def select_student_from_firebase():
    """
    Display students from Firebase and allow user to select one
    Returns selected student data dictionary or None if cancelled
    """
    print("\n📚 Fetching students from Firebase...")
    students = fetch_students_from_firebase()
    
    if not students:
        print("❌ No students found in Firebase database.")
        return None
    
    print(f"\n✅ Found {len(students)} student(s) in database:")
    print("=" * 70)
    
    # Display students in a numbered list (in order: Name, Student ID, Course/Grade, Email, Contact Number)
    for idx, student in enumerate(students, 1):
        name = student.get('Name', student.get('name', 'N/A'))
        student_id = student.get('Student Number', student.get('student_number', student.get('student_id', 'N/A')))
        course = student.get('Course', student.get('course', 'N/A'))
        grade = student.get('grade', student.get('grade_level', course))  # Use course if grade not available
        email = student.get('Gmail', student.get('gmail', student.get('email', student.get('student_email', 'N/A'))))
        contact_number = student.get('Contact Number', student.get('contact_number', student.get('phone', student.get('student_phone', student.get('mobile', 'N/A')))))
        parent_email = student.get('Parent Gmail', student.get('parent_email', student.get('Parent Email', student.get('parent_email_address', 'N/A'))))
        parent_phone = student.get('Parent Number', student.get('parent_phone', student.get('Parent Phone', student.get('parent_contact_number', student.get('parent_mobile', 'N/A')))))
        
        # Display in the specified order
        print(f"{idx}. Name: {name}")
        print(f"   Student ID: {student_id}")
        print(f"   Course / Grade: {course if course != 'N/A' else grade}")
        print(f"   Email: {email}")
        print(f"   Contact Number: {contact_number}")
        if parent_email != 'N/A' or parent_phone != 'N/A':
            print(f"   Parent Email: {parent_email}")
            print(f"   Parent Phone: {parent_phone}")
        print()
    
    print("=" * 70)
    
    # Allow user to select a student
    while True:
        try:
            choice = input(f"Select a student (1-{len(students)}) or '0' to cancel: ").strip()
            
            if choice == '0':
                print("❌ Selection cancelled.")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(students):
                selected_student = students[choice_num - 1]
                print(f"\n✅ Selected: {selected_student.get('name', 'N/A')}")
                return selected_student
            else:
                print(f"❌ Invalid choice. Please enter a number between 1 and {len(students)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def get_violation_count_from_firebase(student_number):
    """
    Get the current violation count for a student from Firebase
    Returns the violation count or 0 if not found
    """
    try:
        if not student_number:
            return 0
        
        db = initialize_firebase()
        student_violations_ref = db.collection("student_violations")
        student_violation_doc = student_violations_ref.document(str(student_number))
        
        existing_data = student_violation_doc.get()
        if existing_data.exists:
            current_data = existing_data.to_dict()
            return current_data.get('violation_count', 0)
        else:
            return 0
    except Exception as e:
        print(f"[WARNING] Error getting violation count: {str(e)}")
        return 0

def save_appeal_to_firebase(student_name, grade, timestamp, student_number, email=None, phone=None):
    """
    Save appeal log to student_violations collection
    Does NOT deduct violation count, only logs the appeal
    """
    try:
        # Check if service account key file exists before initializing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        service_account_path = os.path.join(script_dir, "serviceAccountKey.json")
        
        if not os.path.exists(service_account_path):
            print(f"\n[WARNING] serviceAccountKey.json not found at: {service_account_path}")
            print(f"         Appeal not saved to Firebase.")
            return False
        
        if not student_number:
            print(f"\n[WARNING] Student Number not provided. Appeal not saved to Firebase.")
            return False
        
        db = initialize_firebase()
        
        # Check if student has violations
        student_violations_ref = db.collection("student_violations")
        student_violation_doc = student_violations_ref.document(str(student_number))
        existing_data = student_violation_doc.get()
        
        if not existing_data.exists:
            print(f"\n[ERROR] Student {student_number} does not have any violations in the system.")
            return False
        
        current_data = existing_data.to_dict()
        violation_count = current_data.get('violation_count', 0)
        
        if violation_count == 0:
            print(f"\n[ERROR] Student {student_number} has no violations. Cannot process appeal.")
            return False
        
        # Prepare appeal data
        appeal_data = {
            "student_name": student_name,
            "grade": grade,
            "timestamp": timestamp,
            "appeal_type": "guidance_office",
            "appeal_status": "submitted",
            "recorded_at": datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        }
        
        # Add contact info if provided
        if email:
            appeal_data["student_email"] = email
        if phone:
            appeal_data["student_phone"] = phone
        
        # Save appeal to appeals subcollection (does not affect violation count)
        appeal_id = datetime.now(pytz.timezone('Asia/Manila')).strftime("%Y%m%d_%H%M%S")
        student_violation_doc.collection("appeals").document(appeal_id).set(appeal_data)
        
        print(f"\n[OK] Appeal logged for student {student_number}")
        print(f"     Appeal ID: {appeal_id}")
        print(f"     Current violation count: {violation_count} (unchanged)")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n[WARNING] serviceAccountKey.json not found. Appeal not saved to Firebase.")
        print(f"         Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[WARNING] Error saving appeal to Firebase: {str(e)}")
        return False

def save_violation_to_firebase(student_name, grade, timestamp, violation_type, violation_details=None, email=None, phone=None, violation_count=None, student_number=None):
    """
    Save violation record to student_violations collection using Student Number as document ID
    If student doesn't exist, create a new document with their Student Number
    Stores violations as subcollection under each student's document
    """
    try:
        # Check if service account key file exists before initializing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        service_account_path = os.path.join(script_dir, "serviceAccountKey.json")
        
        if not os.path.exists(service_account_path):
            print(f"\n[WARNING] serviceAccountKey.json not found at: {service_account_path}")
            print(f"         Violation not saved to Firebase.")
            return False
        
        if not student_number:
            print(f"\n[WARNING] Student Number not provided. Violation not saved to Firebase.")
            return False
        
        db = initialize_firebase()
        
        # Prepare violation data
        violation_data = {
            "student_name": student_name,
            "grade": grade,
            "timestamp": timestamp,
            "violation_type": violation_type,
            "violation_type_display": "Incomplete Uniform" if violation_type == "incomplete_uniform" else "Missing ID",
            "action_type": "check-in",  # Violations only occur on check-in
            "recorded_at": datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        }
        
        # Add violation details if provided (for incomplete uniform)
        if violation_details:
            violation_data["violation_details"] = violation_details
        
        # Add contact info if provided
        if email:
            violation_data["student_email"] = email
        if phone:
            violation_data["student_phone"] = phone
        
        # Save to student_violations collection using Student Number as document ID
        student_violations_ref = db.collection("student_violations")
        student_violation_doc = student_violations_ref.document(str(student_number))
        
        # Get existing data or create new
        existing_data = student_violation_doc.get()
        
        if existing_data.exists:
            # Update existing document - increment violation count
            current_data = existing_data.to_dict()
            current_count = current_data.get('violation_count', 0)
            new_count = current_count + 1  # Always increment by 1
            
            # Update student info and violation count
            student_violation_doc.update({
                'violation_count': new_count,
                'last_updated': datetime.now(pytz.timezone('Asia/Manila')).isoformat(),
                'student_name': student_name,
                'grade': grade
            })
            
            # Add violation to violations subcollection
            violation_id = datetime.now(pytz.timezone('Asia/Manila')).strftime("%Y%m%d_%H%M%S")
            student_violation_doc.collection("violations").document(violation_id).set(violation_data)
            
            print(f"\n[OK] Violation saved to student_violations for student {student_number}")
            print(f"     Updated violation count: {new_count} (added 1)")
            print(f"     Violation ID: {violation_id}")
        else:
            # Create new document with Student Number as document ID
            student_violation_doc.set({
                'student_name': student_name,
                'grade': grade,
                'violation_count': 1,  # Start with 1
                'last_updated': datetime.now(pytz.timezone('Asia/Manila')).isoformat(),
                'student_number': str(student_number)
            })
            
            # Add first violation to violations subcollection
            violation_id = datetime.now(pytz.timezone('Asia/Manila')).strftime("%Y%m%d_%H%M%S")
            student_violation_doc.collection("violations").document(violation_id).set(violation_data)
            
            print(f"\n[OK] Created new violation record for student {student_number}")
            print(f"     Violation count: 1")
            print(f"     Violation ID: {violation_id}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n[WARNING] serviceAccountKey.json not found. Violation not saved to Firebase.")
        print(f"         Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[WARNING] Error saving violation to Firebase: {str(e)}")
        return False

# --- Main execution ---
print("Combined Email + SMS Notification System")
print("=" * 50)
print("This will send both email and SMS notifications")

# Ask for recipient type (Student, Parents + Student, or Appeal Student)
print("\nSelect recipient type:")
print("1. Student")
print("2. Parents + Student")
print("3. Appeal Student")
while True:
    recipient_choice = input("Enter your choice (1, 2, or 3): ").strip()
    if recipient_choice == "1":
        recipient_type = "student"
        break
    elif recipient_choice == "2":
        recipient_type = "parents"
        break
    elif recipient_choice == "3":
        recipient_type = "appeal"
        break
    else:
        print("❌ Invalid choice. Please enter 1, 2, or 3.")

# Handle appeal flow separately
if recipient_type == "appeal":
    # Skip action type selection for appeals
    action_type = "appeal"
    violation_type = None
    violation_details = None
    violation_count = None
else:
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

# Initialize violation variables
violation_type = None
violation_details = None
violation_count = None

# Ask about violation only for check-in
if action_type == "check-in":
    print(f"\nRecord student violation?")
    print("1. Yes")
    print("2. No")
    while True:
        violation_choice = input("Enter your choice (1 or 2): ").strip()
        if violation_choice == "1":
            # Automatically set violation type to incomplete_uniform (only option - no ID means no entry)
            violation_type = "incomplete_uniform"
            
            # Ask for specific uniform items that are incomplete
            print(f"\nEnter which uniform items are incomplete (e.g., 'shirt', 'pants', 'shoes', etc.):")
            violation_details = input("Incomplete uniform items: ").strip()
            if not violation_details:
                print("⚠️  No details provided. Continuing without details.")
            
            # Set violation count to 1 (each submission adds 1 violation)
            violation_count = 1
            break
        elif violation_choice == "2":
            # No violation
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

# Select student from Firebase database
print(f"\n📋 Select student from database:")
selected_student = select_student_from_firebase()

if not selected_student:
    print("❌ No student selected. Exiting...")
    exit()

# Extract student information from selected student (using Firebase field names)
student_name = selected_student.get('Name', selected_student.get('name', 'N/A'))
student_grade = selected_student.get('Course', selected_student.get('course', selected_student.get('grade', selected_student.get('grade_level', 'N/A'))))
student_email = selected_student.get('Gmail', selected_student.get('gmail', selected_student.get('email', selected_student.get('student_email', ''))))
student_phone = selected_student.get('Contact Number', selected_student.get('contact_number', selected_student.get('phone', selected_student.get('student_phone', selected_student.get('mobile', '')))))
student_number = selected_student.get('Student Number', selected_student.get('student_number', selected_student.get('student_id', '')))
# Extract parent information with multiple field name variations (prioritizing Firebase field names)
parent_email = selected_student.get('Parent Gmail', selected_student.get('parent_email', selected_student.get('Parent Email', selected_student.get('parent_email_address', ''))))
parent_phone = selected_student.get('Parent Number', selected_student.get('parent_phone', selected_student.get('Parent Phone', selected_student.get('parent_contact_number', selected_student.get('parent_mobile', '')))))

# Handle appeal flow
if recipient_type == "appeal":
    # Check if student has violations
    current_violation_count = get_violation_count_from_firebase(student_number)
    
    if current_violation_count == 0:
        print(f"\n[ERROR] Student {student_number} ({student_name}) does not have any violations.")
        print("        Cannot process appeal. The student must have at least one violation to submit an appeal.")
        exit()
    
    # Get current timestamp
    ph_tz = pytz.timezone('Asia/Manila')
    timestamp = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S Manila Time")
    
    print(f"\n📋 Appeal Information:")
    print(f"  Student: {student_name} ({student_grade})")
    print(f"  Student Number: {student_number}")
    print(f"  Current Violation Count: {current_violation_count}")
    print(f"  Submission Time: {timestamp}")
    print("-" * 50)
    
    # Send appeal notifications
    print(f"\n📧 Sending STUDENT EMAIL notification...")
    student_email_success = send_appeal_email(student_email, student_name, student_grade, timestamp, "student")
    
    print(f"\n📱 Sending STUDENT SMS notification...")
    student_sms_success = send_appeal_sms(student_phone, student_name, student_grade, timestamp, "student")
    
    # Send to parent if available
    parent_email_success = True
    parent_sms_success = True
    
    if parent_email:
        print(f"\n📧 Sending PARENT EMAIL notification...")
        parent_email_success = send_appeal_email(parent_email, student_name, student_grade, timestamp, "parents")
    
    if parent_phone:
        print(f"\n📱 Sending PARENT SMS notification...")
        parent_sms_success = send_appeal_sms(parent_phone, student_name, student_grade, timestamp, "parents")
    
    # Save appeal to Firebase
    print(f"\n💾 Saving appeal to Firebase database...")
    appeal_saved = save_appeal_to_firebase(
        student_name=student_name,
        grade=student_grade,
        timestamp=timestamp,
        student_number=student_number,
        email=student_email,
        phone=student_phone
    )
    
    # Summary
    print(f"\n" + "=" * 50)
    print("APPEAL SUBMISSION SUMMARY")
    print("=" * 50)
    if student_email_success:
        print("✅ Student email notification sent successfully!")
    else:
        print("❌ Student email notification failed!")
    
    if student_sms_success:
        print("✅ Student SMS notification sent successfully!")
    else:
        print("❌ Student SMS notification failed!")
    
    if parent_email and parent_email_success:
        print("✅ Parent email notification sent successfully!")
    elif parent_email:
        print("❌ Parent email notification failed!")
    
    if parent_phone and parent_sms_success:
        print("✅ Parent SMS notification sent successfully!")
    elif parent_phone:
        print("❌ Parent SMS notification failed!")
    
    if appeal_saved:
        print("✅ Appeal logged to Firebase successfully!")
    else:
        print("❌ Failed to log appeal to Firebase!")
    
    if student_email_success and student_sms_success and appeal_saved:
        print("\n🎉 Appeal submitted successfully!")
    else:
        print("\n⚠️  Appeal submitted with some issues. Please check the logs above.")
    
    exit()

# Validate that we have the necessary information
if not student_email:
    print("⚠️  Warning: Student email not found in database.")
if not student_phone:
    print("⚠️  Warning: Student phone not found in database.")

# Display parent information when Parents + Student is selected
if recipient_type == "parents":
    print(f"\n📋 Parent Information from Database:")
    print(f"  📧 Parent Email: {parent_email if parent_email else '❌ Not found in database'}")
    print(f"  📱 Parent Phone: {parent_phone if parent_phone else '❌ Not found in database'}")
    
    if not parent_email:
        print("⚠️  Warning: Parent email not found in database. Parent email notification will be skipped.")
    if not parent_phone:
        print("⚠️  Warning: Parent phone not found in database. Parent SMS notification will be skipped.")

# Set up destination emails and phones based on recipient type
if recipient_type == "parents":
    destination_emails = [parent_email, student_email] if parent_email else [student_email]
    destination_phones = [parent_phone, student_phone] if parent_phone else [student_phone]
    destination_email = student_email  # For single email reference
    destination_phone = student_phone  # For single phone reference
else:
    destination_email = student_email
    destination_phone = student_phone
    destination_emails = [student_email]
    destination_phones = [student_phone]

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
if violation_type:
    print(f"Violation: {'Incomplete Uniform' if violation_type == 'incomplete_uniform' else 'Missing ID'}")
    if violation_details:
        print(f"Violation Details: {violation_details}")
print("-" * 50)

# Get violation count from Firebase if violation exists (before saving, so we get current count)
current_violation_count = None
if violation_type and student_number:
    current_violation_count = get_violation_count_from_firebase(student_number)
    # The count will be incremented after saving, so we show the count that will be after this violation
    current_violation_count = current_violation_count + 1 if current_violation_count is not None else 1

# Send combined notifications
if recipient_type == "parents":
    # Send notifications to both parents and student (for all violation types including incomplete uniform)
    print(f"\n📧 Sending PARENT EMAIL notification...")
    parent_email_success = send_email(parent_email, student_name, student_grade, timestamp, action_type, "parents", violation_type, violation_details, current_violation_count)
    
    print(f"\n📧 Sending STUDENT EMAIL notification...")
    student_email_success = send_email(student_email, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, current_violation_count)
    
    print(f"\n📱 Sending PARENT SMS notification...")
    parent_sms_success = send_sms(parent_phone, student_name, student_grade, timestamp, action_type, "parents", violation_type, violation_details, current_violation_count)
    
    print(f"\n📱 Sending STUDENT SMS notification...")
    student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, current_violation_count)
    
    email_success = parent_email_success and student_email_success
    sms_success = parent_sms_success and student_sms_success
else:
    # Send single notifications (student only)
    print(f"\n📧 Sending EMAIL notification...")
    email_success = send_email(destination_email, student_name, student_grade, timestamp, action_type, recipient_type, violation_type, violation_details, current_violation_count)
    
    print(f"\n📱 Sending SMS notification...")
    sms_success = send_sms(destination_phone, student_name, student_grade, timestamp, action_type, recipient_type, violation_type, violation_details, current_violation_count)

# Save violation to Firebase if violation exists
if violation_type:
    print(f"\n💾 Saving violation to Firebase database...")
    # Determine which email and phone to save (student contact info)
    if recipient_type == "parents":
        save_email = student_email
        save_phone = student_phone
    else:
        save_email = destination_email
        save_phone = destination_phone
    
    # Validate student number exists
    if not student_number:
        print("⚠️  Warning: Student Number not found. Violation count will not be saved to student_violations.")
    
    save_violation_to_firebase(
        student_name=student_name,
        grade=student_grade,
        timestamp=timestamp,
        violation_type=violation_type,
        violation_details=violation_details,
        email=save_email,
        phone=save_phone,
        violation_count=violation_count,
        student_number=student_number
    )

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
