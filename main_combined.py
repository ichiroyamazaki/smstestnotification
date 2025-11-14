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
from google.cloud.firestore_v1 import FieldFilter
import time
import signal
import sys
import threading
from datetime import timedelta

# --- Email setup (Gmail SMTP - FREE) ---
EMAIL_SENDER = "ainiform.notification@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "sluj vevq hzxd jvze"   # Replace with your Gmail App Password
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- SMS setup (PhilSMS API) ---
PHILSMS_API_TOKEN = "3586|19fsJM7JYA9DHC6P9mXRjYzfUDZG67nmlL7df1M0"  # PhilSMS API Token
PHILSMS_SENDER_NAME = "PhilSMS"  # Replace with your approved sender name
PHILSMS_URL = "https://app.philsms.com/api/v3/sms/send"  # PhilSMS API endpoint

# --- Polling Configuration (to reduce Firebase reads) ---
# Adjust this value to control how often the system checks for new violations
# Higher values = fewer Firebase reads but slower notification delivery
# Recommended: 30-60 seconds for free tier Firebase
POLLING_INTERVAL_SECONDS = 10  # Change this to adjust fetch rate (default: 10 seconds)


def send_email(to_email, student_name, grade, timestamp, action_type="check-in", recipient_type="student", violation_type=None, violation_details=None, violation_count=None, recent_activities=None, missing_items=None):
    """
    Send email notification using Gmail SMTP (FREE)
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    violation_type: "incomplete_uniform" or "missing_id" or None
    violation_details: string with details about incomplete uniform items (only for incomplete_uniform)
    violation_count: current violation count for the student
    recent_activities: list of recent activity dictionaries to display
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
        
        # Format violation details with missing items
        violation_html = ""
        if violation_type:
            violation_type_display = "Incomplete Uniform" if violation_type == "incomplete_uniform" else "Missing ID"
            details_html = ""
            
            if violation_type == "incomplete_uniform":
                # Show "Uniform Incomplete" as the main details text
                details_html = "<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Details:</strong> Uniform Incomplete</p>"
                
                # Add missing items list if available
                if missing_items:
                    if isinstance(missing_items, list) and len(missing_items) > 0:
                        items_list = ""
                        for idx, item in enumerate(missing_items, 1):
                            items_list += f"<p style=\"margin: 2px 0 0 20px; color: #856404;\">{idx}. {item}</p>"
                        details_html += items_list
                    elif isinstance(missing_items, str) and missing_items.strip():
                        # If it's a string, try to split by comma or newline
                        items = [item.strip() for item in missing_items.replace('\n', ',').split(',') if item.strip()]
                        if items:
                            items_list = ""
                            for idx, item in enumerate(items, 1):
                                items_list += f"<p style=\"margin: 2px 0 0 20px; color: #856404;\">{idx}. {item}</p>"
                            details_html += items_list
            else:
                # For missing_id, use violation_details if available
                if violation_details:
                    details_html = f"<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Details:</strong> {violation_details}</p>"
            
            violation_count_html = f"<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Total Violation Count:</strong> {violation_count}</p>" if violation_count is not None else ""
            
            violation_html = f'<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #ffc107;"><p style="margin: 0; color: #856404;"><strong>⚠️ Violation Recorded:</strong></p><p style="margin: 5px 0 0 0; color: #856404;"><strong>Type:</strong> {violation_type_display}</p>{details_html}{violation_count_html}</div>'
        
        # Build recent activities section
        activities_html = ""
        if recent_activities and len(recent_activities) > 0:
            activities_list = ""
            for idx, activity in enumerate(recent_activities[:3], 1):
                activity_type = activity.get('action_type', activity.get('type', 'Activity'))
                activity_time = activity.get('timestamp', activity.get('recorded_at', activity.get('time', 'N/A')))
                # Get additional details if available
                activity_details = activity.get('details', activity.get('description', ''))
                # Convert action_type to Time In/Time Out
                activity_type_lower = activity_type.lower() if activity_type else ''
                if activity_type_lower in ['check-in', 'check_in', 'checkin', 'time_in', 'time-in', 'timein']:
                    display_type = "Time In"
                elif activity_type_lower in ['check-out', 'check_out', 'checkout', 'time_out', 'time-out', 'timeout']:
                    display_type = "Time Out"
                else:
                    display_type = activity_type.title()
                activity_info = f"<p style=\"margin: 0; color: #333;\"><strong>{display_type}:</strong> {activity_time}</p>"
                if activity_details:
                    activity_info += f"<p style=\"margin: 5px 0 0 0; color: #666; font-size: 12px;\">{activity_details}</p>"
                activities_list += f'<div style="background-color: #ffffff; padding: 12px; margin: 8px 0; border-radius: 5px; border-left: 3px solid #4a90e2;">{activity_info}</div>'
            activities_html = f'<div style="background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4a90e2;"><h3 style="color: #2c3e50; margin-top: 0;">📋 Recent Activities (Latest 3)</h3>{activities_list}</div>'
        
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
                    {violation_html}
                </div>
                
                {f'<div style="background-color: #dc3545; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #721c24;"><p style="margin: 0; color: #ffffff; font-size: 16px; font-weight: bold;"><strong>🚨 Important Message:</strong></p><p style="margin: 10px 0 0 0; color: #ffffff; font-size: 14px;">{"Your child has reached their 3rd Violation Warning. They need to complete Community Service. Their violation count will be reset after they complete the Community Service." if recipient_type == "parents" else "You have reached your 3rd Violation Warning. You need to complete Community Service. Your violation count will be reset after you complete the Community Service."}</p></div>' if violation_type and violation_count == 3 else ''}
                
                {f'<div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc3545;"><p style="margin: 0; color: #721c24;"><strong>📋 Important Reminder:</strong></p><p style="margin: 5px 0 0 0; color: #721c24;">{"Your child is eligible to appeal their violation to the Guidance Office." if recipient_type == "parents" else "If you wish to appeal your violation, please visit the Guidance Office."}</p></div>' if violation_type and violation_count != 3 else ''}
                
                {activities_html}
                
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

def send_sms(to_phone, student_name, grade, timestamp, action_type="check-in", recipient_type="student", violation_type=None, violation_details=None, violation_count=None, recent_activities=None, missing_items=None):
    """
    Send SMS notification using PhilSMS API
    action_type: "check-in" or "check-out"
    recipient_type: "student" or "parents"
    violation_type: "incomplete_uniform" or "missing_id" or None
    violation_details: string with details about incomplete uniform items (only for incomplete_uniform)
    violation_count: current violation count for the student
    recent_activities: list of recent activity dictionaries to display
    """
    # Format phone number for Philippines (add +63 if needed)
    if not to_phone.startswith('+63'):
        if to_phone.startswith('0'):
            to_phone = '+63' + to_phone[1:]  # Remove leading 0 and add +63
        elif to_phone.startswith('63'):
            to_phone = '+' + to_phone  # Add + if missing
        else:
            to_phone = '+63' + to_phone  # Add +63 prefix
    
    # Build recent activities text for SMS
    activities_text = ""
    if recent_activities and len(recent_activities) > 0:
        activities_list = []
        for idx, activity in enumerate(recent_activities[:3], 1):
            activity_type = activity.get('action_type', activity.get('type', 'Activity'))
            activity_time = activity.get('timestamp', activity.get('recorded_at', activity.get('time', 'N/A')))
            activity_details = activity.get('details', activity.get('description', ''))
            # Convert action_type to Time In/Time Out
            activity_type_lower = activity_type.lower() if activity_type else ''
            if activity_type_lower in ['check-in', 'check_in', 'checkin', 'time_in', 'time-in', 'timein']:
                display_type = "Time In"
            elif activity_type_lower in ['check-out', 'check_out', 'checkout', 'time_out', 'time-out', 'timeout']:
                display_type = "Time Out"
            else:
                display_type = activity_type.title()
            activity_line = f"{idx}. {display_type}: {activity_time}"
            if activity_details:
                activity_line += f" - {activity_details}"
            activities_list.append(activity_line)
        activities_text = f"\n\nRecent Activities:\n" + "\n".join(activities_list)
    
    # Create message based on recipient type and action
    if recipient_type == "student":
        if action_type == "check-in":
            if violation_type:
                violation_msg = f"Violation: {'Incomplete Uniform' if violation_type == 'incomplete_uniform' else 'Missing ID'}"
                
                # Format missing items for incomplete_uniform
                if violation_type == 'incomplete_uniform':
                    violation_msg += " - Uniform Incomplete"
                    if missing_items:
                        if isinstance(missing_items, list) and len(missing_items) > 0:
                            items_text = " ".join([f"{idx}. {item}" for idx, item in enumerate(missing_items, 1)])
                            violation_msg += f" ({items_text})"
                        elif isinstance(missing_items, str) and missing_items.strip():
                            items = [item.strip() for item in missing_items.replace('\n', ',').split(',') if item.strip()]
                            if items:
                                items_text = " ".join([f"{idx}. {item}" for idx, item in enumerate(items, 1)])
                                violation_msg += f" ({items_text})"
                elif violation_details:
                    violation_msg += f" - {violation_details}"
                count_msg = f" Total Violations: {violation_count}" if violation_count is not None else ""
                
                # Special message for 3rd violation
                if violation_count == 3:
                    important_msg = " Important Message: You have reached your 3rd Violation Warning. You need to complete Community Service. Your violation count will be reset after you complete the Community Service."
                    reminder_msg = ""
                else:
                    important_msg = ""
                    reminder_msg = " If you wish to appeal, please visit the Guidance Office."
                
                message = f"Hi {student_name}! You have checked in at {timestamp} with a violation. {violation_msg}.{count_msg}{important_msg}{reminder_msg}{activities_text} Welcome to STI College Balagtas\n\nPowered by AI-niform Technology"
            else:
                message = f"Hi {student_name}! You have successfully checked in at {timestamp}.{activities_text} Welcome to STI College Balagtas\n\nPowered by AI-niform Technology"
        else:  # check-out
            message = f"Hi {student_name}! You have successfully checked out at {timestamp}.{activities_text} Have a great day!\n\nPowered by AI-niform Technology"
    else:  # parents
        if action_type == "check-in":
            if violation_type:
                violation_msg = f"Violation: {'Incomplete Uniform' if violation_type == 'incomplete_uniform' else 'Missing ID'}"
                
                # Format missing items for incomplete_uniform
                if violation_type == 'incomplete_uniform':
                    violation_msg += " - Uniform Incomplete"
                    if missing_items:
                        if isinstance(missing_items, list) and len(missing_items) > 0:
                            items_text = " ".join([f"{idx}. {item}" for idx, item in enumerate(missing_items, 1)])
                            violation_msg += f" ({items_text})"
                        elif isinstance(missing_items, str) and missing_items.strip():
                            items = [item.strip() for item in missing_items.replace('\n', ',').split(',') if item.strip()]
                            if items:
                                items_text = " ".join([f"{idx}. {item}" for idx, item in enumerate(items, 1)])
                                violation_msg += f" ({items_text})"
                elif violation_details:
                    violation_msg += f" - {violation_details}"
                count_msg = f" Total Violations: {violation_count}" if violation_count is not None else ""
                
                # Special message for 3rd violation
                if violation_count == 3:
                    important_msg = " Important Message: Your child has reached their 3rd Violation Warning. They need to complete Community Service. Their violation count will be reset after they complete the Community Service."
                    reminder_msg = ""
                else:
                    important_msg = ""
                    reminder_msg = " Your child is eligible to appeal their violation to the Guidance Office."
                
                message = f"Dear Parent, {student_name} ({grade}) has checked in at {timestamp} with a violation. {violation_msg}.{count_msg}{important_msg}{reminder_msg}{activities_text} Your child is now at STI College Balagtas.\n\nPowered by AI-niform Technology"
            else:
                message = f"Dear Parent, {student_name} ({grade}) has successfully checked in at {timestamp}.{activities_text} Your child is now at STI College Balagtas.\n\nPowered by AI-niform Technology"
        else:  # check-out
            message = f"Dear Parent, {student_name} ({grade}) has successfully checked out at {timestamp}.{activities_text} Your child has left STI College Balagtas.\n\nPowered by AI-niform Technology"
    
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

def send_appeal_result_email(to_email, student_name, grade, timestamp, reason_type, recipient_type="student", violation_count=None, display_reason_type=None):
    """
    Send appeal result notification email
    reason_type: "Excused" (approved) or "Unexcused" (not approved) - from violation_history document
    display_reason_type: The violation type to display (e.g., "incomplete_uniform") - from last_violation_type in parent document
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        
        # Check if appeal was approved: "Excused" means approved (case-insensitive)
        # Use reason_type from violation_history document for approval logic
        is_excused = reason_type and reason_type.lower() == "excused"
        status_text = "Approved" if is_excused else "Not Approved"
        # Use green for approved, yellow for not approved (instead of red)
        status_color = "#28a745" if is_excused else "#856404"  # Green for approved, dark yellow/brown text for not approved
        bg_color = "#d4edda" if is_excused else "#fff3cd"  # Green background for approved, yellow background for not approved
        border_color = "#28a745" if is_excused else "#ffc107"  # Green border for approved, yellow border for not approved
        
        # Format display_reason_type for display (convert violation types to readable format)
        # Use display_reason_type if provided, otherwise fall back to reason_type
        def format_reason_type(reason):
            if not reason:
                return ""
            reason_lower = reason.lower()
            if reason_lower == "incomplete_uniform":
                return "Incomplete Uniform"
            elif reason_lower == "missing_id":
                return "Missing ID"
            else:
                # Return as-is for other values like "Excused", "Unexcused", etc.
                return reason
        
        # Use display_reason_type for the "Reason Type" field display
        reason_to_display = display_reason_type if display_reason_type else reason_type
        formatted_reason_type = format_reason_type(reason_to_display)
        
        # Build reason_type line separately to avoid nested f-string issues
        reason_type_line = f'<p style="margin-top: 10px;"><strong>Reason Type:</strong> {formatted_reason_type}</p>' if formatted_reason_type else ""
        
        msg['Subject'] = f"Your Appeal Has Been Decided"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #ffffff;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: bold;">AI-niform</h1>
                    <p style="color: #e8f4fd; margin: 5px 0 0 0; font-size: 14px;">Smart School Management System</p>
                </div>
                
                <h2 style="color: #2c3e50; text-align: center; margin-top: 0;">Appeal Result Notification</h2>
                
                <div style="background-color: {bg_color}; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {border_color};">
                    <p><strong>Student Name:</strong> {student_name}</p>
                    <p><strong>Grade Level:</strong> {grade}</p>
                    <p><strong>Decision Time:</strong> {timestamp}</p>
                    <p style="margin-top: 15px;"><strong>Result:</strong> {"Your child's" if recipient_type == "parents" else "Your"} appeal was <strong>{"Excused" if is_excused else "Unexcused"}</strong>.</p>
                    {reason_type_line}
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;"><strong>📋 Important Policy Reminder:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #856404;">According to school policy, whether {"your child's" if recipient_type == "parents" else "your"} appeal is excused or unexcused, {"your child's" if recipient_type == "parents" else "your"} violation count will remain unchanged and will still be counted.</p>
                    {"<p style=\"margin: 5px 0 0 0; color: #856404;\"><strong>Current Violation Count:</strong> " + str(violation_count) + "</p>" if violation_count is not None else ""}
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
        
        print(f"✅ Appeal result email sent to {to_email}: {student_name} ({grade}) - {status_text}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending appeal result email: {str(e)}")
        return False

