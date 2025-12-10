# Newsletter Digest Agent

An AI-powered agent that monitors your Gmail for newsletters, extracts key insights using Google Gemini, and compiles them into a Notion database and Daily Summary page.

NOTE: This agent was built via AI. Design brainstorm and PRD via Claude Sonnet. Code, testing, and utilities via Gemini/Antigravity.

## Features
-   **Automated Search**: Scans Gmail for newsletters based on your filters.
-   **AI Extraction**: Uses Gemini Flash to extract summaries, key takeaways, and categories from emails.
-   **Notion Integration**: Creates individual article pages and a consolidated "Daily Summary" in Notion.
-   **Chunking Support**: Handles large summaries by splitting content into Notion-compatible blocks.
-   **Deduplication**: Tags emails as processed to prevent duplicate entries.

## Setup

1.  **Prerequisites**:
    -   Python 3.10+
    -   Google Cloud Project (Gmail API enabled)
    -   Google Gemini API Key
    -   Notion Integration Token

2.  **Environment Variables**:
    Create a `.env` file:
    ```bash
    GEMINI_API_KEY=your_key_here
    NOTION_API_KEY=your_key_here
    NOTION_ARTICLES_DB_ID=your_db_id
    NOTION_SUMMARY_DB_ID=your_db_id
    ```

3.  **Authentication**:
    -   Place `credentials.json` (Gmail OAuth) in the root.
    -   Run `python gmail_auth.py` to generate `token.json`.

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the agent manually:
```bash
python main.py
```

### Scheduling
Uses `launchd` on macOS for daily execution at 8:00 AM.
See `com.ben.newsletter_agent.plist`.

## Project Structure
-   `main.py`: Entry point and orchestration.
-   `gmail_client.py`: Handles Gmail API searching and label management.
-   `llm_processor.py`: Interacts with Gemini API for content extraction.
-   `notion_agent.py`: Manages Notion pages and databases.
