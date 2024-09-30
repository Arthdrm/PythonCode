from playwright.sync_api import sync_playwright
import json
import time

def extract_article_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="load")

        # Get the script tag which contain the desired ld+json data
        script_content = page.query_selector_all('head > script[type="application/ld+json"]')[1].inner_text()

        # Parse the JSON content
        json_data = json.loads(script_content)

        # Extract article's content (Title, article body, date published, keyphrases)
        article_title = json_data.get("headline")
        article_published = json_data.get("datePublished")
        article_body = json_data.get("articleBody")
        article_keyphrases = json_data.get("keywords")

        # Get the genre of the news
        article_genre = page.query_selector_all('span[itemprop="name"]')[1].inner_text()

        # Create a dictionary containing article's content
        article_content = {
            "title": article_title,
            "body": article_body,
            "date": article_published,
            "genre": article_genre,
            "keyphrases": article_keyphrases
        }

        browser.close()
        return article_content

# Usage example
start_time = time.perf_counter()
url = "https://nasional.tempo.co/read/216808/sebelum-meninggal-gus-dur-sering-membicarakan-pkb"
article_content = extract_article_content(url)
elapsed_time = time.perf_counter() - start_time
print(f"Time taken: {elapsed_time:.2f}s")  
for key, value in article_content.items():
    print(f"{key}: {value}")
    print("")