def send_appeal_result_sms(to_phone, student_name, grade, timestamp, reason_type, recipient_type="student", violation_count=None, display_reason_type=None):
    """
    Send appeal result notification SMS
    reason_type: "Excused" (approved) or "Unexcused" (not approved) - from violation_history document
    display_reason_type: The violation type to display (e.g., "incomplete_uniform") - from last_violation_type in parent document
    """
    # Format phone number for Philippines
    if not to_phone.startswith('+63'):
        if to_phone.startswith('0'):
            to_phone = '+63' + to_phone[1:]
        elif to_phone.startswith('63'):
            to_phone = '+' + to_phone
        else:
            to_phone = '+63' + to_phone
    
    # Check if appeal was approved: "Excused" means approved (case-insensitive)
    # Use reason_type from violation_history document for approval logic
    is_excused = reason_type and reason_type.lower() == "excused"
    status_text = "Approved" if is_excused else "Not Approved"
    
    # Determine excused status text
    excused_status = "Excused" if is_excused else "Unexcused"
    
    if recipient_type == "student":
        message = f"Hi {student_name}! Your appeal was {excused_status} at {timestamp}. Important: According to school policy, whether your appeal is excused or unexcused, your violation count will remain unchanged.{" Current Violations: " + str(violation_count) if violation_count is not None else ""}\n\nPowered by AI-niform Technology"
    else:  # parents
        message = f"Dear Parent, {student_name} ({grade}) appeal was {excused_status} at {timestamp}. Important: According to school policy, whether the appeal is excused or unexcused, your child's violation count will remain unchanged.{" Current Violations: " + str(violation_count) if violation_count is not None else ""}\n\nPowered by AI-niform Technology"
    
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
                print(f"✅ Appeal result SMS sent to {to_phone}: {student_name} ({grade}) - {status_text}")
                return True
            else:
                print(f"❌ Appeal result SMS failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending appeal result SMS: {str(e)}")
        return False

def send_combined_notification(email, phone, student_name, grade, timestamp, action_type="check-in", recipient_type="parents", violation_type=None, violation_details=None, violation_count=None, recent_activities=None, missing_items=None):
    """
    Send both email and SMS notifications simultaneously
    """
    print(f"\n📧 Sending EMAIL notification...")
    email_success = send_email(email, student_name, grade, timestamp, action_type, recipient_type, violation_type, violation_details, violation_count, recent_activities, missing_items)
    
    print(f"\n📱 Sending SMS notification...")
    sms_success = send_sms(phone, student_name, grade, timestamp, action_type, recipient_type, violation_type, violation_details, violation_count, recent_activities, missing_items)
    
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
            
            # Create violation_history document with message1 and message2 fields
            # Structure: student_violations/{student_number}/violation_history/{violation_id}
            violation_history_data = violation_data.copy()  # Copy all violation data
            violation_history_data.update({
                'message1': "false",  # Default: violation notification not sent yet
                'message2': "false",  # Default: appeal result notification not sent yet
                'status': "pending",  # Status for message1 (pending = not appealed yet)
                'created_at': datetime.now(pytz.timezone('Asia/Manila')).isoformat()
            })
            
            # Add details field if violation_details exists
            if violation_details:
                violation_history_data['details'] = violation_details
            
            violation_history_ref = student_violation_doc.collection("violation_history")
            violation_history_ref.document(violation_id).set(violation_history_data)
            
            print(f"\n[OK] Violation saved to student_violations for student {student_number}")
            print(f"     Updated violation count: {new_count} (added 1)")
            print(f"     Violation ID: {violation_id}")
            print(f"     Violation history document created with message1=false, message2=false")
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
            
            # Create violation_history document with message1 and message2 fields
            # Structure: student_violations/{student_number}/violation_history/{violation_id}
            violation_history_data = violation_data.copy()  # Copy all violation data
            violation_history_data.update({
                'message1': "false",  # Default: violation notification not sent yet
                'message2': "false",  # Default: appeal result notification not sent yet
                'status': "pending",  # Status for message1 (pending = not appealed yet)
                'created_at': datetime.now(pytz.timezone('Asia/Manila')).isoformat()
            })
            
            # Add details field if violation_details exists
            if violation_details:
                violation_history_data['details'] = violation_details
            
            violation_history_ref = student_violation_doc.collection("violation_history")
            violation_history_ref.document(violation_id).set(violation_history_data)
            
            print(f"\n[OK] Created new violation record for student {student_number}")
            print(f"     Violation count: 1")
            print(f"     Violation ID: {violation_id}")
            print(f"     Violation history document created with message1=false, message2=false")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n[WARNING] serviceAccountKey.json not found. Violation not saved to Firebase.")
        print(f"         Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[WARNING] Error saving violation to Firebase: {str(e)}")
        return False

