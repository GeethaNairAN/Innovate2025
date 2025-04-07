import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

def send_email(recipient_email, subject, message_content, attachments=None):
    """
    Send an email with the chat details to the specified recipient
    
    Args:
        recipient_email (str): The recipient's email address
        subject (str): Email subject line
        message_content (str): Email body content (can be HTML)
        attachments (list): Optional list of file paths to attach
    
    Returns:
        dict: Status of the email sending operation
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add message body as HTML
        msg.attach(MIMEText(message_content, 'html'))
        
        # Add attachments if any
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                    
                    # Add header as key/value pair to attachment
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
        
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": "Email sent successfully"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

def email_chat():
    data = request.json
    
    # Required fields
    recipient_email = data.get('email')
    conversation = data.get('conversation', [])
    subject = data.get('subject', 'Your Chat Conversation from ChexMate')
    
    # Optional fields
    user_name = data.get('name', 'User')
    file_paths = data.get('attachments', [])
    
    # Check for required fields
    if not recipient_email:
        return jsonify({"status": "error", "message": "Email address is required"}), 400
    
    if not conversation:
        return jsonify({"status": "error", "message": "No conversation to send"}), 400
    
    # Format the conversation into HTML
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .conversation {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .message {{ padding: 10px; margin-bottom: 15px; border-radius: 5px; }}
            .user {{ background-color: #e6f2ff; margin-left: 50px; }}
            .assistant {{ background-color: #f0f0f0; margin-right: 50px; }}
            .header {{ background-color: #0078d4; color: white; padding: 15px; text-align: center; }}
            .footer {{ font-size: 12px; color: #666; text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>ChexMate Chat Conversation</h2>
        </div>
        <div class="conversation">
            <p>Hello {user_name},</p>
            <p>Here is a transcript of your recent conversation with our chat assistant:</p>
            
            <div class="messages">
    """
    
    # Add each message from the conversation
    for message in conversation:
        if message.get('type') == 'user':
            html_content += f'<div class="message user"><strong>You:</strong> {message.get("text")}</div>'
        else:
            html_content += f'<div class="message assistant"><strong>Assistant:</strong> {message.get("text")}</div>'
    
    # Complete the HTML
    html_content += """
            </div>
        </div>
        <div class="footer">
            <p>Thank you for using ChexMate services. If you have any further questions, please contact us.</p>
            <p>&copy; 2025 ChexMate. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    # Send the email
    result = send_email('geetha.mair@fisglobal.com', subject, html_content, file_paths)
    
    # Return the result to client
    if result["status"] == "success":
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# Example Flask endpoint to send email with chat conversation

    
# # Example usage in your chat endpoint
# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.json
#     user_message = data.get('message', '')
    
#     # Process message and get response (your existing code)
#     # ...
    
#     # If the user requests to send the conversation by email
#     if "send email" in user_message.lower() or "email conversation" in user_message.lower():
#         # You can either:
#         # 1. Ask for their email address in the chat flow
#         response = "I'd be happy to email this conversation to you. Please provide your email address."
        
#         # Or 2. If you already have their email, send it directly
#         # This assumes you're keeping track of the conversation history
#         # conversation_history = [...] # Your conversation tracking logic
#         # email_result = send_email("user@example.com", "Your Chat Conversation", conversation_history)
#         # response = "I've sent the conversation to your email address."
    
#     return jsonify({"response": response})
