import os
import openai
import requests
import json

gpt_endpoint = "https://innovate-openai-api-mgt.azure-api.net/innovate-tracked/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-01"
gpt_api_key = "5525afe32ec74890a64807db7d7e871a"    

gpt_headers = {
    "Content-Type": "application/json",
    "cache_control": "no-cache",
    "api-key": gpt_api_key
}

def retrieve_resp(user_message):

    user_question = user_message
    print(user_question)
    potential_responses = [
    "To place a security freeze on behalf of a Protected Consumer, you must submit the request in writing by mail and provide sufficient proof of identity and sufficient proof of authority. If you have any questions, please contact the ChexSystems Security Freeze Department.",
    """You must be 18 years of age or older to communicate with ChexSystems. To place a security freeze on behalf of a minor, a parent or legal guardian must send the request in writing to ChexMate by mail. All of the following documentation must be included:
    A copy of the minor's birth certificate;
    A legible copy of the minor's Social Security card;
    A legible copy of the parent or legal guardian's driver's license or state identification card;
    Proof of address for the parent or legal guardian (in the form of a pay stub, utility bill or other official document bearing the address to which correspondence is to be sent);
    If your name does not appear on the birth certificate, a copy of a document confirming legal guardianship is required. The proof of guardianship must be an official court or other legally binding document; and
    Correspondence must include consumer’s full name, current address, date of birth, and Social Security number.""",
    "To place a security freeze on behalf of someone who is not a minor, you must send the request in writing to ChexSystems by mail. You must also include the following documentation authorizing ChexSystems to communicate and provide information to you:"
     ]

    #print(potential_responses[3])

    messages = [
        {"role": "system", "content": "You are a helpful assistant that evaluates response options and selects the most appropriate one. Return ONLY the best response with no additional text."},
        {"role": "system", "content": "If the request is to place a security freeze, ask Are you a protected consumer"},
        {"role": "system", "content": "If none of the responses match the request, please respond with, Sorry, I am unable to find an appropriate answer for the request at this time. Please contact the admin for more details and assistance."},
        {"role": "user", "content": f"Select the best response to this customer question: '{user_question}'\n\nPotential responses:\n1. {potential_responses[0]}\n2. {potential_responses[1]}\n3. {potential_responses[2]}\n\nProvide only the text of the best response, with no explanation or additional commentary."}
        ]

    gpt_data = {
        "model": "gpt-4o-mini",
        "messages": messages
        }

    response=requests.post(gpt_endpoint, headers=gpt_headers, data=json.dumps(gpt_data),verify=False)   
    if response.status_code == 200:
       result = response.json()
       gpt_resp=result['choices'][0]['message']['content']
       return(gpt_resp)
#    print("Response:", result['data'][0]['embedding'])
    #else:
    #   print("failed")
    #   print(f"Error: {response.status_code}, {response.text}")
