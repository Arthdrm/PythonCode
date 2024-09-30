"""
A Python script for performing news scrapping (async version).

Author: Kadek Artha Darma Pradnyana
Date: 22 September 2024
"""
import os
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import json
from tqdm.asyncio import tqdm
import time
import sys
from collections import defaultdict

# Global Constants
SCRIPT_DIR = os.path.dirname(__file__)
RESULT_DIR = f"{SCRIPT_DIR}/scrapping_result/"
BASE_URL = "https://www.tempo.co/indeks/"

# Create a semaphore to limit concurrent tasks
sem = asyncio.Semaphore(15)

async def scrape_article_content(browser, url):
    async with sem:
        page = await browser.new_page()
        try:
            while True:
                try:
                    await page.goto(url, timeout=60000, wait_until="load")
                    # Getting the script & genre tags
                    script_tags = page.locator('head script[type="application/ld+json"] + script[type="application/ld+json"]').nth(0)                
                    article_genre_tags = page.locator('ul.sitemap li:nth-child(2) span[itemprop="name"]')
                    
                    # Extrating article content & genre
                    script_content = await script_tags.inner_text(timeout=60000)
                    article_genre = await article_genre_tags.inner_text(timeout=60000)

                    # Parse the JSON content
                    json_data = json.loads(script_content)

                    # Extract article's content (Title, article body, date published, keyphrases)
                    article_title = json_data.get("headline")
                    article_published = json_data.get("datePublished")
                    article_body = json_data.get("articleBody")
                    article_keyphrases = json_data.get("keywords")

                    # Create a dictionary containing article's content
                    article_content = {
                        "url": url,
                        "title": article_title,
                        "body": article_body,
                        "date": article_published,
                        "genre": article_genre,
                        "keyphrases": article_keyphrases
                    }                    
                    break
                except Exception as e:
                    tqdm.write(f"{e} occurred. Retrying after 2 seconds...")
                    await asyncio.sleep(2)
        finally:
            await page.close()

        return article_content

async def main():
    df = pd.read_csv(r'C:\Users\User\Documents\Python_Projects\test_web\scrapping_result\test_scrap.csv')

    # Extract the desired column as a list
    column_name = 'Link'  # Replace with your actual column name
    all_links = df[column_name].tolist()[:50] # Extracting 50 links

    # Create multiple tasks for extracting individual news content
    start_time_individual = time.perf_counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        tasks_individual = [scrape_article_content(browser, url) for url in all_links] 
        results_individual_list = await tqdm.gather(*tasks_individual, desc="Scraping Individual Pages", total=len(all_links)) 
        await browser.close()    
    elapsed_time_individual = time.perf_counter() - start_time_individual

    with open('data.json', 'w') as f:
        json.dump(results_individual_list, f)

    # # Combining list of dictionaries into a single dictionary
    # results_individual = defaultdict(list)
    # for d in results_individual_list:
    #     for key, value in d.items():
    #         results_individual[key].extend(value)  # Combine the list values
    # results_individual = dict(results_individual)

    # # Saving to dataframe
    # file_name = f"{RESULT_DIR}scraped_articles_merged_2023.csv"
    # df = pd.DataFrame({
    #     "url": all_links,
    #     "title": results_individual["title"],
    #     "body": results_individual["body"],
    #     "date": results_individual["date"],
    #     "genre": results_individual["genre"],
    #     "keyphrases": results_individual["keyphrases"],        
    # })    
    # df.to_csv(file_name, index=False)

    # # Final Reporting
    # sys.stdout.flush()    
    # print("")
    # print("\n")    
    # print(f"Scraping complete. Total articles scraped: {len(all_links)}")
    # print(f"Time taken for scraping individual news page: {elapsed_time_individual:.2f}s")          
    # print(f"Results saved to {file_name}")

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
