# Fix for Python 3.9 compatibility with Google libraries
import sys
try:
    import importlib.metadata as stdlib_metadata
    if not hasattr(stdlib_metadata, 'packages_distributions'):
        import importlib_metadata
        sys.modules['importlib.metadata'] = importlib_metadata
except ImportError:
    pass

import time
from gmail_client import GmailClient
from notion_agent import NotionAgent
from llm_processor import LLMProcessor

def main():
    print("Starting Newsletter Digest Agent...")
    
    # 1. Initialize Components
    try:
        gmail = GmailClient()
        notion = NotionAgent()
        llm = LLMProcessor()
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 2. Find Newsletters
    print("Searching for newsletters...")
    messages = gmail.search_newsletters()
    
    if not messages:
        print("No new newsletters found.")
        return

    print(f"Found {len(messages)} newsletters to process.")
    
    processed_newsletters = []

    # 3. Process Each Newsletter
    for msg in messages:
        try:
            details = gmail.get_email_details(msg['id'])
            print(f"Processing: {details['subject']}...")
            
            # Determine Newsletter Name (Simple heuristic: Sender Name)
            # "Sender Name <email@example.com>" -> "Sender Name"
            sender_name = details['sender'].split('<')[0].strip().replace('"', '')
            
            # Extract Articles via LLM
            articles = llm.process_newsletter(details['subject'], details['body'], newsletter_name=sender_name)
            
            if not articles:
                print(f"  - No articles extracted from {details['subject']}. Skipping.")
                continue
                
            print(f"  - Extracted {len(articles)} articles.")
            
            # Create Notion Entries for Articles
            for article in articles:
                notion_id = notion.create_article_entry(article)
                article['notion_id'] = notion_id
                print(f"    - Created article: {article['title']}")
            
            # Add to list for Daily Summary
            processed_newsletters.append({
                "name": sender_name,
                "subject": details['subject'],
                "articles": articles
            })
            
            # Mark as Processed
            gmail.add_label(msg['id'], "Agent/newsletter processed")
            
        except Exception as e:
            print(f"Error processing message {msg['id']}: {e}")

    # 4. Create Daily Summary
    if processed_newsletters:
        print("Creating Daily Summary Page...")
        notion.create_daily_summary(processed_newsletters)
        print("Done!")
    else:
        print("No newsletters were successfully processed.")

if __name__ == "__main__":
    main()
