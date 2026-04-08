import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/top-headlines"


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


def get_news(query="latest"):
    try:
        query = query.lower().strip()

        num_articles = extract_number(query)
        cleaned_query = clean_query(query)
        category = detect_category(query)

        country = None
        if "india" in query:
            country = "in"
        elif "us" in query or "america" in query:
            country = "us"

        params = {
            "apiKey": API_KEY,
            "pageSize": max(num_articles * 3, 15)
        }

        if country:
            params["country"] = country
        else:
            params["language"] = "en"

        if category:
            params["category"] = category
        elif cleaned_query:
            params["q"] = cleaned_query

        response = requests.get(BASE_URL, params=params, timeout=5)
        data = response.json()

        if data.get("status") != "ok":
            print("DEBUG:", data)
            return "Couldn't fetch news right now."

        articles = data.get("articles", [])

        if not articles and cleaned_query:
            words = cleaned_query.split()

            for word in words:
                params.pop("category", None)
                params["q"] = word

                response = requests.get(BASE_URL, params=params, timeout=5)
                data = response.json()
                articles = data.get("articles", [])

                if articles:
                    break

        if not articles:
            return "No news found."

        seen = set()
        news_list = []

        for article in articles:
            title = article.get("title", "")

            if not title or title in seen:
                continue

            seen.add(title)

            source = article.get("source", {}).get("name", "Unknown")

            news_list.append(f"{len(news_list)+1}. {title} ({source})")

            if len(news_list) >= num_articles:
                break

        if len(news_list) < num_articles:
            fallback_params = {
                "apiKey": API_KEY,
                "language": "en",
                "pageSize": num_articles * 2
            }

            response = requests.get(BASE_URL, params=fallback_params, timeout=5)
            fallback_articles = response.json().get("articles", [])

            for article in fallback_articles:
                title = article.get("title", "")

                if not title or title in seen:
                    continue

                seen.add(title)

                source = article.get("source", {}).get("name", "Unknown")

                news_list.append(f"{len(news_list)+1}. {title} ({source})")

                if len(news_list) >= num_articles:
                    break

        return "\n".join(news_list)

    except Exception as e:
        print("ERROR:", str(e))
        return "Something went wrong while fetching news."