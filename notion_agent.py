import os
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class NotionAgent:
    def __init__(self):
        self.notion = Client(auth=os.environ["NOTION_API_KEY"])
        self.articles_db_id = os.environ["NOTION_ARTICLES_DB_ID"]
        self.summary_db_id = os.environ["NOTION_SUMMARY_DB_ID"]

    def create_article_entry(self, article):
        """
        Creates a page in the Articles Database.
        """
        try:
            properties = {
                "Article Title": {"title": [{"text": {"content": article["title"]}}]},
                "Newsletter Name": {"rich_text": [{"text": {"content": article["newsletter_name"]}}]},
                "Newsletter Subject Line": {"rich_text": [{"text": {"content": article["newsletter_subject"]}}]},
                "Article Link": {"url": article["url"]},
                "Summary": {"rich_text": [{"text": {"content": article["summary"]}}]},
                "Category": {"select": {"name": article["category"].replace(",", "/") if article["category"] else "Uncategorized"}},
                "Must-Read": {"checkbox": article.get("must_read", False)},
                "Date Processed": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
                "Rank": {"number": article["rank"]}
            }
            
            # Key Takeaways as children blocks (bullet points)
            children = []
            children.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Key Takeaways"}}]}
            })
            
            for takeaway in article["takeaways"]:
                children.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": takeaway}}]}
                })

            response = self.notion.pages.create(
                parent={"database_id": self.articles_db_id},
                properties=properties,
                children=children
            )
            return response["id"] # Return ID to link in summary
        except Exception as e:
            print(f"Error creating article entry: {e}")
            return None

    def create_daily_summary(self, processed_newsletters):
        """
        Creates a daily summary page.
        processed_newsletters: List of dicts, each containing 'name', 'subject', 'articles' (list of article dicts)
        """
        today_str = datetime.now().strftime("%B %d, %Y")
        title = f"Newsletter Digest - {today_str}"
        
        total_articles = sum(len(n["articles"]) for n in processed_newsletters)
        
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Number of Newsletters": {"number": len(processed_newsletters)},
            "Number of Articles": {"number": total_articles}
        }

        children = []
        
        # Header (Removed as per request to avoid duplication with page title)
        # children.append({
        #     "object": "block",
        #     "type": "heading_1",
        #     "heading_1": {"rich_text": [{"text": {"content": title}}]}
        # })

        for newsletter in processed_newsletters:
            # Newsletter Section Header
            header_text = f"{newsletter['name']} - {newsletter['subject']}"
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": header_text}}]}
            })

            for article in newsletter['articles']:
                # Article Title Line: 💥 [Title](url) [link to DB]
                icon = "💥 " if article.get('must_read', False) else ""
                
                # Ensure URL is valid string
                article_url = article.get('url')
                if not article_url:
                    article_url = "https://example.com" # Fallback

                text_content = [
                    {"type": "text", "text": {"content": icon}},
                    {"type": "text", "text": {"content": article['title'], "link": {"url": article_url}}},
                    {"type": "text", "text": {"content": " "}},
                ]
                
                # Add link to Notion DB entry if we have the ID
                if article.get('notion_id'):
                    # Notion app link format or just a text indicator? 
                    # The prompt asks for "link to Articles DB entry". 
                    # We can't easily get the public URL of the new page immediately without an extra call, 
                    # but we can try to mention it or just link to the DB.
                    # For now, let's just add a text marker.
                    text_content.append({
                        "type": "text", 
                        "text": {"content": "[View in DB]", "link": {"url": f"https://notion.so/{article['notion_id'].replace('-', '')}"}}
                    })

                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": text_content}
                })

                # Summary
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": article['summary']}}]}
                })

                # Key Takeaways
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": "Key Takeaways:"}, "annotations": {"bold": True}}]}
                })
                
                for takeaway in article['takeaways']:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [{"text": {"content": takeaway}}]}
                    })
                
                # Spacer
                children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}})

            # Divider between newsletters
            children.append({"object": "block", "type": "divider", "divider": {}})

        # Chunking for 100 block limit
        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        chunks = list(chunk_list(children, 100))
        first_chunk = chunks[0] if chunks else []
        remaining_chunks = chunks[1:] if len(chunks) > 1 else []

        try:
            # Create page with first chunk
            response = self.notion.pages.create(
                parent={"database_id": self.summary_db_id},
                properties=properties,
                children=first_chunk
            )
            page_id = response["id"]
            print(f"Created Daily Summary page: {title}")

            # Append remaining chunks
            for i, chunk in enumerate(remaining_chunks):
                print(f"Appending chunk {i+1} of {len(remaining_chunks)}...")
                self.notion.blocks.children.append(
                    block_id=page_id,
                    children=chunk
                )
            
        except Exception as e:
            print(f"Error creating daily summary: {e}")

if __name__ == "__main__":
    # Test
    pass