def fetch_undelivered_violations():
    """
    Fetch violation logs from violation_history subcollection where:
    - message1 == false AND status == "pending" (initial violation notification)
    - message2 == false AND reason_type exists (appeal result notification)
    Structure: student_violations/{student_id}/violation_history/{log_id}
    Uses Firestore queries to filter server-side, reducing read operations
    Returns a tuple: (list of violation log documents, count of parent documents read)
    """
    try:
        db = initialize_firebase()
        student_violations_ref = db.collection("student_violations")
        undelivered = []
        parent_docs_read = 0
        
        # Get all student_violations documents (these are the student_id documents)
        # We need to check each one's violation_history subcollection
        # Note: Each document in the stream() call counts as 1 read
        try:
            student_violations_docs = student_violations_ref.stream()
            
            for student_doc in student_violations_docs:
                parent_docs_read += 1  # Count parent document read
                student_id = student_doc.id
                
                # Get violation_count from parent document
                parent_data = student_doc.to_dict()
                parent_violation_count = parent_data.get('violation_count', 1)
                
                # Access the violation_history subcollection for this student
                violation_history_ref = student_doc.reference.collection("violation_history")
                
                # Query for message1 == false (string) with status == "pending" - initial violation notification
                try:
                    logs_query = violation_history_ref.where(filter=FieldFilter('message1', '==', "false")).where(filter=FieldFilter('status', '==', "pending")).stream()
                    for log_doc in logs_query:
                        log_id = log_doc.id
                        # Ensure message1 and message2 fields exist in this document
                        ensure_message_fields_exist(student_id, log_id)
                        log_data = log_doc.to_dict()
                        log_data['log_id'] = log_id
                        log_data['student_id'] = student_id
                        log_data['doc_id'] = log_id
                        log_data['parent_doc_id'] = student_id
                        log_data['violation_count'] = parent_violation_count
                        log_data['message_type'] = 'message1'  # Mark as message1 type
                        undelivered.append(log_data)
                except Exception as e:
                    print(f"[WARNING] Error querying violation_history (message1) for student {student_id}: {str(e)}")
                
                # Also query for message1 == False (boolean) with status == "pending"
                try:
                    logs_query = violation_history_ref.where(filter=FieldFilter('message1', '==', False)).where(filter=FieldFilter('status', '==', "pending")).stream()
                    for log_doc in logs_query:
                        log_id = log_doc.id
                        # Ensure message1 and message2 fields exist in this document
                        ensure_message_fields_exist(student_id, log_id)
                        # Avoid duplicates
                        if not any(v.get('log_id') == log_id and v.get('student_id') == student_id and v.get('message_type') == 'message1' for v in undelivered):
                            log_data = log_doc.to_dict()
                            log_data['log_id'] = log_id
                            log_data['student_id'] = student_id
                            log_data['doc_id'] = log_id
                            log_data['parent_doc_id'] = student_id
                            log_data['violation_count'] = parent_violation_count
                            log_data['message_type'] = 'message1'
                            undelivered.append(log_data)
                except Exception as e:
                    print(f"[WARNING] Error querying violation_history (message1 boolean) for student {student_id}: {str(e)}")
                
                # Query for message2 == false (string) - appeal result notification
                # Check if reason_type exists (will filter in Python since we need to check for existence)
                try:
                    logs_query = violation_history_ref.where(filter=FieldFilter('message2', '==', "false")).stream()
                    for log_doc in logs_query:
                        log_id = log_doc.id
                        # Ensure message1 and message2 fields exist in this document
                        ensure_message_fields_exist(student_id, log_id)
                        log_data = log_doc.to_dict()
                        # Only include if reason_type exists (Excused or Unexcused)
                        if 'reason_type' in log_data and log_data.get('reason_type') in ['Excused', 'Unexcused']:
                            # Avoid duplicates
                            if not any(v.get('log_id') == log_id and v.get('student_id') == student_id and v.get('message_type') == 'message2' for v in undelivered):
                                log_data['log_id'] = log_id
                                log_data['student_id'] = student_id
                                log_data['doc_id'] = log_id
                                log_data['parent_doc_id'] = student_id
                                log_data['violation_count'] = parent_violation_count
                                log_data['message_type'] = 'message2'  # Mark as message2 type
                                undelivered.append(log_data)
                except Exception as e:
                    print(f"[WARNING] Error querying violation_history (message2) for student {student_id}: {str(e)}")
                
                # Also query for message2 == False (boolean)
                try:
                    logs_query = violation_history_ref.where(filter=FieldFilter('message2', '==', False)).stream()
                    for log_doc in logs_query:
                        log_id = log_doc.id
                        # Ensure message1 and message2 fields exist in this document
                        ensure_message_fields_exist(student_id, log_id)
                        log_data = log_doc.to_dict()
                        # Only include if reason_type exists (Excused or Unexcused)
                        if 'reason_type' in log_data and log_data.get('reason_type') in ['Excused', 'Unexcused']:
                            # Avoid duplicates
                            if not any(v.get('log_id') == log_id and v.get('student_id') == student_id and v.get('message_type') == 'message2' for v in undelivered):
                                log_data['log_id'] = log_id
                                log_data['student_id'] = student_id
                                log_data['doc_id'] = log_id
                                log_data['parent_doc_id'] = student_id
                                log_data['violation_count'] = parent_violation_count
                                log_data['message_type'] = 'message2'
                                undelivered.append(log_data)
                except Exception as e:
                    print(f"[WARNING] Error querying violation_history (message2 boolean) for student {student_id}: {str(e)}")
                    
        except Exception as e:
            print(f"[ERROR] Error fetching student_violations documents: {str(e)}")
        
        return undelivered, parent_docs_read
    except Exception as e:
        print(f"[ERROR] Error fetching undelivered violations: {str(e)}")
        return [], 0

# Global student cache to prevent re-reading the same student documents
_student_cache = {}
_cache_hits = 0
_cache_misses = 0
_cache_last_refresh = None  # Timestamp of last full cache refresh
_force_refresh_flag = False  # Flag to force refresh on next cycle

# Global violation count cache (from student_violations parent documents)
_violation_count_cache = {}

def fetch_all_undelivered_activities():
    """
    Fetch ALL activities from student_activities collection where message=false AND date is today
    Structure: student_activities collection with message field
    Only returns activities from today's date (Asia/Manila timezone), ignoring past dates
    
    Returns:
        List of activity dictionaries with message=false from today, ordered by most recent first
    """
    try:
        db = initialize_firebase()
        student_activities_ref = db.collection("student_activities")
        activities = []
        
        # Get today's date in Asia/Manila timezone (for date comparison)
        ph_tz = pytz.timezone('Asia/Manila')
        today = datetime.now(ph_tz).date()  # Get today's date (without time)
        
        # Helper function to check if timestamp is from today
        def is_today(timestamp):
            """Check if timestamp is from today"""
            if timestamp is None:
                return False
            
            try:
                # Handle different timestamp formats
                if isinstance(timestamp, datetime):
                    # If it's already a datetime, convert to Asia/Manila timezone
                    if timestamp.tzinfo is None:
                        # Assume it's in Asia/Manila if no timezone info
                        timestamp = ph_tz.localize(timestamp)
                    else:
                        # Convert to Asia/Manila timezone
                        timestamp = timestamp.astimezone(ph_tz)
                    return timestamp.date() == today
                elif isinstance(timestamp, str):
                    # Try to parse string timestamp
                    try:
                        # Try ISO format
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = ph_tz.localize(dt)
                        else:
                            dt = dt.astimezone(ph_tz)
                        return dt.date() == today
                    except:
                        # Try other common formats
                        try:
                            # Try format like "2024-01-15 10:30:00"
                            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                            dt = ph_tz.localize(dt)
                            return dt.date() == today
                        except:
                            # Try format like "2024-01-15"
                            try:
                                dt = datetime.strptime(timestamp, "%Y-%m-%d")
                                dt = ph_tz.localize(dt)
                                return dt.date() == today
                            except:
                                # If parsing fails, check if string contains today's date
                                return str(today) in timestamp or today.strftime("%Y-%m-%d") in timestamp
                else:
                    return False
            except Exception as e:
                # If any error occurs, skip this activity (conservative approach)
                return False
        
        # Query for all activities where message == "false" (string)
        try:
            activities_query = student_activities_ref.where(filter=FieldFilter('message', '==', "false")).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                
                # Check if activity is from today
                timestamp = activity_data.get('timestamp') or activity_data.get('recorded_at') or activity_data.get('time') or activity_data.get('date')
                if is_today(timestamp):
                    # Avoid duplicates
                    if not any(a.get('activity_id') == doc.id for a in activities):
                        activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (message=false string): {str(e)}")
        
        # Also try message == False (boolean)
        try:
            activities_query = student_activities_ref.where(filter=FieldFilter('message', '==', False)).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                
                # Check if activity is from today
                timestamp = activity_data.get('timestamp') or activity_data.get('recorded_at') or activity_data.get('time') or activity_data.get('date')
                if is_today(timestamp):
                    # Avoid duplicates
                    if not any(a.get('activity_id') == doc.id for a in activities):
                        activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (message=False boolean): {str(e)}")
        
        # Sort by timestamp if available (most recent first)
        if activities:
            try:
                # Try to sort by timestamp (could be string or datetime)
                def get_sort_key(activity):
                    timestamp = activity.get('timestamp') or activity.get('recorded_at') or activity.get('time') or ''
                    # If it's a string, try to parse it, otherwise use as-is
                    if isinstance(timestamp, str):
                        try:
                            # Try to parse ISO format
                            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            return timestamp
                    return timestamp
                
                activities.sort(key=get_sort_key, reverse=True)
            except Exception as e:
                # If sorting fails, keep original order
                pass
        
        return activities
    except Exception as e:
        print(f"[ERROR] Error fetching all undelivered activities: {str(e)}")
        return []

def get_latest_activities(student_id, limit=None):
    """
    Get all activities from student_activities collection for a student where message=false
    Structure: student_activities collection with student_id field and message field
    
    Args:
        student_id: The student ID to fetch activities for
        limit: Optional limit on number of activities (default: None, returns all with message=false)
    
    Returns:
        List of activity dictionaries with message=false, ordered by most recent first
    """
    try:
        db = initialize_firebase()
        student_activities_ref = db.collection("student_activities")
        
        # Query for activities by student_id AND message=false
        # Try different field name variations
        activities = []
        
        # Try 'student_id' field with message=false filter
        try:
            # Query for student_id AND message == "false" (string)
            activities_query = student_activities_ref.where(filter=FieldFilter('student_id', '==', str(student_id))).where(filter=FieldFilter('message', '==', "false")).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                # Avoid duplicates
                if not any(a.get('activity_id') == doc.id for a in activities):
                    activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (student_id, message=false string): {str(e)}")
        
        # Also try message == False (boolean)
        try:
            activities_query = student_activities_ref.where(filter=FieldFilter('student_id', '==', str(student_id))).where(filter=FieldFilter('message', '==', False)).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                # Avoid duplicates
                if not any(a.get('activity_id') == doc.id for a in activities):
                    activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (student_id, message=False boolean): {str(e)}")
        
        # Note: Skipping 'Student ID' field (with space) as Firestore FieldFilter doesn't support spaces in field names
        # We'll rely on 'student_id' and 'student_number' field variations instead
        
        # Try 'student_number' field with message=false filter
        try:
            activities_query = student_activities_ref.where(filter=FieldFilter('student_number', '==', str(student_id))).where(filter=FieldFilter('message', '==', "false")).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                # Avoid duplicates
                if not any(a.get('activity_id') == doc.id for a in activities):
                    activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (student_number, message=false string): {str(e)}")
        
        # Also try message == False (boolean) for 'student_number' field
        try:
            activities_query = student_activities_ref.where(filter=FieldFilter('student_number', '==', str(student_id))).where(filter=FieldFilter('message', '==', False)).stream()
            for doc in activities_query:
                activity_data = doc.to_dict()
                activity_data['activity_id'] = doc.id
                # Avoid duplicates
                if not any(a.get('activity_id') == doc.id for a in activities):
                    activities.append(activity_data)
        except Exception as e:
            print(f"[WARNING] Error querying activities (student_number, message=False boolean): {str(e)}")
        
        # Sort by timestamp if available (most recent first)
        if activities:
            try:
                # Try to sort by timestamp (could be string or datetime)
                def get_sort_key(activity):
                    timestamp = activity.get('timestamp') or activity.get('recorded_at') or activity.get('time') or ''
                    # If it's a string, try to parse it, otherwise use as-is
                    if isinstance(timestamp, str):
                        try:
                            # Try to parse ISO format
                            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            return timestamp
                    return timestamp
                
                activities.sort(key=get_sort_key, reverse=True)
            except Exception as e:
                # If sorting fails, keep original order
                pass
            
            # Apply limit if specified
            if limit is not None and limit > 0:
                activities = activities[:limit]
        
        return activities
    except Exception as e:
        print(f"[ERROR] Error fetching activities for student {student_id}: {str(e)}")
        return []

