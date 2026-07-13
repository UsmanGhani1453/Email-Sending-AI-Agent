import os
import smtplib
import csv
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from dotenv import load_dotenv

load_dotenv()

def greeting(reciever_name):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = f"Write a short, warm, and professional Greeting email to {reciever_name}.Do not include a subject line or placeholder brackets in the text."
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print("Real error",e)
            print(f"Server busy (Attempt {attempt + 1} of 3). Waiting 5 seconds...")
            time.sleep(5)
            
    return "Hello! Just sending a quick message to say I hope you are having a great day."

def send_email(to_email, subject, body):
    sender_email = os.environ.get("SENDER_EMAIL", "")
    sender_password = os.environ.get("EMAIL_APP_PASSWORD", "")

    if not sender_email or not sender_password:
        raise ValueError("Missing email credentials")
        
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    with open('contacts.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row['Name']
            reciever = row['Email']

            print(f"\n--- Processing {name} ---")
            print(f"Thinking: Generating AI greeting for {name}...")

            ai_message = greeting(name)

            print("Sending Email.......")
            send_email(reciever, f"Good Morning, {name}!", ai_message)

            print("Waiting 5 seconds before the next email...")
            time.sleep(5)