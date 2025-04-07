from flask import Flask, render_template, request, jsonify, session
import os
import re
import uuid
from werkzeug.utils import secure_filename
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import Test

SMTP_SERVER = "smtp.gmail.com"  # Change to your SMTP server
SMTP_PORT = 587
SMTP_USERNAME = "gnairfis@gmail.com"  # Replace with your email
SMTP_PASSWORD = "SidParu@01"  # Replace with your password or app password

#retriever=vectordb.as_retriever(search_kwargs={"k":2})

app = Flask(__name__,static_folder='static',template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'ChexProdAgnt@01') 
UPLOAD_FOLDER='uploads'
ALLOWED_EXTENSIONS={'txt','pdf','doc','docx','csv','xlsx','ppt','pptx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Flow state management
FLOW_STATES = {
    'INITIAL': 0,
    'FREEZE_REQUESTED': 1,
    'SELF_OR_OTHER_ASKED': 2,
    'AGE_VERIFICATION_ASKED': 3,
    'PROTECTED_ASKED': 4,
    'PIN_REQUESTED': 5,
    'COMPLETED': 6,
    'BROKEN': -1
}

# Regular expressions for user responses
YES_PATTERN = re.compile(r'\b(yes|yep|yeah|sure|ok|okay|confirm|y)\b', re.IGNORECASE)
NO_PATTERN = re.compile(r'\b(no|nope|nah|n)\b', re.IGNORECASE)
SELF_PATTERN = re.compile(r'\b(self|me|myself|my|i)\b', re.IGNORECASE)
OTHER_PATTERN = re.compile(r'\b(other|someone|somebody|else|behalf|another)\b', re.IGNORECASE)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER,exist_ok=True)

