from gmail_client import GmailClient

def reset_labels():
    client = GmailClient()
    
    # Query to find processed emails from the last 2 days
    # We look for label:newsletter and label:"Agent/newsletter processed"
    query = 'label:newsletter label:"Agent/newsletter processed" newer_than:2d'
    
    results = client.service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    
    print(f"Found {len(messages)} messages to reset.")
    
    # Get Label ID
    results = client.service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
    label_id = None
    target_label = "Agent/newsletter processed"
    for label in labels:
        if label['name'].lower() == target_label.lower():
            label_id = label['id']
            break
            
    if not label_id:
        print(f"Label '{target_label}' not found.")
        print("Available labels:")
        for label in labels:
            print(f"- {label['name']}")
        return

    for msg in messages:
        try:
            body = {'removeLabelIds': [label_id]}
            client.service.users().messages().modify(userId="me", id=msg['id'], body=body).execute()
            print(f"Removed label from {msg['id']}")
        except Exception as e:
            print(f"Error resetting {msg['id']}: {e}")

if __name__ == "__main__":
    reset_labels()
