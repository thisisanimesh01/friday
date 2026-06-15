import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")
INDIAN_API_KEY = os.getenv("INDIAN_NEWS_API")

TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"

BLOCKED_SOURCES = [
    "menafn",
    "prnewswire",
    "gizmochina",
    "startupnews",
    "google",
    "gyanhigyan"
]


def extract_number(query):
    match = re.search(r'\b(\d+)\b', query)
    if match:
        return min(int(match.group(1)), 15)
    return 5


def clean_query(query):
    query = query.lower()
    query = re.sub(r'\b\d+\b', '', query)

    stopwords = [
        "give", "me", "news", "about", "on", "the",
        "latest", "headlines", "please", "show", "related"
    ]

    words = query.split()
    keywords = [w for w in words if w not in stopwords]

    return " ".join(keywords).strip()


#news function to fetch news based on the query given by the admin
def detect_category(query):
    if any(word in query for word in ["tech", "technology", "ai"]):
        return "technology"
    if "business" in query or "finance" in query:
        return "business"
    if "sports" in query:
        return "sports"
    if "health" in query:
        return "health"
    if "science" in query:
        return "science"
    if "entertainment" in query or "movie" in query:
        return "entertainment"
    return None

#func to fetch news from the Indian news API quickly
def fetch_indian_news_fast(params, num_articles):
    try:
        url = "https://newsdata.io/api/1/news"
        response = requests.get(url, params=params, timeout=4)
        data = response.json()

        articles = data.get("results", [])

        seen = set()
        news_list = []

        for article in articles:
            title = article.get("title", "")
            source = article.get("source_id", "").lower()

            if any(bad in source for bad in BLOCKED_SOURCES):
                continue

            if not title or title in seen:
                continue

            seen.add(title)
            news_list.append(f"{len(news_list)+1}. {title} ({source})")

            if len(news_list) >= num_articles:
                break

        return news_list

    except:
        return []

def fetch_newsapi(query, cleaned_query, category, num_articles, is_indian):
    params = {
        "apiKey": API_KEY,
        "pageSize": num_articles * 3,
        "sortBy": "publishedAt",
        "language": "en"
    }

    url = EVERYTHING_URL

    if is_indian:
        search_query = "india"
        if cleaned_query:
            search_query += " " + cleaned_query
        params["q"] = search_query

    elif category:
        params["q"] = category

    else:
        params["q"] = cleaned_query if cleaned_query else "latest"

    response = requests.get(url, params=params, timeout=6)
    data = response.json()

    if data.get("status") != "ok":
        print("DEBUG:", data)
        return []

    articles = data.get("articles", [])

    seen = set()
    news_list = []

    for article in articles:
        title = article.get("title", "")
        source = article.get("source", {}).get("name", "Unknown")

        if not title or title in seen:
            continue

        seen.add(title)
        news_list.append(f"{len(news_list)+1}. {title} ({source})")

        if len(news_list) >= num_articles:
            break

    return news_list


def get_news(query="latest"):
    try:
        query = query.lower().strip()

        num_articles = extract_number(query)
        cleaned_query = clean_query(query)
        category = detect_category(query)

        is_indian = "india" in query or "indian" in query

        if is_indian and INDIAN_API_KEY:
            params = {
                "apikey": INDIAN_API_KEY,
                "country": "in",
                "language": "en"
            }

            if category:
                params["category"] = category

            if cleaned_query:
                params["q"] = cleaned_query

            news = fetch_indian_news_fast(params, num_articles)

            if news:
                return "\n".join(news)

        news = fetch_newsapi(query, cleaned_query, category, num_articles, is_indian)

        if news:
            return "\n".join(news)

        return "Couldn't fetch news right now."

    except Exception as e:
        print("ERROR:", str(e))
        return "Something went wrong while fetching news."