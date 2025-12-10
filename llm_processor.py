import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMProcessor:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash-lite as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def process_newsletter(self, email_subject, email_body, newsletter_name="Unknown"):
        """
        Analyzes newsletter content and extracts top 5 articles.
        Returns a list of article dictionaries.
        """
        prompt = f"""
        You are an expert newsletter curator. Your task is to analyze the following newsletter and extract the TOP 5 most valuable articles based on practical, actionable insights.

        Newsletter Name: {newsletter_name}
        Subject: {email_subject}

        CONTENT:
        {email_body[:30000]}  # Truncate to avoid context limits if extremely long, though 1.5 handles 1M tokens.

        INSTRUCTIONS:
        1. Identify the most important articles/sections.
        2. Select the top 5 (or fewer if there aren't 5 distinct topics).
        3. Rank them 1 to 5 (1 is best).
        4. The top 2 are "must_read": true.
        5. Extract the URL for each.
        6. Write a 3-6 sentence summary for each.
        7. Extract 3-5 actionable bullet points (takeaways).
        8. Assign a category (e.g., AI, Healthcare, Product, Engineering, Business).

        OUTPUT FORMAT:
        Return ONLY a valid JSON array of objects. Do not include markdown formatting like ```json.
        [
            {{
                "title": "Article Headline",
                "url": "https://...",
                "summary": "...",
                "takeaways": ["point 1", "point 2", ...],
                "category": "...",
                "must_read": true,
                "rank": 1
            }},
            ...
        ]
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            articles = json.loads(text)
            
            # Enrich with newsletter metadata
            for article in articles:
                article["newsletter_name"] = newsletter_name
                article["newsletter_subject"] = email_subject
            
            return articles

        except Exception as e:
            print(f"Error processing newsletter with LLM: {e}")
            return []

if __name__ == "__main__":
    # Test
    pass