def update_activity_message_status(activity_id, status="true"):
    """
    Update the message field in student_activities document to indicate delivery status
    Structure: student_activities/{activity_id}
    
    Args:
        activity_id: The activity document ID in student_activities collection
        status: "true" for delivered, "false" for not delivered
    """
    try:
        db = initialize_firebase()
        student_activities_ref = db.collection("student_activities")
        activity_doc = student_activities_ref.document(str(activity_id))
        
        update_data = {
            'message': status,
            'message_updated_at': datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        }
        
        activity_doc.update(update_data)
        return True
    except Exception as e:
        print(f"[ERROR] Error updating message status for activity {activity_id}: {str(e)}")
        return False

def get_violation_count_from_parent(student_id, use_cache=True):
    """
    Get violation_count from student_violations parent document
    Structure: student_violations/{student_id}
    Uses caching to prevent re-reading the same document multiple times
    
    Args:
        student_id: The student ID (document ID in student_violations collection)
        use_cache: If True, uses cache to avoid re-reading (default: True)
    """
    global _violation_count_cache
    
    # Check cache first
    if use_cache and student_id in _violation_count_cache:
        return _violation_count_cache[student_id]
    
    # Cache miss - need to read from Firebase
    try:
        db = initialize_firebase()
        student_violations_ref = db.collection("student_violations")
        parent_doc = student_violations_ref.document(str(student_id)).get()
        
        if parent_doc.exists:
            parent_data = parent_doc.to_dict()
            violation_count = parent_data.get('violation_count', 1)
            # Cache the result
            if use_cache:
                _violation_count_cache[student_id] = violation_count
            return violation_count
        else:
            # Document doesn't exist, return default
            default_count = 1
            if use_cache:
                _violation_count_cache[student_id] = default_count
            return default_count
    except Exception as e:
        print(f"[ERROR] Error fetching violation_count for student {student_id}: {str(e)}")
        return 1  # Default to 1 if error

def get_last_violation_type_from_parent(student_id, use_cache=True):
    """
    Get last_violation_type from student_violations parent document
    Structure: student_violations/{student_id}
    Uses caching to prevent re-reading the same document multiple times
    
    Args:
        student_id: The student ID (document ID in student_violations collection)
        use_cache: If True, uses cache to avoid re-reading (default: True)
    
    Returns:
        The last_violation_type value (e.g., "Excused" or "Unexcused") or empty string if not found
    """
    global _violation_count_cache
    
    # Use the same cache key pattern but store last_violation_type separately
    # We'll create a new cache for this
    if not hasattr(get_last_violation_type_from_parent, '_cache'):
        get_last_violation_type_from_parent._cache = {}
    
    # Check cache first
    if use_cache and student_id in get_last_violation_type_from_parent._cache:
        return get_last_violation_type_from_parent._cache[student_id]
    
    # Cache miss - need to read from Firebase
    # Reading from parent document: student_violations/{student_id} (NOT from violation_history subcollection)
    try:
        db = initialize_firebase()
        student_violations_ref = db.collection("student_violations")
        parent_doc = student_violations_ref.document(str(student_id)).get()
        
        if parent_doc.exists:
            parent_data = parent_doc.to_dict()
            # Get last_violation_type from the parent document directly
            last_violation_type = parent_data.get('last_violation_type', '')
            # Cache the result
            if use_cache:
                get_last_violation_type_from_parent._cache[student_id] = last_violation_type
            return last_violation_type
        else:
            # Document doesn't exist, return empty string
            if use_cache:
                get_last_violation_type_from_parent._cache[student_id] = ''
            return ''
    except Exception as e:
        print(f"[ERROR] Error fetching last_violation_type for student {student_id}: {str(e)}")
        return ''  # Default to empty string if error

def get_student_by_id(student_id, use_cache=True):
    """
    Get student information from students collection by student_id
    Uses caching to prevent re-reading the same student document multiple times
    Returns student data dictionary or None if not found
    
    Args:
        student_id: The student ID to look up
        use_cache: If True, uses cache to avoid re-reading (default: True)
    """
    global _student_cache, _cache_hits, _cache_misses
    
    # Check cache first to avoid Firebase reads
    if use_cache and student_id in _student_cache:
        _cache_hits += 1
        return _student_cache[student_id]
    
    # Cache miss - need to read from Firebase
    _cache_misses += 1
    try:
        db = initialize_firebase()
        students_ref = db.collection("students")
        
        # Try to find student by various ID fields
        # First try direct document ID (most efficient - 1 read)
        student_doc = students_ref.document(str(student_id)).get()
        if student_doc.exists:
            student_data = student_doc.to_dict()
            student_data['doc_id'] = student_doc.id
            # Cache the result
            if use_cache:
                _student_cache[student_id] = student_data
            return student_data
        
        # If not found, search by Student Number field (query - 1 read per document)
        students_query = students_ref.where(filter=FieldFilter('Student Number', '==', str(student_id))).stream()
        for doc in students_query:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id
            # Cache the result using both student_id and the found doc_id
            if use_cache:
                _student_cache[student_id] = student_data
                _student_cache[doc.id] = student_data  # Also cache by doc_id
            return student_data
        
        # Try other field names (query - 1 read per document)
        students_query = students_ref.where(filter=FieldFilter('student_number', '==', str(student_id))).stream()
        for doc in students_query:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id
            if use_cache:
                _student_cache[student_id] = student_data
                _student_cache[doc.id] = student_data
            return student_data
        
        students_query = students_ref.where(filter=FieldFilter('student_id', '==', str(student_id))).stream()
        for doc in students_query:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id
            if use_cache:
                _student_cache[student_id] = student_data
                _student_cache[doc.id] = student_data
            return student_data
        
        # Try searching by RFID field (RFID numbers are valid student identifiers)
        students_query = students_ref.where(filter=FieldFilter('RFID', '==', str(student_id))).stream()
        for doc in students_query:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id
            if use_cache:
                _student_cache[student_id] = student_data
                _student_cache[doc.id] = student_data
            return student_data
        
        # Try lowercase RFID field
        students_query = students_ref.where(filter=FieldFilter('rfid', '==', str(student_id))).stream()
        for doc in students_query:
            student_data = doc.to_dict()
            student_data['doc_id'] = doc.id
            if use_cache:
                _student_cache[student_id] = student_data
                _student_cache[doc.id] = student_data
            return student_data
        
        # Not found - cache None to avoid repeated failed lookups
        if use_cache:
            _student_cache[student_id] = None
        return None
    except Exception as e:
        print(f"[ERROR] Error fetching student by ID {student_id}: {str(e)}")
        return None

def get_cache_stats():
    """Get cache statistics"""
    global _student_cache, _cache_hits, _cache_misses, _cache_last_refresh
    total_requests = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    # Calculate time since last refresh
    time_since_refresh = None
    if _cache_last_refresh:
        time_since_refresh = datetime.now(pytz.timezone('Asia/Manila')) - _cache_last_refresh
        hours_since_refresh = time_since_refresh.total_seconds() / 3600
    else:
        hours_since_refresh = None
    
    return {
        'cache_size': len([v for v in _student_cache.values() if v is not None]),
        'cache_hits': _cache_hits,
        'cache_misses': _cache_misses,
        'hit_rate': hit_rate,
        'last_refresh': _cache_last_refresh,
        'hours_since_refresh': hours_since_refresh
    }

