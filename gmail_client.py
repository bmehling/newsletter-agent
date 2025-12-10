# Fix for Python 3.9 compatibility with Google libraries
import sys
try:
    import importlib.metadata as stdlib_metadata
    if not hasattr(stdlib_metadata, 'packages_distributions'):
        import importlib_metadata
        sys.modules['importlib.metadata'] = importlib_metadata
except ImportError:
    pass

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

class GmailClient:
    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def _get_credentials(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Valid token.json not found. Please run gmail_auth.py first.")
        return creds

    def search_newsletters(self):
        """
        Search for emails in 'Forums' category from yesterday/today 
        that haven't been processed yet.
        """
        # Query: category:forums -label:"Newsletter Processed" after:yesterday
        # Note: 'after:yesterday' in Gmail query means emails from yesterday and today.
        query = 'label:newsletter -label:"Agent/newsletter processed" newer_than:2d'
        
        results = self.service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        return messages

    def get_email_details(self, msg_id):
        """
        Fetches full email content and metadata.
        Returns a dict with subject, sender, body, date, etc.
        """
        msg = self.service.users().messages().get(userId="me", id=msg_id, format='full').execute()
        payload = msg['payload']
        headers = payload.get("headers", [])
        
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "")

        body = self._get_body(payload)
        
        return {
            "id": msg_id,
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body
        }

    def _get_body(self, payload):
        """
        Recursively extracts text body from email payload.
        Prefers plain text, falls back to HTML (cleaned).
        """
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode()
                elif part['mimeType'] == 'text/html':
                    # If we haven't found plain text yet, or if we want to append?
                    # Usually plain text is preferred for LLMs. 
                    # If plain text is empty, try HTML.
                    if not body:
                        data = part['body'].get('data')
                        if data:
                            html_content = base64.urlsafe_b64decode(data).decode()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            body = soup.get_text(separator='\n')
        else:
            # Single part email
            data = payload['body'].get('data')
            if data:
                decoded = base64.urlsafe_b64decode(data).decode()
                if payload['mimeType'] == 'text/html':
                    soup = BeautifulSoup(decoded, 'html.parser')
                    body = soup.get_text(separator='\n')
                else:
                    body = decoded
        
        return body

    def add_label(self, msg_id, label_name="Newsletter Processed"):
        """
        Adds a label to a message. Creates the label if it doesn't exist.
        """
        # 1. Check if label exists, get ID
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        label_id = None
        for label in labels:
            if label['name'] == label_name:
                label_id = label['id']
                break
        
        # 2. Create if not exists
        if not label_id:
            try:
                label_object = {'name': label_name}
                created_label = self.service.users().labels().create(userId="me", body=label_object).execute()
                label_id = created_label['id']
            except Exception as e:
                # If label exists (409), try to find it again (maybe case sensitivity issue or race condition)
                if "Label name exists" in str(e) or "409" in str(e):
                    results = self.service.users().labels().list(userId="me").execute()
                    labels = results.get("labels", [])
                    for label in labels:
                        if label['name'].lower() == label_name.lower(): 
                            label_id = label['id']
                            break
                
                if not label_id:
                    raise e
        
        # 3. Apply label
        body = {'addLabelIds': [label_id]}
        self.service.users().messages().modify(userId="me", id=msg_id, body=body).execute()
        print(f"Applied label '{label_name}' to message {msg_id}")

if __name__ == "__main__":
    # Test
    client = GmailClient()
    msgs = client.search_newsletters()
    print(f"Found {len(msgs)} potential newsletters.")
    if msgs:
        details = client.get_email_details(msgs[0]['id'])
        print(f"First subject: {details['subject']}")
        print(f"Body snippet: {details['body'][:200]}...")
