import streamlit as st
import requests
import xmltodict
from bs4 import BeautifulSoup
import newspaper
import google.generativeai as genai

# --- Gemini Setup (Requires API Key) ---
# Ensure you have a Google Cloud project and the Gemini API enabled
# Replace 'YOUR_GEMINI_API_KEY' with your actual API key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]  # Best practice: store API keys in streamlit secrets
genai.configure(api_key=GEMINI_API_KEY)

# **CHANGE THE MODEL NAME HERE:**
MODEL_NAME = 'models/gemini-1.5-flash-latest'

try:
    model = genai.GenerativeModel(MODEL_NAME)  # Use the correct model name
except Exception as e:
    st.error(f"Error initializing Gemini model: {e}")
    model = None

# --- CSS Styling ---
st.markdown(
    """
    <style>
    .rss-title {
        font-size: 2em;
        font-weight: bold;
        color: rgb(236, 223, 204);
        text-align: left;
    }
    .rss-description {
        font-size: 1.5em;
        color: rgb(167, 130, 149);
    }
    .rss-link {
        font-size: 1em;
        color: rgb(24, 255, 109) !important;
        text-decoration: none;
    }
    .center {
        display: flex;
        justify-content: right;
        align-items: center;
    }
    .feed-container {
        width: 90%;
    }

    .feed-divider {
        border-top: 2px solid #808080;
        margin-top: 20px;
        margin-bottom: 20px;
    }

   .stTextInput > label {
        visibility: hidden;
        position: absolute;
    }
    .input-container {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }

    .input-container > div:first-child {
        width: 70%;
        margin-right: 10px;
    }

    .input-container > div:last-child {
        width: 30%;
    }

    .stButton > button {
        height: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }

    .chat-message {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 16px;
    }
    .user-message {
        background-color: #DCF8C6; /* Light green for user messages */
        align-self: flex-end;
        text-align: right;
    }
    .bot-message {
        background-color: #ECE5DD; /* Light gray for bot messages */
        align-self: flex-start;
        text-align: left;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session State Initialization ---
if 'rss_urls' not in st.session_state:
    st.session_state['rss_urls'] = ['http://feeds.nytimes.com/nyt/rss/Technology']

if 'active_feed' not in st.session_state:
    st.session_state['active_feed'] = None

if 'search_term' not in st.session_state:
    st.session_state['search_term'] = ""

if 'article_data' not in st.session_state:
    st.session_state['article_data'] = {}

if 'selected_article' not in st.session_state:
    st.session_state['selected_article'] = None

if 'get_all_feeds' not in st.session_state:
    st.session_state['get_all_feeds'] = False

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --- RSS Feed Functions ---
def get_rss_feed(url: str) -> dict:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return xmltodict.parse(response.content)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching RSS feed from {url}: {e}")
        return None
    except Exception as e:
        st.error(f"Error parsing RSS feed from {url}: {e}")
        return None

def fetch_article_data(url: str) -> dict:
    """
    Fetches and extracts article data using the newspaper3k library.
    """
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()
        return {
            'title': article.title,
            'text': article.text,
            'authors': article.authors,
            'publish_date': article.publish_date,
            'top_image': article.top_image
        }
    except Exception as e:
        st.error(f"Error fetching article data from {url}: {e}")
        return {}

def display_rss_items(data: dict, search_term: str = "") -> None:
    try:
        if not data or 'rss' not in data or 'channel' not in data['rss'] or 'item' not in data['rss']['channel']:
            st.error("Invalid RSS feed format.")
            return

        items = data['rss']['channel']['item']

        for i, item in enumerate(items):  # Enumerate to make keys unique
            title = item.get('title', 'No Title Available')
            description = item.get('description', '')
            link = item.get('link', '#')

            if search_term and search_term.lower() not in title.lower() and search_term.lower() not in description.lower():
                continue

            image_url = None
            if 'enclosure' in item and isinstance(item['enclosure'], dict) and 'url' in item['enclosure']:
                image_url = item['enclosure']['url']
            elif 'media:content' in item and isinstance(item['media:content'], dict) and 'url' in item['media:content']:
                image_url = item['media:content']['url']
            else:
                soup = BeautifulSoup(description, 'html.parser')
                img_tag = soup.find('img')
                if img_tag:
                    image_url = img_tag['src']

            if len(description) >= 20:
                st.markdown(f"<div class='rss-title'>{title}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='rss-description'>{description}</div>", unsafe_allow_html=True)

                # Use a unique key for each button
                if st.button(f"Read more - {title}", key=f"read_more_{link}_{i}"):
                    st.session_state['selected_article'] = link
                    st.rerun()  # Force immediate rerun

                if image_url:
                    try:
                        st.image(image_url, caption=title, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying image from {image_url}: {e}")
                st.write("---")
    except Exception as e:
        st.error(f"Error displaying items: {e}")

def process_all_feeds(urls: list, search_term: str = ""):
    with st.container():
        st.markdown("<div class='feed-container'>", unsafe_allow_html=True)
        for i, url in enumerate(urls):
            rss_data = get_rss_feed(url)
            if rss_data:
                display_rss_items(rss_data, search_term)
            else:
                st.warning(f"Failed to retrieve or display feed from {url}")

            if i < len(urls) - 1:
                st.markdown("<div class='feed-divider'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- Sidebar Button Functions ---
def show_feed(url):
    st.session_state['active_feed'] = url

def add_url():
    st.session_state['rss_urls'].append("")

def remove_url():
    if len(st.session_state['rss_urls']) > 1:
        st.session_state['rss_urls'].pop()
    else:
        st.warning("Cannot remove the last URL. Please clear the URL instead.")

def perform_search():
    st.session_state['search_term'] = search_term

def get_all_feeds_callback():
     st.session_state['get_all_feeds'] = True

# --- Article Display Function ---
def display_article(article_url: str):
    article = None  # Initialize article

    if article_url in st.session_state['article_data']:
        article = st.session_state['article_data'][article_url]
    else:
        # Fetch article data only if it's not already in session state
        article = fetch_article_data(article_url)
        st.session_state['article_data'][article_url] = article

    if article:
        st.title(article['title'])
        if article['top_image']:
            st.image(article['top_image'], caption=article['title'], use_container_width=True)
        if article['authors']:
            st.write(f"**Authors:** {', '.join(article['authors'])}")
        if article['publish_date']:
            st.write(f"**Published:** {article['publish_date']}")
        st.write(article['text'])  # Display the article text

        if st.button("Back to Feed"):
            st.session_state['selected_article'] = None
            st.session_state['get_all_feeds'] = False  # add this line to reset get all feed button
            st.rerun()  # Force immediate rerun
    else:
        st.error("Failed to fetch article data.")

# --- Gemini Integration & Chatbot Functionality ---

def generate_gemini_response(prompt):
    """Generates a response from the Gemini Pro model."""
    if model is None: # Check if the model was initialized correctly
        st.error("Gemini model could not be initialized.  Check your API key and model name.")
        return "I'm sorry, the Gemini model is not available."
    try:
        #response = model.generate_content(prompt)
        #return response.text
        return "Bot Response"  # Simplified response for debugging
    except Exception as e:
        st.error(f"Error generating Gemini response: {e}")
        st.error(f"Exception Details: {e}")  # Print the exception object
        return "I'm sorry, I encountered an error processing your request."

def display_chat_history():
    """Displays the chat history in a styled format."""
    for i, message in enumerate(st.session_state['chat_history']):
        if i % 2 == 0:  # User message
            st.markdown(f'<div class="chat-message user-message">{message}</div>', unsafe_allow_html=True)
        else:  # Bot message
            st.markdown(f'<div class="chat-message bot-message">{message}</div>', unsafe_allow_html=True)


def chatbot_interface():
    """Implements the chatbot interface."""
    st.header("Gemini Chatbot")
    display_chat_history()

    # Use session state to manage user input and prevent infinite loops
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""  # Initialize if it doesn't exist

    user_input = st.text_input("Ask me anything:", key="user_input_text", value=st.session_state['user_input'])

    if user_input and user_input != st.session_state['user_input']:
        st.session_state['chat_history'].append(user_input)
        gemini_response = generate_gemini_response(user_input)
        st.session_state['chat_history'].append(gemini_response)
        st.session_state['user_input'] = ""
        st.rerun()

def article_summary_request(article_text):
    """
    Requests Gemini to summarize an article.
    """
    prompt = f"Please provide a concise summary of the following article:\n\n{article_text}\n\nSummary:"
    return generate_gemini_response(prompt)

def sentiment_analysis_request(article_text):
    """
    Requests Gemini to perform sentiment analysis on an article.
    """
    prompt = f"Analyze the sentiment of the following article and provide a brief explanation:\n\n{article_text}"
    return generate_gemini_response(prompt)

def extract_keywords_request(article_text):
    """
    Requests Gemini to extract keywords from an article.
    """
    prompt = f"Extract the 5 most important keywords from the following article:\n\n{article_text}\n\nKeywords:"
    return generate_gemini_response(prompt)


# --- Main Content - Title and Description ---
st.title("RSS Feed and Gemini Integration")

# --- Sidebar Content - RSS Feed Configuration ---
with st.sidebar:
    st.header("RSS Feed Configuration")
    for i, url in enumerate(st.session_state['rss_urls']):
        with st.container():
            st.markdown("<div class='input-container'>", unsafe_allow_html=True)
            col1, col2 = st.columns([5, 2], gap="small")

            with col1:
                st.session_state['rss_urls'][i] = st.text_input(f"RSS Feed URL {i+1}:", url, key=f"url_{i}", label_visibility="collapsed")
            with col2:
                if st.session_state['rss_urls'][i]:
                    st.button("Show Feed", on_click=show_feed, args=(st.session_state['rss_urls'][i],), key=f"show_button_{i}")
            st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.button("Add URL", on_click=add_url)

    with col2:
        st.button("Remove URL", on_click=remove_url)

    with col3:
        st.button("Get All Feeds", key="get_all_small", on_click=get_all_feeds_callback)

    with st.container():
        st.markdown("<div class='input-container'>", unsafe_allow_html=True)
        col1, col2 = st.columns([5, 2], gap="small")

        with col1:
            search_term = st.text_input("Search Feed:", value=st.session_state['search_term'], key="search_input", label_visibility="collapsed")

        with col2:
            st.button("Search", on_click=perform_search)
        st.markdown("</div>", unsafe_allow_html=True)

    st.header("Gemini Chatbot")
    if st.button("Open Chatbot"):
        st.session_state['show_chatbot'] = True

    if 'show_chatbot' in st.session_state and st.session_state['show_chatbot']:
        chatbot_interface()
        st.session_state['active_feed'] = None
        st.session_state['get_all_feeds'] = False
        st.session_state['selected_article'] = None

# --- Main Content Logic ---

# **Crucially, process all state changes *before* deciding what to display**

# **Now determine what to display based on the updated state**
if st.session_state.get('selected_article'):
    display_article(st.session_state['selected_article'])

    # Gemini Functionalities when Article is selected
    article = st.session_state['article_data'].get(st.session_state['selected_article'])
    if article:
        st.subheader("Gemini Analysis Tools")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Summarize Article"):
                with st.spinner("Generating summary..."):
                    summary = article_summary_request(article['text'])
                    st.write(summary)
        with col2:
            if st.button("Sentiment Analysis"):
                with st.spinner("Analyzing sentiment..."):
                    sentiment = sentiment_analysis_request(article['text'])
                    st.write(sentiment)
        with col3:
            if st.button("Extract Keywords"):
                with st.spinner("Extracting keywords..."):
                    keywords = extract_keywords_request(article['text'])
                    st.write(keywords)

elif st.session_state['active_feed']:
    st.header(f"Feed: {st.session_state['active_feed']}")
    display_rss_items(get_rss_feed(st.session_state['active_feed']), st.session_state['search_term'])
elif st.session_state['get_all_feeds']:
    valid_urls = [url.strip() for url in st.session_state['rss_urls'] if url.strip()]
    if valid_urls:
        process_all_feeds(valid_urls, st.session_state['search_term'])
    else:
        st.warning("Please enter at least one RSS Feed URL.")
else:
    st.markdown("Choose a feed from the sidebar or click 'Get All Feeds' to display content.")