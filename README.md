# News RSS Feed and Gemini Integration

This project integrates RSS feed reading with Gemini AI for enhanced content analysis and chatbot functionality using Streamlit.

## Features

- Fetch and display RSS feeds.
- Search within RSS feeds.
- Display detailed articles.
- Summarize articles using Gemini AI.
- Perform sentiment analysis on articles using Gemini AI.
- Extract keywords from articles using Gemini AI.
- Chatbot interface powered by Gemini AI.

## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/rohithvinice/news.git
    cd news
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up Streamlit secrets:**
    - Create a file named `secrets.toml` in the `.streamlit` directory.
    - Add your Gemini API key:
    ```toml
    [secrets]
    GEMINI_API_KEY = "your_gemini_api_key_here"
    ```

## Running the Application

To run the Streamlit application, use the following command:
```bash
streamlit run NewsRss.py
```

## Usage

- **RSS Feed Configuration:**
  - Add, remove, or display RSS feed URLs from the sidebar.
  - Search within the feeds using the search bar.

- **Article Display:**
  - Click on "Read more" to view the full article.
  - Use Gemini tools to summarize, analyze sentiment, or extract keywords from the article.

- **Chatbot:**
  - Open the chatbot from the sidebar and interact with the Gemini-powered chatbot.

## Dependencies

- `streamlit`
- `requests`
- `xmltodict`
- `beautifulsoup4`
- `newspaper3k`
- `google-generativeai`

## License

This project is licensed under the MIT License.