documents={}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        print(recipient_email)

        # Add attachments if any
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                    
                    # Add header as key/value pair to attachment
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
        
        print(msg)
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        print('Logged in')

        # Send email
        server.send_message(msg)
        server.quit()
        
        return {"status": "success", "message": "Email sent successfully"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

    
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

@app.route('/')
def home():
    return render_template('test.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')
    user_id = request.json.get('user_id', 'default_user')

    # Use user_id as a key for session management
    session_key = f"flow_state_{user_id}"
    details_key = f"freeze_details_{user_id}"

    print(FLOW_STATES)
    # Initialize session state if it doesn't exist
    if session_key not in session:
        session[session_key] = FLOW_STATES['INITIAL']
        session[details_key] = {}

    current_state = session[session_key]
    freeze_details = session[details_key]

    # Check if the message contains freeze request trigger
    if 'want to place a freeze' in user_message.lower() and current_state == FLOW_STATES['INITIAL']:
        # Transition to freeze requested state
           session[session_key] = FLOW_STATES['FREEZE_REQUESTED']
           return jsonify({
               "response": "Would you like to place a security freeze on your account? Please respond with Yes or No.",
               "flow_active": True
            })
        
    if 'please place a freeze' in user_message.lower() and current_state == FLOW_STATES['INITIAL']:
        # Transition to freeze requested state
        session[session_key] = FLOW_STATES['FREEZE_REQUESTED']
        return jsonify({
            "response": "Would you like to place a security freeze on your account? Please respond with Yes or No.",
            "flow_active": True
        })
    # Handle the flow based on current state
    if current_state == FLOW_STATES['FREEZE_REQUESTED']:
        if YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['SELF_OR_OTHER_ASKED']
            return jsonify({
                "response": "Are you placing this security freeze request for yourself or on behalf of someone else? Please respond self or other.",
                "flow_active": True
            })
        elif NO_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "I understand you don't want to place a freeze. How else can I assist you today?",
                "flow_active": False
            })
        else:
            return jsonify({
                "response": "I didn't understand your response. Please respond with Yes or No if you want to place a freeze.",
                "flow_active": True
            })
    elif current_state == FLOW_STATES['SELF_OR_OTHER_ASKED']:
        if SELF_PATTERN.search(user_message):
            freeze_details['request_type'] = 'self'
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['AGE_VERIFICATION_ASKED']
            return jsonify({
                "response": "Are you 18 years of age or older? Please respond with Yes or No.",
                "flow_active": True
            })
        elif OTHER_PATTERN.search(user_message):
            freeze_details['request_type'] = 'other'
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['BROKEN']
            return jsonify({
                "response": "For freeze requests on behalf of someone else, please send a written mail with the details of your request.",
                "flow_active": False
            })
        else:
            return jsonify({
                "response": "I didn't understand your response. Are you placing this security freeze request for yourself or on behalf of someone else? Please respond self or other.",
                "flow_active": True
            })
    
    elif current_state == FLOW_STATES['AGE_VERIFICATION_ASKED']:
        if YES_PATTERN.search(user_message):
            freeze_details['age_verified'] = True
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['PROTECTED_ASKED']
            return jsonify({
                "response": "Are you a protected consumer? Please answer Yes or No",
                "flow_active": True
            })
        elif NO_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['BROKEN']
            return jsonify({
                "response": "I'm sorry, but you must be 18 years or older to place a freeze request online. Please have a parent or guardian send a mail with the relevant documents.",
                "flow_active": False
            })
        else:
            return jsonify({
                "response": "I didn't understand your response. Are you 18 years of age or older? Please respond with Yes or No.",
                "flow_active": True
            })
    
    elif current_state == FLOW_STATES['PROTECTED_ASKED']:
        if NO_PATTERN.search(user_message):
            freeze_details['protected_consumer'] = True
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['PIN_REQUESTED']
            return jsonify({
                "response": "Please provide your Consumer Pin Number. Please contact us if you have misplaced the pin number or need help with getting the pin number",
                "flow_active": True
            })
        elif YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['BROKEN']
            return jsonify({
                "response": "Protected consumer cannot place a freeze request online. Please send a mail with the relevant documents.",
                "flow_active": False
            })
        else:
            return jsonify({
                "response": "I didn't understand your response. Are you a protected consumer? Please answer Yes or No",
                "flow_active": True
            })
    
    elif current_state == FLOW_STATES['PIN_REQUESTED']:
        # Save the provided details
        freeze_details['provided_details'] = user_message
        session[details_key] = freeze_details
        session[session_key] = FLOW_STATES['COMPLETED']
        
        # Here you would typically process the freeze request
        # This could involve database updates, notifications, etc.
        
        return jsonify({
            "response": "Thank you for providing your details. Your freeze request has been submitted successfully. You will receive a confirmation email shortly. Is there anything else I can help you with?",
            "flow_active": False,
            "freeze_details": freeze_details  # You might want to process this on the backend
        })
    
    if current_state == FLOW_STATES['COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
        session[session_key] = FLOW_STATES['INITIAL']

    # For broken flow or if not in a flow state, process normally with Azure OpenAI
    if 'want to place a freeze' in user_message.lower() and current_state == FLOW_STATES['COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
        return jsonify({
            "response": "A freeze request has already been placed on your data. Is there anything else I can help you with?",
            "flow_active": False
        })

   # print(user_message)
    #vectors=Test.generate_embeddings(user_message_str)
    #retrieved_results=retriever.get_relevant_documents(user_message_str)
    #print(type(retrieved_results))
    import processquery
    gpt_resp=processquery.retrieve_resp(user_message)
    print(gpt_resp)
    # Simple echo response for demonstration
    response_message = f"CheMate: {gpt_resp}"
    return jsonify({'response': response_message, "flow_active": False})
    
# Route to clear/reset the freeze flow
@app.route('/reset_flow', methods=['POST'])
def reset_flow():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    
    session_key = f"flow_state_{user_id}"
    details_key = f"freeze_details_{user_id}"
    
    if session_key in session:
        session[session_key] = FLOW_STATES['INITIAL']
        session[details_key] = {}
    
    return jsonify({"status": "success", "message": "Flow state reset"})

@app.route('/upload', methods=['POST'])
def upload_files():
    session_id = request.cookies.get('session_id', str(uuid.uuid4()))

    if 'files' not in request.files:
        return jsonify({"error": "No files part"}),400
    
    files = request.files.getlist('files')
    upload_files=[]
    print(files)

    for file in files:
        if file.filename=='':
            continue

        if file and allowed_file(file.filename):
            filename=secure_filename(file.filename)
            file_path=os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
            file.save(file_path)
            print(filename)

            if session_id not in documents:
                documents[session_id] = []

            documents[session_id].append({
                "name": filename,
                "path": file_path,
                "type": filename.rsplit('.',1)[1].lower()
            })

            upload_files.append({"name": filename})
        else:
            return jsonify({"error": "Invalid File Format. Please upload as text, document or spreadsheet"})
        
    response = jsonify({"files": upload_files})
    print(response)
    print(upload_files)
    response.set_cookie('session_id', session_id)
    return response

@app.route('/send-email', methods=['POST'])
def email_chat():
    data = request.json
    import emailto
    # Required fields
    recipient_email = data.get('email')
    conversation = data.get('conversation', [])
    subject = data.get('subject', 'Your Chat Conversation from ChexMate')
    print(recipient_email)

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
    
    print(html_content)
    # Send the email
    result = send_email(recipient_email, subject, html_content, file_paths)
    
    # Return the result to client
    if result["status"] == "success":
        return jsonify(result), 200
    else:
        return jsonify(result), 500


if __name__ == '__main__':
    app.run(debug=True)
