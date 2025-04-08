from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import re
import uuid
from werkzeug.utils import secure_filename
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import Chromatest
#from processquery import query_chromadb
from Chromatest import collection 
import random
    

SMTP_SERVER = "testmail.fisdev.local"  # Change to your SMTP server
SMTP_PORT = 25
SMTP_USERNAME = "dsreporting@fisdev.local"  # Replace with your email
SMTP_PASSWORD = "Welcome@8451(#sd"  # Replace with your password or app password

#retriever=vectordb.as_retriever(search_kwargs={"k":2})

app = Flask(__name__,static_folder='static',template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'ChexProdAgnt@02') 
UPLOAD_FOLDER='uploads'
ALLOWED_EXTENSIONS={'txt','pdf','doc','docx','csv','xlsx','ppt','pptx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Flow state management
FLOW_STATES = {
    'INITIAL': 0,
    'REMOVE_INITIAL': 1,
    'FREEZE_REQUESTED': 2,
    'REMOVAL_REQUESTED': 3,
    'SELF_OR_OTHER_ASKED': 4,
    'AGE_VERIFICATION_ASKED': 5,
    'PROTECTED_ASKED': 6,
    'PIN_REQUESTED': 7,
    'GOVTNBR_REQUESTED': 8, 
    'REMOVAL_PIN_REQUESTED': 9,
    'FREEZE_COMPLETED': 10,
    'REMOVE_COMPLETED': 11,
    'BROKEN': -1,
    'REMOVE_BROKEN': -2
}

# Regular expressions for user responses
YES_PATTERN = re.compile(r'\b(yes|yep|yeah|sure|ok|okay|confirm|y)\b', re.IGNORECASE)
NO_PATTERN = re.compile(r'\b(no|nope|nah|n)\b', re.IGNORECASE)
SELF_PATTERN = re.compile(r'\b(self|me|myself|my|i)\b', re.IGNORECASE)
OTHER_PATTERN = re.compile(r'\b(other|someone|somebody|else|behalf|another)\b', re.IGNORECASE)
QUERY_PATTERN = re.compile(r'\b(who|what|how|when|whose|which|where|whom)\b', re.IGNORECASE)
WELCOME_PATTERN = re.compile(r'\b(hi|hello)\b', re.IGNORECASE)
PLACE_PATTERN = re.compile(r'\b(place|add|placing|adding|raise|raising)\b', re.IGNORECASE)
END_PATTERN = re.compile(r'\b(thanks|thank you|thank|thankyou)\b', re.IGNORECASE)
QUESTION_PATTERN = r'?'
PIN_PATTERN = r'^[A-Za-z0-9]+$'

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
    reset_flow()
    return render_template('test.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')
    user_id = request.json.get('user_id', 'default_user')

    # Use user_id as a key for session management
    session_key = f"flow_state_{user_id}"
    details_key = f"freeze_details_{user_id}"
    
   # print(session[session_key])
    # Initialize session state if it doesn't exist
    if session_key not in session:
        session[session_key] = FLOW_STATES['INITIAL']
        session[details_key] = {}
    
    current_state = session[session_key]
    freeze_details = session[details_key]
    add_final_state = FLOW_STATES['INITIAL']
    remove_final_state = FLOW_STATES['INITIAL']

    # Check if the message contains freeze request trigger
    if WELCOME_PATTERN.search(user_message) and not QUERY_PATTERN.search(user_message) and current_state == FLOW_STATES['INITIAL']:
        # Transition to freeze requested state
           session[session_key] = FLOW_STATES['INITIAL']
           return jsonify({
               "response": " Welcome To ChexMate Services !!!"
               " How can I help you today? ",
               "flow_active": True
            })
    
    # Check if the message contains freeze request trigger
    # if END_PATTERN.search(user_message) and not QUERY_PATTERN.search(user_message) and current_state == FLOW_STATES['BROKEN']:
    #     # Transition to freeze requested state
    #        #session[session_key] = FLOW_STATES['SESSION_ENDED']
    #        return jsonify({
    #            "response": " Thank you for using the ChexMate Services !!!",
    #            "flow_active": False
    #         })

    # Check if the message contains freeze request trigger
    if PLACE_PATTERN.search(user_message) and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message) and current_state == FLOW_STATES['INITIAL'] and not add_final_state == FLOW_STATES['FREEZE_COMPLETED']:
        # Transition to freeze requested state
           session[session_key] = FLOW_STATES['FREEZE_REQUESTED']
           return jsonify({
               "response": "Would you like to place a security freeze on your data? Please confirm Yes or No.",
               "flow_active": True
            })

    if PLACE_PATTERN.search(user_message) and 'security' in user_message.lower() and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message) and current_state == FLOW_STATES['INITIAL'] and not add_final_state == FLOW_STATES['FREEZE_COMPLETED']:
        # Transition to freeze requested state
        session[session_key] = FLOW_STATES['FREEZE_REQUESTED']
        return jsonify({
            "response": "Would you like to place a security freeze on your data? Please confirm Yes or No.",
            "flow_active": True
        })
    
    if 'remove' in user_message.lower() and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message) and current_state == FLOW_STATES['INITIAL'] and not remove_final_state == FLOW_STATES['REMOVE_COMPLETED']:
       # Transition to freeze requested state
        session[session_key] = FLOW_STATES['REMOVAL_REQUESTED']
        return jsonify({
           "response": "Would you like to remove the security freeze on your data? Please confirm Yes or No.",
            "flow_active": True
        })

    # Handle the flow based on current state
    if current_state == FLOW_STATES['FREEZE_REQUESTED']:
        if YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['SELF_OR_OTHER_ASKED']
            return jsonify({
                "response": "Are you placing the security freeze request for yourself or on behalf of someone else? Please respond self or other.",
                "flow_active": True
            })
        elif NO_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "I understand you don't want to place a freeze. How else can I assist you today?",
                "flow_active": False
            })
        else:
            session[session_key] = FLOW_STATES['FREEZE_REQUESTED']
            return jsonify({
                "response": "I didn't understand your response. Please respond Yes to place a freeze.",
                "flow_active": True
            })
    elif current_state == FLOW_STATES['SELF_OR_OTHER_ASKED']:
        if SELF_PATTERN.search(user_message):
            freeze_details['request_type'] = 'self'
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['AGE_VERIFICATION_ASKED']
            return jsonify({
                "response": "Are you 18 years of age or older? Please respond Yes or No.",
                "flow_active": True
            })
        elif OTHER_PATTERN.search(user_message):
            freeze_details['request_type'] = 'other'
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "For freeze requests on behalf of someone else, please send a written mail with the details of your request.Is there anything else I can assist you with?",
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['SELF_OR_OTHER_ASKED']
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
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "I'm sorry, but you must be 18 years or older to place a freeze request online. Please have a parent or guardian send a mail with the required documents. Is there anything else I can help you with?",
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['AGE_VERIFICATION_ASKED']
            return jsonify({
                "response": "I didn't understand your response. Are you 18 years of age or older? Please respond Yes or No.",
                "flow_active": True
            })
    
    elif current_state == FLOW_STATES['PROTECTED_ASKED']:
        if NO_PATTERN.search(user_message):
            freeze_details['protected_asked'] = True
            session[details_key] = freeze_details
            print(freeze_details)
            session[session_key] = FLOW_STATES['PIN_REQUESTED']
            return jsonify({
                "response": "Please provide your Consumer Pin Number. Please contact us at 1800-555-1234 if you have misplaced the pin number or need help with getting the pin number",
                "flow_active": True
            })
        elif YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            add_final_state = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "Protected consumer cannot place a freeze request online. Please send a mail with the relevant documents. Is there anything else I can help you with?",
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['PROTECTED_ASKED']
            return jsonify({
                "response": "I didn't understand your response. Are you a protected consumer? Please answer Yes or No",
                "flow_active": True
            })

    if current_state == FLOW_STATES['REMOVAL_REQUESTED']:
        if YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['REMOVAL_PIN_REQUESTED']
            return jsonify({
                "response": "Please provide your Consumer Pin Number to remove the freeze.",
                "flow_active": True
            })
        elif NO_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "I understand you don't want to remove the freeze on your data. How else can I assist you today?",
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['REMOVAL_REQUESTED']
            return jsonify({
                "response": "I didn't understand your response. Please respond Yes to remove a freeze.",
                "flow_active": True
            })

    elif current_state == FLOW_STATES['PIN_REQUESTED']:
        if re.match(PIN_PATTERN, user_message):
            freeze_details['pin_requested'] = True
            session[details_key] = freeze_details
            print(freeze_details)
            session[session_key] = FLOW_STATES['GOVTNBR_REQUESTED']
            return jsonify({
                "response": "Please provide your Government Number.",
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['PIN_REQUESTED']
            return jsonify({
                "response": "Please provide a valid Consumer Pin Number. Please contact us at 1800-555-1234 if you need assistance to get the pin number.",
                "flow_active": True
            })

    elif current_state == FLOW_STATES['REMOVAL_PIN_REQUESTED']:
        if re.match(PIN_PATTERN, user_message):
            freeze_details['remove_pin_requested'] = True
            session[details_key] = freeze_details
            print(freeze_details)
            session[session_key] = FLOW_STATES['BROKEN']
            remove_final_state = FLOW_STATES['REMOVE_COMPLETED']
            random_number = random.randint(999999,99999999)
            response_message = f"Thank you for providing your details. Your freeze request has been removed successfully. Your Reference number is: {random_number}. You will receive a confirmation email shortly. Is there anything else I can help you with?"
            return jsonify({
                "response": response_message,
                "flow_active": True
            })
        else:
            session[session_key] = FLOW_STATES['REMOVAL_PIN_REQUESTED']
            return jsonify({
                "response": "Please provide a valid Consumer Pin Number. Please contact us at 1800-555-1234 if you need assistance to get the pin number.",
                "flow_active": True
            })
        
    elif current_state == FLOW_STATES['GOVTNBR_REQUESTED']:
        # Save the provided details
        if (user_message.isdigit()):
            freeze_details['provided_details'] = user_message
            session[details_key] = freeze_details
            session[session_key] = FLOW_STATES['BROKEN']
            add_final_state =  FLOW_STATES['FREEZE_COMPLETED']
        
        # Here you would typically process the freeze request
        # This could involve database updates, notifications, etc.
        # For this example, we'll just simulate a successful request
            random_number = random.randint(999999,99999999)
            response_message = f"Thank you for providing your details. Your freeze request has been initiated successfully. Your Reference number is: {random_number}. You will receive a confirmation email shortly. Is there anything else I can help you with?"
         
            return jsonify({
                "response": response_message,
                "flow_active": True,
                "freeze_details": freeze_details  # You might want to process this on the backend
            })
    
        else:
            session[session_key] = FLOW_STATES['GOVTNBR_REQUESTED']
            return jsonify({
                "response": "Please provide a valid Government Number.",
                "flow_active": True
            })
        

    if current_state == FLOW_STATES['BROKEN']:
        # Reset the flow state after broken flow message has been delivered
        print('session reset')

        if END_PATTERN.search(user_message) and not QUERY_PATTERN.search(user_message):
        # Transition to freeze requested state
           session[session_key] = FLOW_STATES['INITIAL']
           return jsonify({
               "response": " Thank you for using the ChexMate Services !!!",
               "flow_active": False
            })

        if 'remove' in user_message.lower() and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message) and remove_final_state == FLOW_STATES['REMOVE_COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
            session[session_key] = FLOW_STATES['BROKEN']
            return jsonify({
                "response": "Your freeze request has already been removed. Is there anything else I can help you with?",
                "flow_active": True
            })
        
        if PLACE_PATTERN.search(user_message) and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message) and add_final_state == FLOW_STATES['FREEZE_COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
            session[session_key] = FLOW_STATES['BROKEN']
            return jsonify({
                "response": "A freeze request has already been placed on your data. Is there anything else I can help you with?",
                "flow_active": True
            })

        #session[session_key] = FLOW_STATES['INITIAL']
        if YES_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": "How can I help you today?",
                "flow_active": True
            })
        elif NO_PATTERN.search(user_message):
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": " Thank you for using the ChexMate Services !!!",
                "flow_active": False
            })
        else:
            session[session_key] = FLOW_STATES['INITIAL']
            return jsonify({
                "response": " Welcome To ChexMate Services !!!"
               " How can I help you today?",
                "flow_active": True
            })

    # For broken flow or if not in a flow state, process normally with Azure OpenAI
    if PLACE_PATTERN.search(user_message) and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message)  and current_state == FLOW_STATES['FREEZE_COMPLETED'] and add_final_state == FLOW_STATES['FREEZE_COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
        session[session_key] = FLOW_STATES['INITIAL']
        add_final_state == FLOW_STATES['FREEZE_COMPLETED']
        return jsonify({
            "response": "A freeze request has already been placed on your data. Is there anything else I can help you with?",
            "flow_active": True
        })

# For broken flow or if not in a flow state, process normally with Azure OpenAI
    if 'remove' in user_message.lower() and 'freeze' in user_message.lower() and not QUERY_PATTERN.search(user_message)  and current_state == FLOW_STATES['REMOVE_COMPLETED'] and remove_final_state == FLOW_STATES['REMOVE_COMPLETED']:
        # Reset the flow state after broken flow message has been delivered
        session[session_key] = FLOW_STATES['INITIAL']
        remove_final_state == FLOW_STATES['REMOVE_COMPLETED']
        return jsonify({
            "response": "Your freeze request has already been removed. Is there anything else I can help you with?",
            "flow_active": True
        })

   # print(user_message)
    #vectors=Test.generate_embeddings(user_message_str)
    #retrieved_results=retriever.get_relevant_documents(user_message_str)
    #print(type(retrieved_results))
    #query_embedding = generate_embeddings([user_message]) 
    
    doc_resp=query_chromadb(collection,user_message)
    potential_responses = []
    documents=doc_resp.get('documents',[])
    for doc_list in documents:
        for doc in doc_list:
            #print(doc)
            potential_responses.append(doc)
    
    print(potential_responses)
    from processquery import retrieve_resp
    gpt_resp=retrieve_resp(user_message,potential_responses)
   # print(gpt_resp)

   # print(len(potential_responses))  # Simple echo response for demonstration
    response_message = f"ChexMate: {gpt_resp}"
    return jsonify({'response': response_message, "flow_active": False})
    
def query_chromadb(collection, query_text, n_results=3):
    # Generate embedding for the query text
    query_text = "What is a security freeze?"
    from Chromatest import generate_embeddings_str # Ensure this function is defined in Test.py
    query_embedding = generate_embeddings_str(query_text)  # Ensure this returns a list of embeddings
      # Perform the query
    print(query_text)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"]  # Include documents, metadata, and distances in the result
    )
    print(results)
    return results

# Route to clear/reset the freeze flow
#@app.route('/reset_flow', methods=['POST'])
def reset_flow():
    user_id = 'default_user'
    
    session_key = f"flow_state_{user_id}"
    details_key = f"freeze_details_{user_id}"
    print(session_key)
    print(session)

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

        print(allowed_file(file.filename))

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
            #response = jsonify({"files": upload_files})
            response = jsonify("success")
        else:
            print("error in file format")
            #response = jsonify({"error": "Invalid File Format. Please upload as text, document or spreadsheet"})
            response = jsonify("faile")
            
    print(response)
    print(upload_files)
    response.set_cookie('session_id', session_id)
    return response

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

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
