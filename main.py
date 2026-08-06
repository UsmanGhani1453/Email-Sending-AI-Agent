import csv
import os
import time
import random
import base64
from email.message import EmailMessage

from dotenv import load_dotenv
from google import genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_greeting(receiver_name):
    prompt = (
        f"Write a short, warm, and professional Greeting email to {receiver_name}. "
        "Do not include a subject line, conversational filler, or placeholder brackets."
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )
            return response.text.strip() # type: ignore
        except Exception as e:
            print(f"Server busy (Attempt {attempt + 1} of 3). Error: {e}")
            time.sleep(3)

    return "Hello! Just sending a quick message to say I hope you are having a great day."

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred initiating Gmail service: {error}")
        return None

def send_email(service, sender_email, to_email, subject, body):
    try:
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['From'] = sender_email
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"Email successfully sent to {to_email}. Message Id: {send_message['id']}")
    except HttpError as error:
        print(f"An error occurred sending email to {to_email}: {error}")

if __name__ == '__main__':
    sender_email = os.environ.get("SENDER_EMAIL") 
    
    if not sender_email:
        raise ValueError("Missing SENDER_EMAIL in .env file.")

    gmail_service = get_gmail_service()
    
    if not gmail_service:
        print("Failed to initialize Gmail API service.")
        exit(1)

    try:
        with open('contacts.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Name', 'Valued Contact')
                receiver_email = row.get('Email')
                
                if not receiver_email:
                    print(f"Skipping {name} due to missing email address.")
                    continue

                print(f"\n--- Processing {name} ---")
                print(f"Thinking: Generating AI greeting for {name}...")
                
                ai_message = generate_greeting(name)
                
                print("Sending Email.......")
                
                subjects = [
                    f"Good Morning, {name}!", 
                    f"Hello {name}, checking in!", 
                    f"A quick message for {name}"
                ]
                chosen_subject = random.choice(subjects)
                
                send_email(gmail_service, sender_email, receiver_email, chosen_subject, ai_message)
                
                delay = random.randint(5, 10)
                print(f"Waiting {delay} seconds before the next email ")
                time.sleep(delay)
                
    except FileNotFoundError:
        print("Error: contacts.csv not found.")