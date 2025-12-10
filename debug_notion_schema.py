import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

def inspect_db(db_id, name):
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    try:
        db = notion.databases.retrieve(database_id=db_id)
        print(f"--- Object for {name} ({db_id}) ---")
        print(f"Object Type: {db.get('object')}")
        print(f"Title: {db.get('title')}")
        properties = db.get("properties", {})
        print(f"Properties Count: {len(properties)}")
        if not properties:
            print("WARNING: No properties found. Full DB Object keys:", db.keys())
            # print(json.dumps(db, indent=2)) # Uncomment if needed
        
        for prop_name, prop_data in properties.items():
            print(f"Property: '{prop_name}' | Type: '{prop_data['type']}'")
    except Exception as e:
        print(f"Error retrieving {name}: {e}")

if __name__ == "__main__":
    articles_db_id = os.environ.get("NOTION_ARTICLES_DB_ID")
    summary_db_id = os.environ.get("NOTION_SUMMARY_DB_ID")
    
    inspect_db(articles_db_id, "Articles DB")
    inspect_db(summary_db_id, "Summary DB")