def clear_student_cache():
    """Clear the student cache (useful if student data is updated)"""
    global _student_cache, _cache_hits, _cache_misses, _cache_last_refresh, _violation_count_cache
    _student_cache.clear()
    _violation_count_cache.clear()  # Also clear violation count cache
    _cache_hits = 0
    _cache_misses = 0
    _cache_last_refresh = datetime.now(pytz.timezone('Asia/Manila'))
    print(f"   🔄 Student cache cleared and refresh timestamp updated: {_cache_last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

def should_refresh_cache():
    """Check if cache should be refreshed (once per day)"""
    global _cache_last_refresh, _force_refresh_flag
    
    # Force refresh flag takes priority
    if _force_refresh_flag:
        _force_refresh_flag = False
        return True
    
    # If never refreshed, refresh now
    if _cache_last_refresh is None:
        return True
    
    # Check if 24 hours have passed
    now = datetime.now(pytz.timezone('Asia/Manila'))
    time_since_refresh = now - _cache_last_refresh
    
    # Refresh if 24 hours or more have passed
    if time_since_refresh >= timedelta(hours=24):
        return True
    
    return False

def force_refresh_cache():
    """Force refresh the student cache on next cycle"""
    global _force_refresh_flag
    _force_refresh_flag = True
    print("\n   🔄 Force refresh flag set. Cache will be refreshed on next cycle.")

def ensure_message_fields_exist(parent_doc_id, log_id):
    """
    Ensure that message1 and message2 fields exist in violation_history document
    If they don't exist, set them to "false"
    Structure: student_violations/{parent_doc_id}/violation_history/{log_id}
    
    Args:
        parent_doc_id: The student_id document ID in student_violations collection
        log_id: The log document ID in violation_history subcollection
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db = initialize_firebase()
        student_violation_doc = db.collection("student_violations").document(str(parent_doc_id))
        violation_history_ref = student_violation_doc.collection("violation_history")
        log_doc = violation_history_ref.document(str(log_id))
        
        # Get current document to check if fields exist
        current_doc = log_doc.get()
        
        if current_doc.exists:
            current_data = current_doc.to_dict()
            update_needed = False
            update_data = {}
            
            # Check if message1 exists, if not add it
            if 'message1' not in current_data:
                update_data['message1'] = "false"
                update_needed = True
            
            # Check if message2 exists, if not add it
            if 'message2' not in current_data:
                update_data['message2'] = "false"
                update_needed = True
            
            # Only update if fields are missing
            if update_needed:
                log_doc.update(update_data)
                return True
            return True  # Fields already exist
        else:
            # Document doesn't exist yet, create it with both fields
            log_doc.set({
                'message1': "false",
                'message2': "false"
            }, merge=False)
            return True
    except Exception as e:
        print(f"[ERROR] Error ensuring message fields exist for log {log_id} in student {parent_doc_id}: {str(e)}")
        return False

def update_message_status(parent_doc_id, log_id, message_field="message1", status="true"):
    """
    Update the message1 or message2 field in violation_history log document to indicate delivery status
    Also ensures that both message1 and message2 fields exist in the document
    Structure: student_violations/{parent_doc_id}/violation_history/{log_id}
    
    Args:
        parent_doc_id: The student_id document ID in student_violations collection
        log_id: The log document ID in violation_history subcollection
        message_field: "message1" or "message2" (default: "message1")
        status: "true" for delivered, "false" for not delivered
    """
    try:
        # First ensure both message fields exist
        ensure_message_fields_exist(parent_doc_id, log_id)
        
        db = initialize_firebase()
        # Access the violation_history subcollection for this student
        student_violation_doc = db.collection("student_violations").document(str(parent_doc_id))
        violation_history_ref = student_violation_doc.collection("violation_history")
        log_doc = violation_history_ref.document(str(log_id))
        
        update_data = {
            message_field: status,
            f'{message_field}_updated_at': datetime.now(pytz.timezone('Asia/Manila')).isoformat()
        }
        
        log_doc.update(update_data)
        return True
    except Exception as e:
        print(f"[ERROR] Error updating {message_field} status for log {log_id} in student {parent_doc_id}: {str(e)}")
        return False

# --- Global flag for graceful shutdown ---
running = True
paused = False  # Pause state for the main loop

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n🛑 Shutting down gracefully...")
    running = False
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

def user_input_handler():
    """Background thread to handle user input for force refresh"""
    global running, paused
    # Small delay to let main thread initialize
    time.sleep(1)
    while running:
        try:
            # Note: This will block until user presses Enter
            # Users can type commands while the system is running
            user_input = input().strip().lower()
            if user_input == 'refresh' or user_input == 'r':
                force_refresh_cache()
            elif user_input == 'pause' or user_input == 'p':
                paused = not paused
                if paused:
                    print("\n   ⏸️  System PAUSED. Type 'p' or 'pause' again to resume.")
                else:
                    print("\n   ▶️  System RESUMED.")
            elif user_input == 'help' or user_input == 'h':
                print("\n   📖 Available commands:")
                print("      'refresh' or 'r' - Force refresh student cache on next cycle")
                print("      'pause' or 'p' - Pause/resume the system")
                print("      'help' or 'h' - Show this help message")
                print("      'stats' or 's' - Show cache statistics")
                print("      'usage' or 'u' - Show Firebase usage estimate and limits")
            elif user_input == 'usage' or user_input == 'u':
                print(get_firebase_usage_info())
            elif user_input == 'stats' or user_input == 's':
                stats = get_cache_stats()
                print("\n   📊 Cache Statistics:")
                print(f"      Students cached: {stats['cache_size']}")
                print(f"      Cache hits: {stats['cache_hits']}")
                print(f"      Cache misses: {stats['cache_misses']}")
                print(f"      Hit rate: {stats['hit_rate']:.1f}%")
                if stats['last_refresh']:
                    print(f"      Last refresh: {stats['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")
                    if stats['hours_since_refresh'] is not None:
                        if stats['hours_since_refresh'] >= 1:
                            print(f"      Hours since refresh: {stats['hours_since_refresh']:.1f}")
                        else:
                            minutes = stats['hours_since_refresh'] * 60
                            print(f"      Minutes since refresh: {minutes:.0f}")
                else:
                    print(f"      Last refresh: Never")
            elif user_input:
                print(f"\n   ⚠️  Unknown command: '{user_input}'. Type 'help' for available commands.")
        except EOFError:
            # Handle EOF (when input is redirected or terminal closed)
            break
        except Exception as e:
            # Ignore input errors (e.g., when stdin is not available)
            if running:
                time.sleep(1)  # Wait a bit before retrying

# --- Main execution ---
print("=" * 70)
print("Automated Violation Notification System")
print("=" * 70)
print("This system continuously monitors student_violations collection")
print("and sends notifications for undelivered violations (message: false)")
print(f"Polling interval: {POLLING_INTERVAL_SECONDS} seconds")
print("Press Ctrl+C to stop the service")
print("=" * 70)
print("\n💡 Firebase Read Optimization:")
print(f"   - Using server-side queries (only reads documents with message='false')")
print(f"   - Student data caching enabled (prevents re-reading same student)")
print(f"   - Cache auto-refreshes once per day (24 hours)")
print(f"   - Polling every {POLLING_INTERVAL_SECONDS} seconds")
cycles_per_day = int(86400 / POLLING_INTERVAL_SECONDS)
print(f"   - Cycles per day: ~{cycles_per_day}")
print(f"   - Note: Only reads documents that match query, not all documents!")
print(f"   - Note: Student cache prevents duplicate reads for same student")
print("\n⌨️  Terminal Commands (type during operation):")
print("   - 'pause' or 'p' - Pause/resume the system")
print("   - 'refresh' or 'r' - Force refresh student cache")
print("   - 'stats' or 's' - Show cache statistics")
print("   - 'usage' or 'u' - Show Firebase usage estimate and limits")
print("   - 'help' or 'h' - Show available commands")
print("=" * 70)

# Initialize Firebase
try:
    db = initialize_firebase()
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"❌ Error initializing Firebase: {str(e)}")
    print("Exiting...")
    sys.exit(1)

# Start background thread for user input
input_thread = threading.Thread(target=user_input_handler, daemon=True)
input_thread.start()
print("✅ User input handler started (type 'help' for commands)")

ph_tz = pytz.timezone('Asia/Manila')
cycle_count = 0
total_violation_reads = 0  # Track violation document reads
total_student_reads = 0    # Track student document reads
session_start_time = datetime.now(pytz.timezone('Asia/Manila'))  # Track session start for usage estimation

# Firebase Free Tier Limits (Spark Plan)
FIREBASE_FREE_TIER_READS_PER_DAY = 50000
FIREBASE_FREE_TIER_WRITES_PER_DAY = 20000
FIREBASE_FREE_TIER_DELETES_PER_DAY = 20000

def estimate_daily_reads(total_reads, session_duration_seconds):
    """
    Estimate daily read usage based on current session rate
    
    Args:
        total_reads: Total reads in current session
        session_duration_seconds: How long the session has been running (seconds)
    
    Returns:
        dict with estimated daily reads, percentage of limit, and status
    """
    if session_duration_seconds <= 0:
        return {
            'estimated_daily_reads': 0,
            'percentage_of_limit': 0,
            'status': 'unknown',
            'reads_per_hour': 0
        }
    
    # Calculate reads per second
    reads_per_second = total_reads / session_duration_seconds
    
    # Estimate reads per day (24 hours = 86400 seconds)
    estimated_daily_reads = reads_per_second * 86400
    
    # Calculate percentage of free tier limit
    percentage_of_limit = (estimated_daily_reads / FIREBASE_FREE_TIER_READS_PER_DAY) * 100
    
    # Determine status
    if percentage_of_limit >= 100:
        status = 'exceeded'
    elif percentage_of_limit >= 90:
        status = 'critical'
    elif percentage_of_limit >= 75:
        status = 'warning'
    elif percentage_of_limit >= 50:
        status = 'moderate'
    else:
        status = 'safe'
    
    reads_per_hour = reads_per_second * 3600
    
    return {
        'estimated_daily_reads': int(estimated_daily_reads),
        'percentage_of_limit': percentage_of_limit,
        'status': status,
        'reads_per_hour': int(reads_per_hour),
        'session_duration_hours': session_duration_seconds / 3600
    }

def get_firebase_usage_info():
    """
    Get comprehensive Firebase usage information
    Returns a formatted string with usage statistics
    """
    global total_violation_reads, total_student_reads, session_start_time
    
    total_reads = total_violation_reads + total_student_reads
    current_time = datetime.now(pytz.timezone('Asia/Manila'))
    session_duration = (current_time - session_start_time).total_seconds()
    
    usage = estimate_daily_reads(total_reads, session_duration)
    
    # Status emoji
    status_emoji = {
        'safe': '✅',
        'moderate': '⚠️',
        'warning': '⚠️',
        'critical': '🔴',
        'exceeded': '❌',
        'unknown': '❓'
    }
    
    emoji = status_emoji.get(usage['status'], '❓')
    
    info = f"\n   {emoji} Firebase Usage Estimate:\n"
    info += f"      Session Duration: {usage['session_duration_hours']:.2f} hours\n"
    info += f"      Current Session Reads: {total_reads:,} ({total_violation_reads:,} violations + {total_student_reads:,} students)\n"
    info += f"      Reads per Hour: ~{usage['reads_per_hour']:,}\n"
    info += f"      Estimated Daily Reads: ~{usage['estimated_daily_reads']:,}\n"
    info += f"      Free Tier Limit: {FIREBASE_FREE_TIER_READS_PER_DAY:,} reads/day\n"
    info += f"      Usage: {usage['percentage_of_limit']:.1f}% of free tier limit\n"
    
    if usage['status'] == 'exceeded':
        info += f"      ⚠️  WARNING: Estimated usage EXCEEDS free tier limit!\n"
    elif usage['status'] == 'critical':
        info += f"      🔴 CRITICAL: Estimated usage is {usage['percentage_of_limit']:.1f}% of limit!\n"
    elif usage['status'] == 'warning':
        info += f"      ⚠️  WARNING: Estimated usage is {usage['percentage_of_limit']:.1f}% of limit\n"
    elif usage['status'] == 'moderate':
        info += f"      ℹ️  Moderate usage: {usage['percentage_of_limit']:.1f}% of limit\n"
    else:
        info += f"      ✅ Usage is within safe limits\n"
    
    info += f"\n   💡 To check actual Firebase usage:\n"
    info += f"      1. Go to https://console.firebase.google.com/\n"
    info += f"      2. Select your project\n"
    info += f"      3. Navigate to Firestore Database > Usage tab\n"
    
    return info

def write_message_fields():
    """
    Write message1 and message2 fields to Firestore violation_history subcollection
    This ensures all violation_history documents have message1 and message2 fields set to False
    Structure: student_violations/{student_doc_id}/violation_history/{violation_doc_id}
    """
    try:
        db = initialize_firebase()
        
        # Get all documents in student_violations collection
        student_violations_ref = db.collection('student_violations')
        student_violations = student_violations_ref.stream()
        
        total_updated = 0
        total_skipped = 0
        
        for student_doc in student_violations:
            student_doc_id = student_doc.id
            
            # Get all documents in violation_history subcollection
            violation_history_ref = student_violations_ref.document(student_doc_id).collection('violation_history')
            violation_docs = violation_history_ref.stream()
            
            for violation_doc in violation_docs:
                violation_doc_id = violation_doc.id
                violation_data = violation_doc.to_dict()
                
                # Check if message1 and message2 already exist
                if 'message1' in violation_data and 'message2' in violation_data:
                    total_skipped += 1
                    continue
                
                # Prepare update data
                update_data = {}
                if 'message1' not in violation_data:
                    update_data['message1'] = "false"
                if 'message2' not in violation_data:
                    update_data['message2'] = "false"
                
                # Write message1 and message2 fields if needed
                if update_data:
                    violation_doc_ref = violation_history_ref.document(violation_doc_id)
                    violation_doc_ref.update(update_data)
                    total_updated += 1
        
        if total_updated > 0 or total_skipped > 0:
            print(f"   📝 Message fields: Updated {total_updated}, Skipped {total_skipped} violation_history documents")
        
        return total_updated, total_skipped
        
    except Exception as e:
        print(f"   ❌ Error in write_message_fields: {str(e)}")
        return 0, 0

def write_student_activities_message():
    """
    Write message field to student_activities collection
    This ensures all student_activities documents have message field set to False
    Structure: student_activities/{activity_doc_id}
    """
    try:
        db = initialize_firebase()
        
        # Get all documents in student_activities collection
        student_activities_ref = db.collection('student_activities')
        activities_docs = student_activities_ref.stream()
        
        total_updated = 0
        total_skipped = 0
        
        for activity_doc in activities_docs:
            activity_doc_id = activity_doc.id
            activity_data = activity_doc.to_dict()
            
            # Check if message already exists
            if 'message' in activity_data:
                total_skipped += 1
                continue
            
            # Write message field (set to false)
            activity_doc_ref = student_activities_ref.document(activity_doc_id)
            activity_doc_ref.update({
                'message': "false"
            })
            total_updated += 1
        
        if total_updated > 0 or total_skipped > 0:
            print(f"   📝 Activity message fields: Updated {total_updated}, Skipped {total_skipped} student_activities documents")
        
        return total_updated, total_skipped
        
    except Exception as e:
        print(f"   ❌ Error in write_student_activities_message: {str(e)}")
        return 0, 0

# Main monitoring loop
while running:
    try:
        # Check if system is paused
        while paused and running:
            time.sleep(1)  # Wait while paused
        
        if not running:
            break  # Exit if stopped while paused
        
        cycle_count += 1
        current_time = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S")
        total_reads = total_violation_reads + total_student_reads
        cache_stats = get_cache_stats()
        
        # STEP 0: First, ensure message fields exist in violation_history and student_activities
        print(f"\n[{current_time}] Cycle #{cycle_count} - Step 0: Ensuring message fields exist...")
        print(f"   🔄 Processing student_violations/violation_history...")
        violation_updated, violation_skipped = write_message_fields()
        print(f"   🔄 Processing student_activities...")
        activity_updated, activity_skipped = write_student_activities_message()
        print(f"   ✅ Message fields check complete (Violations: {violation_updated} updated, {violation_skipped} skipped | Activities: {activity_updated} updated, {activity_skipped} skipped)")
        
        # Check if cache needs refresh (once per day or force refresh)
        if should_refresh_cache():
            print(f"\n[{current_time}] Cycle #{cycle_count} - Refreshing student cache...")
            clear_student_cache()
            print(f"   ✅ Cache refreshed. All student data will be re-fetched from Firebase when needed.")
        
        print(f"\n[{current_time}] Cycle #{cycle_count} - Checking for undelivered violations...")
        print(f"   📊 Total Firebase reads: {total_reads} (Violations: {total_violation_reads}, Students: {total_student_reads})")
        
        # Display cache info with refresh status
        cache_info = f"   💾 Student cache: {cache_stats['cache_size']} students cached | Hits: {cache_stats['cache_hits']} | Misses: {cache_stats['cache_misses']} | Hit rate: {cache_stats['hit_rate']:.1f}%"
        if cache_stats['last_refresh']:
            if cache_stats['hours_since_refresh'] is not None:
                if cache_stats['hours_since_refresh'] >= 1:
                    cache_info += f" | Last refresh: {cache_stats['hours_since_refresh']:.1f}h ago"
                else:
                    minutes = cache_stats['hours_since_refresh'] * 60
                    cache_info += f" | Last refresh: {minutes:.0f}m ago"
            else:
                cache_info += f" | Last refresh: {cache_stats['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            cache_info += " | Last refresh: Never"
        print(cache_info)
        
        # Check Firebase usage and show warnings if needed (only if session has been running for at least 1 minute)
        session_duration = (datetime.now(pytz.timezone('Asia/Manila')) - session_start_time).total_seconds()
        if session_duration >= 60:  # Only show after 1 minute of runtime
            usage = estimate_daily_reads(total_reads, session_duration)
            if usage['status'] in ['critical', 'exceeded']:
                print(f"\n   🔴 CRITICAL: Firebase usage estimate: {usage['percentage_of_limit']:.1f}% of free tier limit!")
                print(f"   💡 Type 'usage' or 'u' for detailed usage information")
            elif usage['status'] == 'warning' and cycle_count % 5 == 0:  # Show every 5 cycles
                print(f"\n   ⚠️  WARNING: Firebase usage estimate: {usage['percentage_of_limit']:.1f}% of free tier limit")
                print(f"   💡 Type 'usage' or 'u' for detailed usage information")
        
        # Fetch undelivered violations (uses server-side query - only reads matching documents)
        # Note: This reads student_violations documents AND violation_history logs
        undelivered_violations, parent_docs_read = fetch_undelivered_violations()
        
        # Count reads: 
        # - Each student_violations document checked = 1 read (parent documents)
        # - Each violation_history log returned = 1 read (log documents)
        violation_reads_this_cycle = parent_docs_read + len(undelivered_violations)
        total_violation_reads += violation_reads_this_cycle
        
        if not undelivered_violations:
            print(f"   ✓ No undelivered violations found.")
            print(f"   📊 Violation reads this cycle: {violation_reads_this_cycle} ({parent_docs_read} parent docs + {len(undelivered_violations)} logs)")
        else:
            print(f"   📋 Found {len(undelivered_violations)} undelivered violation log(s)")
            print(f"   📊 Violation reads this cycle: {violation_reads_this_cycle} ({parent_docs_read} parent docs + {len(undelivered_violations)} logs)")
            
            # STEP 1: Get unique student IDs from violations
            unique_student_ids = set()
            for violation in undelivered_violations:
                student_id = violation.get('student_id') or violation.get('parent_doc_id')
                if student_id:
                    unique_student_ids.add(student_id)
            
            print(f"\n   📋 Step 1: Found {len(unique_student_ids)} unique student(s) with violations")
            
            # STEP 2: Process each violation
            print(f"\n   📋 Step 2: Processing violations and sending notifications...")
            
            # Process each undelivered violation
            for violation in undelivered_violations:
                # Get the student_id from the violation log (this is the parent document ID)
                student_id = violation.get('student_id') or violation.get('parent_doc_id')
                log_id = violation.get('log_id') or violation.get('doc_id')
                
                if not student_id:
                    print(f"   ⚠️  Skipping violation log {log_id}: No student_id found")
                    continue
                
                if not log_id:
                    print(f"   ⚠️  Skipping violation for student {student_id}: No log_id found")
                    continue
                
                print(f"\n   Processing violation log {log_id} for student_id: {student_id}")
                
                # Ensure message1 and message2 fields exist in the violation_history document
                ensure_message_fields_exist(student_id, log_id)
                
                # Get student information from students collection (uses cache to avoid re-reading)
                # Only counts as a read if cache miss (cache hit = 0 reads)
                cache_misses_before = get_cache_stats()['cache_misses']
                student_info = get_student_by_id(student_id, use_cache=True)
                cache_misses_after = get_cache_stats()['cache_misses']
                
                # Only count as a read if there was a cache miss
                if cache_misses_after > cache_misses_before:
                    total_student_reads += 1  # 1 read only on cache miss
                    print(f"   📖 Student data read from Firebase (cache miss)")
                else:
                    print(f"   💾 Student data retrieved from cache (no read)")
                
                if not student_info:
                    # Try to find student by RFID number if available (RFID numbers are valid student identifiers)
                    rfid = violation.get('rfid') or violation.get('RFID')
                    if rfid:
                        print(f"   ℹ️  Student with ID {student_id} not found. Trying RFID number {rfid}...")
                        cache_misses_before_rfid = get_cache_stats()['cache_misses']
                        student_info = get_student_by_id(rfid, use_cache=True)
                        cache_misses_after_rfid = get_cache_stats()['cache_misses']
                        if cache_misses_after_rfid > cache_misses_before_rfid:
                            total_student_reads += 1
                            print(f"   📖 Student data read from Firebase using RFID (cache miss)")
                        if student_info:
                            print(f"   ✅ Found student using RFID number {rfid}")
                            # Don't update student_id to RFID - we'll use student_number from student_info for student_violations
                        else:
                            print(f"   ❌ Student not found using RFID {rfid} either. Skipping...")
                            continue
                    else:
                        print(f"   ❌ Student with ID {student_id} not found in students collection. Skipping...")
                        continue
                
                # Extract student information
                student_name = student_info.get('Name', student_info.get('name', violation.get('student_name', 'N/A')))
                student_grade = student_info.get('Course', student_info.get('course', student_info.get('grade', student_info.get('grade_level', violation.get('grade', 'N/A')))))
                student_email = student_info.get('Gmail', student_info.get('gmail', student_info.get('email', student_info.get('student_email', ''))))
                student_phone = student_info.get('Contact Number', student_info.get('contact_number', student_info.get('phone', student_info.get('student_phone', student_info.get('mobile', '')))))
                # Extract student_number - use this for student_violations (NOT RFID)
                student_number = student_info.get('Student Number', student_info.get('student_number', student_info.get('student_id', student_id)))
                
                # IMPORTANT: Use student_number (not student_id/RFID) when accessing student_violations
                # student_id might be an RFID number, but student_violations should use the actual student number
                
                # Extract parent information
                parent_email = student_info.get('Parent Gmail', student_info.get('parent_email', student_info.get('Parent Email', student_info.get('parent_email_address', ''))))
                parent_phone = student_info.get('Parent Number', student_info.get('parent_phone', student_info.get('Parent Phone', student_info.get('parent_contact_number', student_info.get('parent_mobile', '')))))
                
                # Extract violation information from violation log document
                # Priority: Use "details" field directly from the violation log
                details = violation.get('details', '')
                
                # Extract missing_items from violation data (for incomplete_uniform violations)
                missing_items = violation.get('missing_items') or violation.get('last_missing_items') or violation.get('Missing Items')
                
                # If details field exists and has content, use it as violation_details
                if details and details.strip():
                    violation_details = details.strip()
                    # Determine violation_type based on details content
                    details_lower = violation_details.lower()
                    # Only classify as missing_id if "missing id" is explicitly mentioned
                    # Otherwise, treat as incomplete_uniform (missing uniform items like shoes, pants, etc.)
                    if 'missing id' in details_lower:
                        violation_type = 'missing_id'
                    else:
                        # Default to incomplete_uniform for all other cases
                        # This includes: "Missing: black shoes, rtw pants" and similar
                        violation_type = 'incomplete_uniform'
                else:
                    # Fallback to other fields if details is not available
                    violation_details = violation.get('violation_details', violation.get('violation_type_display', ''))
                    violation_type = violation.get('violation_type', 'incomplete_uniform')
                
                # Get violation_count from parent document (already included in violation log from fetch)
                # Fallback to fetching it if not present
                violation_count = violation.get('violation_count')
                if violation_count is None:
                    # Fetch from parent document if not included
                    # Use student_number (not student_id/RFID) for student_violations access
                    violation_count = get_violation_count_from_parent(student_number, use_cache=True)
                    total_violation_reads += 1  # Count the read if we had to fetch it
                else:
                    violation_count = int(violation_count)  # Ensure it's an integer
                
                timestamp = violation.get('timestamp', violation.get('recorded_at', datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S Manila Time")))
                action_type = violation.get('action_type', 'check-in')
                
                # Determine recipient type (default to parents if parent info exists, otherwise student)
                recipient_type = "parents" if (parent_email or parent_phone) else "student"
                
                # Determine message type (message1 = initial violation, message2 = appeal result)
                message_type = violation.get('message_type', 'message1')  # Default to message1 for backward compatibility
                
                # For message2, we need two things:
                # 1. appeal_reason_type: from violation_history document to determine if approved ("Excused"/"Unexcused")
                # 2. display_reason_type: from last_violation_type in parent document for display ("incomplete_uniform" -> "Incomplete Uniform")
                if message_type == 'message2':
                    # Get appeal_reason_type from violation_history document (to determine if approved)
                    appeal_reason_type = violation.get('reason_type', '')
                    
                    # Get display_reason_type from last_violation_type in parent document (for display)
                    # Use student_number (not student_id/RFID) for student_violations access
                    display_reason_type = get_last_violation_type_from_parent(student_number, use_cache=True)
                    if not display_reason_type:
                        print(f"   ⚠️  Warning: last_violation_type is empty in parent document for student {student_number}")
                    
                    # Use appeal_reason_type for approval logic, but display_reason_type for the "Reason Type" field
                    # If appeal_reason_type exists, use it; otherwise fall back to display_reason_type
                    reason_type = appeal_reason_type if appeal_reason_type else display_reason_type
                    
                    # Store display_reason_type separately for formatting in email/SMS
                    violation['display_reason_type'] = display_reason_type
                else:
                    reason_type = ''  # Not needed for message1
                    violation['display_reason_type'] = ''
                
                print(f"   Student: {student_name} ({student_grade})")
                print(f"   Message Type: {message_type}")
                
                if message_type == 'message1':
                    print(f"   Violation Details: {violation_details}")
                    print(f"   Violation Type: {violation_type}")
                    print(f"   Violation Count: {violation_count}")
                elif message_type == 'message2':
                    print(f"   Appeal Result: {reason_type}")
                    print(f"   Violation Count: {violation_count} (remains unchanged per school policy)")
                
                # Note: Activities are now processed independently in Step 4, not included in violation notifications
                
                # Check available contact information
                has_parent_email = bool(parent_email and parent_email.strip())
                has_parent_phone = bool(parent_phone and parent_phone.strip())
                has_student_email = bool(student_email and student_email.strip())
                has_student_phone = bool(student_phone and student_phone.strip())
                
                # Collect error reasons
                error_reasons = []
                
                # Send notifications
                email_success = False
                sms_success = False
                parent_email_success = False
                student_email_success = False
                parent_sms_success = False
                student_sms_success = False
                
                # Handle message1 (initial violation notification) or message2 (appeal result notification)
                if message_type == 'message1':
                    # MESSAGE1: Initial violation notification
                    if recipient_type == "parents":
                        # Send to both parents and student
                        if has_parent_email:
                            print(f"   📧 Sending PARENT EMAIL to {parent_email}...")
                            parent_email_success = send_email(parent_email, student_name, student_grade, timestamp, action_type, "parents", violation_type, violation_details, violation_count, None, missing_items)
                            if parent_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Parent email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Parent email not found in student record")
                        
                        if has_student_email:
                            print(f"   📧 Sending STUDENT EMAIL to {student_email}...")
                            student_email_success = send_email(student_email, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, violation_count, None, missing_items)
                            if student_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Student email not found in student record")
                        
                        if has_parent_phone:
                            print(f"   📱 Sending PARENT SMS to {parent_phone}...")
                            parent_sms_success = send_sms(parent_phone, student_name, student_grade, timestamp, action_type, "parents", violation_type, violation_details, violation_count, None, missing_items)
                            if parent_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Parent SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Parent phone number not found in student record")
                        
                        if has_student_phone:
                            print(f"   📱 Sending STUDENT SMS to {student_phone}...")
                            student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, violation_count, None, missing_items)
                            if student_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Student phone number not found in student record")
                    else:
                        # Send to student only
                        if has_student_email:
                            print(f"   📧 Sending STUDENT EMAIL to {student_email}...")
                            student_email_success = send_email(student_email, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, violation_count, None, missing_items)
                            if student_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Student email not found in student record")
                        
                        if has_student_phone:
                            print(f"   📱 Sending STUDENT SMS to {student_phone}...")
                            student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, action_type, "student", violation_type, violation_details, violation_count, None, missing_items)
                            if student_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Student phone number not found in student record")
                elif message_type == 'message2':
                    # MESSAGE2: Appeal result notification
                    # reason_type should come from violation_history document (Excused/Unexcused)
                    # If not found, skip this violation
                    if not reason_type or reason_type.lower() not in ['excused', 'unexcused']:
                        print(f"   ⚠️  Skipping: reason_type from violation_history is missing or invalid ({reason_type})")
                        continue
                    
                    # Get display_reason_type for the "Reason Type" field display
                    display_reason_type = violation.get('display_reason_type', '')
                    
                    if recipient_type == "parents":
                        # Send to both parents and student
                        if has_parent_email:
                            print(f"   📧 Sending PARENT APPEAL RESULT EMAIL to {parent_email}...")
                            parent_email_success = send_appeal_result_email(parent_email, student_name, student_grade, timestamp, reason_type, "parents", violation_count, display_reason_type)
                            if parent_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Parent email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Parent email not found in student record")
                        
                        if has_student_email:
                            print(f"   📧 Sending STUDENT APPEAL RESULT EMAIL to {student_email}...")
                            student_email_success = send_appeal_result_email(student_email, student_name, student_grade, timestamp, reason_type, "student", violation_count, display_reason_type)
                            if student_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Student email not found in student record")
                        
                        if has_parent_phone:
                            print(f"   📱 Sending PARENT APPEAL RESULT SMS to {parent_phone}...")
                            parent_sms_success = send_appeal_result_sms(parent_phone, student_name, student_grade, timestamp, reason_type, "parents", violation_count, display_reason_type)
                            if parent_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Parent SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Parent phone number not found in student record")
                        
                        if has_student_phone:
                            print(f"   📱 Sending STUDENT APPEAL RESULT SMS to {student_phone}...")
                            student_sms_success = send_appeal_result_sms(student_phone, student_name, student_grade, timestamp, reason_type, "student", violation_count, display_reason_type)
                            if student_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Student phone number not found in student record")
                    else:
                        # Send to student only
                        if has_student_email:
                            print(f"   📧 Sending STUDENT APPEAL RESULT EMAIL to {student_email}...")
                            student_email_success = send_appeal_result_email(student_email, student_name, student_grade, timestamp, reason_type, "student", violation_count, display_reason_type)
                            if student_email_success:
                                email_success = True
                            else:
                                error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                        else:
                            error_reasons.append("Student email not found in student record")
                        
                        if has_student_phone:
                            print(f"   📱 Sending STUDENT APPEAL RESULT SMS to {student_phone}...")
                            student_sms_success = send_appeal_result_sms(student_phone, student_name, student_grade, timestamp, reason_type, "student", violation_count, display_reason_type)
                            if student_sms_success:
                                sms_success = True
                            else:
                                error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                        else:
                            error_reasons.append("Student phone number not found in student record")
                
                # Print summary of notification attempts
                print(f"\n   📊 Notification Summary:")
                if recipient_type == "parents":
                    if has_parent_email:
                        status = "✅ Sent" if parent_email_success else "❌ Failed"
                        print(f"      Parent Email: {status}")
                    if has_student_email:
                        status = "✅ Sent" if student_email_success else "❌ Failed"
                        print(f"      Student Email: {status}")
                    if has_parent_phone:
                        status = "✅ Sent" if parent_sms_success else "❌ Failed"
                        print(f"      Parent SMS: {status}")
                    if has_student_phone:
                        status = "✅ Sent" if student_sms_success else "❌ Failed"
                        print(f"      Student SMS: {status}")
                else:
                    if has_student_email:
                        status = "✅ Sent" if student_email_success else "❌ Failed"
                        print(f"      Student Email: {status}")
                    if has_student_phone:
                        status = "✅ Sent" if student_sms_success else "❌ Failed"
                        print(f"      Student SMS: {status}")
                
                # Update message status to "true" if at least one notification was sent successfully
                if email_success or sms_success:
                    print(f"\n   ✅ At least one notification sent successfully. Updating {message_type} status to 'true'...")
                    # Update the correct message field (message1 or message2) in violation_history subcollection
                    update_success = update_message_status(student_id, log_id, message_field=message_type, status="true")
                    if update_success:
                        print(f"   ✅ {message_type} status updated successfully in violation_history/{log_id}")
                    else:
                        print(f"   ⚠️  Failed to update {message_type} status")
                else:
                    print(f"\n   ❌ All notifications failed. {message_type} status will remain 'false'")
                    print(f"   📋 Detailed failure reasons:")
                    for i, reason in enumerate(error_reasons, 1):
                        print(f"      {i}. {reason}")
            
            # Summary of violations processing
            print(f"\n   ✅ Violations processing complete!")
            print(f"   📊 Violation reads this cycle: {violation_reads_this_cycle}")
        
        # STEP 4: Process ALL activities with message=false (independent of violations)
        print(f"\n   📋 Step 4: Processing ALL activities with message=false...")
        undelivered_activities = fetch_all_undelivered_activities()
        activity_reads_this_cycle = len(undelivered_activities)
        total_violation_reads += activity_reads_this_cycle
        
        if not undelivered_activities:
            print(f"   ✓ No undelivered activities found.")
            print(f"   📊 Activity reads this cycle: {activity_reads_this_cycle}")
        else:
            print(f"   📋 Found {len(undelivered_activities)} undelivered activity/activities")
            print(f"   📊 Activity reads this cycle: {activity_reads_this_cycle}")
            
            # Process each undelivered activity
            for activity in undelivered_activities:
                activity_id = activity.get('activity_id')
                if not activity_id:
                    print(f"   ⚠️  Skipping activity: No activity_id found")
                    continue
                
                # Extract student ID from activity (try different field names)
                student_id = activity.get('student_id') or activity.get('Student ID') or activity.get('student_number') or activity.get('Student Number')
                
                if not student_id:
                    print(f"   ⚠️  Skipping activity {activity_id}: No student_id found")
                    continue
                
                print(f"\n   Processing activity {activity_id} for student_id: {student_id}")
                
                # Get student information from students collection (uses cache to avoid re-reading)
                cache_misses_before = get_cache_stats()['cache_misses']
                student_info = get_student_by_id(student_id, use_cache=True)
                cache_misses_after = get_cache_stats()['cache_misses']
                
                # Only count as a read if there was a cache miss
                if cache_misses_after > cache_misses_before:
                    total_student_reads += 1  # 1 read only on cache miss
                    print(f"   📖 Student data read from Firebase (cache miss)")
                else:
                    print(f"   💾 Student data retrieved from cache (no read)")
                
                if not student_info:
                    # Try to find student by RFID number if available (RFID numbers are valid student identifiers)
                    rfid = activity.get('rfid') or activity.get('RFID')
                    if rfid:
                        print(f"   ℹ️  Student with ID {student_id} not found. Trying RFID number {rfid}...")
                        cache_misses_before_rfid = get_cache_stats()['cache_misses']
                        student_info = get_student_by_id(rfid, use_cache=True)
                        cache_misses_after_rfid = get_cache_stats()['cache_misses']
                        if cache_misses_after_rfid > cache_misses_before_rfid:
                            total_student_reads += 1
                            print(f"   📖 Student data read from Firebase using RFID (cache miss)")
                        if student_info:
                            print(f"   ✅ Found student using RFID number {rfid}")
                            # Don't update student_id to RFID - keep original for reference
                        else:
                            print(f"   ❌ Student not found using RFID {rfid} either. Skipping...")
                            continue
                    else:
                        print(f"   ❌ Student with ID {student_id} not found in students collection. Skipping...")
                        continue
                
                # Extract student information
                student_name = student_info.get('Name', student_info.get('name', activity.get('student_name', 'N/A')))
                student_grade = student_info.get('Course', student_info.get('course', student_info.get('grade', student_info.get('grade_level', activity.get('grade', 'N/A')))))
                student_email = student_info.get('Gmail', student_info.get('gmail', student_info.get('email', student_info.get('student_email', ''))))
                student_phone = student_info.get('Contact Number', student_info.get('contact_number', student_info.get('phone', student_info.get('student_phone', student_info.get('mobile', '')))))
                
                # Extract parent information
                parent_email = student_info.get('Parent Gmail', student_info.get('parent_email', student_info.get('Parent Email', student_info.get('parent_email_address', ''))))
                parent_phone = student_info.get('Parent Number', student_info.get('parent_phone', student_info.get('Parent Phone', student_info.get('parent_contact_number', student_info.get('parent_mobile', '')))))
                
                # Extract activity information
                # Check multiple possible field names: activity_type, action_type, type
                activity_type = activity.get('activity_type') or activity.get('action_type') or activity.get('type') or 'check-in'
                
                # Normalize activity_type: map "time_out" to "check-out" and "time_in" to "check-in"
                activity_type_lower = activity_type.lower() if activity_type else ''
                if activity_type_lower in ['time_out', 'time-out', 'timeout']:
                    activity_type = 'check-out'
                elif activity_type_lower in ['time_in', 'time-in', 'timein']:
                    activity_type = 'check-in'
                
                timestamp = activity.get('timestamp', activity.get('recorded_at', activity.get('time', datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S Manila Time"))))
                
                # Determine recipient type (default to parents if parent info exists, otherwise student)
                recipient_type = "parents" if (parent_email or parent_phone) else "student"
                
                print(f"   Student: {student_name} ({student_grade})")
                print(f"   Activity Type: {activity_type}")
                print(f"   Timestamp: {timestamp}")
                
                # Check available contact information
                has_parent_email = bool(parent_email and parent_email.strip())
                has_parent_phone = bool(parent_phone and parent_phone.strip())
                has_student_email = bool(student_email and student_email.strip())
                has_student_phone = bool(student_phone and student_phone.strip())
                
                # Collect error reasons
                error_reasons = []
                
                # Send notifications
                email_success = False
                sms_success = False
                parent_email_success = False
                student_email_success = False
                parent_sms_success = False
                student_sms_success = False
                
                # Send activity notifications based on activity type
                if recipient_type == "parents":
                    # Send to both parents and student
                    if has_parent_email:
                        print(f"   📧 Sending PARENT EMAIL to {parent_email}...")
                        parent_email_success = send_email(parent_email, student_name, student_grade, timestamp, activity_type, "parents", None, None, None, None, None)
                        if parent_email_success:
                            email_success = True
                        else:
                            error_reasons.append("Parent email sending failed (check SMTP configuration or email address)")
                    else:
                        error_reasons.append("Parent email not found in student record")
                    
                    if has_student_email:
                        print(f"   📧 Sending STUDENT EMAIL to {student_email}...")
                        student_email_success = send_email(student_email, student_name, student_grade, timestamp, activity_type, "student", None, None, None, None, None)
                        if student_email_success:
                            email_success = True
                        else:
                            error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                    else:
                        error_reasons.append("Student email not found in student record")
                    
                    if has_parent_phone:
                        print(f"   📱 Sending PARENT SMS to {parent_phone}...")
                        parent_sms_success = send_sms(parent_phone, student_name, student_grade, timestamp, activity_type, "parents", None, None, None, None, None)
                        if parent_sms_success:
                            sms_success = True
                        else:
                            error_reasons.append("Parent SMS sending failed (check PhilSMS API configuration or phone number)")
                    else:
                        error_reasons.append("Parent phone number not found in student record")
                    
                    if has_student_phone:
                        print(f"   📱 Sending STUDENT SMS to {student_phone}...")
                        student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, activity_type, "student", None, None, None, None, None)
                        if student_sms_success:
                            sms_success = True
                        else:
                            error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                    else:
                        error_reasons.append("Student phone number not found in student record")
                else:
                    # Send to student only
                    if has_student_email:
                        print(f"   📧 Sending STUDENT EMAIL to {student_email}...")
                        student_email_success = send_email(student_email, student_name, student_grade, timestamp, activity_type, "student", None, None, None, None, None)
                        if student_email_success:
                            email_success = True
                        else:
                            error_reasons.append("Student email sending failed (check SMTP configuration or email address)")
                    else:
                        error_reasons.append("Student email not found in student record")
                    
                    if has_student_phone:
                        print(f"   📱 Sending STUDENT SMS to {student_phone}...")
                        student_sms_success = send_sms(student_phone, student_name, student_grade, timestamp, activity_type, "student", None, None, None, None, None)
                        if student_sms_success:
                            sms_success = True
                        else:
                            error_reasons.append("Student SMS sending failed (check PhilSMS API configuration or phone number)")
                    else:
                        error_reasons.append("Student phone number not found in student record")
                
                # Print summary of notification attempts
                print(f"\n   📊 Notification Summary:")
                if recipient_type == "parents":
                    if has_parent_email:
                        status = "✅ Sent" if parent_email_success else "❌ Failed"
                        print(f"      Parent Email: {status}")
                    if has_student_email:
                        status = "✅ Sent" if student_email_success else "❌ Failed"
                        print(f"      Student Email: {status}")
                    if has_parent_phone:
                        status = "✅ Sent" if parent_sms_success else "❌ Failed"
                        print(f"      Parent SMS: {status}")
                    if has_student_phone:
                        status = "✅ Sent" if student_sms_success else "❌ Failed"
                        print(f"      Student SMS: {status}")
                else:
                    if has_student_email:
                        status = "✅ Sent" if student_email_success else "❌ Failed"
                        print(f"      Student Email: {status}")
                    if has_student_phone:
                        status = "✅ Sent" if student_sms_success else "❌ Failed"
                        print(f"      Student SMS: {status}")
                
                # Update message status to "true" if at least one notification was sent successfully
                if email_success or sms_success:
                    print(f"\n   ✅ At least one notification sent successfully. Updating message status to 'true'...")
                    update_success = update_activity_message_status(activity_id, status="true")
                    if update_success:
                        print(f"   ✅ Message status updated successfully in student_activities/{activity_id}")
                    else:
                        print(f"   ⚠️  Failed to update message status")
                else:
                    print(f"\n   ❌ All notifications failed. Message status will remain 'false'")
                    print(f"   📋 Detailed failure reasons:")
                    for i, reason in enumerate(error_reasons, 1):
                        print(f"      {i}. {reason}")
            
            # Summary of activities processing
            print(f"\n   ✅ Activities processing complete!")
            print(f"   📊 Activity reads this cycle: {activity_reads_this_cycle}")
        
        # Wait before next check (using configurable interval)
        if running:
            print(f"\n   ⏳ Waiting {POLLING_INTERVAL_SECONDS} seconds before next check...")
            time.sleep(POLLING_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user. Shutting down...")
        total_reads = total_violation_reads + total_student_reads
        cache_stats = get_cache_stats()
        print(f"📊 Total Firebase reads during this session: {total_reads:,}")
        print(f"   - Violation document reads: {total_violation_reads:,}")
        print(f"   - Student document reads: {total_student_reads:,}")
        print(f"\n💾 Student Cache Statistics:")
        print(f"   - Students cached: {cache_stats['cache_size']}")
        print(f"   - Cache hits: {cache_stats['cache_hits']} (saved {cache_stats['cache_hits']} reads!)")
        print(f"   - Cache misses: {cache_stats['cache_misses']}")
        print(f"   - Cache hit rate: {cache_stats['hit_rate']:.1f}%")
        print(f"   - Total reads saved by caching: {cache_stats['cache_hits']}")
        
        # Show Firebase usage estimate
        session_duration = (datetime.now(pytz.timezone('Asia/Manila')) - session_start_time).total_seconds()
        if session_duration >= 60:  # Only show if session ran for at least 1 minute
            print(get_firebase_usage_info())
        
        running = False
        break
    except Exception as e:
        print(f"\n   ❌ Error in main loop: {str(e)}")
        print(f"   ⏳ Waiting {POLLING_INTERVAL_SECONDS} seconds before retrying...")
        if running:
            time.sleep(POLLING_INTERVAL_SECONDS)

print("\n" + "=" * 70)
print("Service stopped. Goodbye!")
print("=" * 70)
