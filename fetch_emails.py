import sqlite3
from helpers.gmail_helper import GmailHelper

def fetch_emails(service, folder):
    """Fetch emails from Gmail."""
    print("===== Fetching emails from gmail")
    results = service.users().messages().list(userId='me', labelIds=[folder]).execute()
    messages = results.get('messages', [])
    return messages

def save_emails(service, messages):
    """Saves emails to sqlite3 email database."""
    print("===== Saving emails to database")
    conn = sqlite3.connect('email_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (id TEXT PRIMARY KEY, from_email TEXT, to_email TEXT, subject TEXT, date_received TEXT)''')

    for msg in messages[:10]:  # Fetch and saves only the first 10 emails detailed info
        msg_id = msg['id']
        msg = service.users().messages().get(userId='me', id=msg_id).execute()

        headers = msg['payload']['headers']
        from_email = next(header['value'] for header in headers if header['name'] == 'From')
        to_email = next(header['value'] for header in headers if header['name'] == 'To')
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')
        date_received = next(header['value'] for header in headers if header['name'] == 'Date')
        
        c.execute('INSERT OR IGNORE INTO emails (id, from_email, to_email, subject, date_received) VALUES (?, ?, ?, ?, ?)',
                  (msg_id, from_email, to_email, subject, date_received))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("!!!!! SCRIPT STARTED - fetch_emails.py")
    gmail_helper_instance = GmailHelper()
    service = gmail_helper_instance.authenticate_gmail()
    messages = fetch_emails(service, 'INBOX')
    save_emails(service, messages)
    print("!!!!! SCRIPT COMPLETED - fetch_emails.py")


