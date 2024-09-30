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

# Asynchronous function to scrape articles for a particular month
async def scrape_article_monthly(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        article_links = []
        summaries_list = []
        
        # Extract the year and month from the URL
        current_date = datetime.strptime(url.split("/")[-2], "%Y-%m-%d")
        # Getting the last date of the current month (month provided by the URL)
        next_month = current_date.replace(day=28) + timedelta(days=4)  
        last_day_of_month = next_month - timedelta(days=next_month.day)

        # Total number of days to scrape (offset +1 for loop)
        total_days = (last_day_of_month - current_date).days + 1  

        # Extracting month name & year
        month_name = current_date.strftime('%B')  # Get the full month name
        year = current_date.strftime('%Y')  # Get the year
        
        # Progress bar setup
        async for _ in tqdm(range(total_days), desc=f"Progress {month_name} {year}".ljust(24)):
            try:
                formatted_url = f"{BASE_URL}{current_date.strftime('%Y-%m-%d')}/"
                await page.goto(formatted_url, timeout=60000, wait_until="domcontentloaded")
                # Collect all article links on the current page
                links = page.locator('article.text-card h2.title a')
                summaries = page.locator('article.text-card p:not([class])')
                
                article_links.extend([await link.get_attribute('href') for link in await links.element_handles()])
                summaries_list.extend([await summary.text_content() for summary in await summaries.element_handles()])
                
                current_date += timedelta(days=1)  # Move to the next day
            except Exception as e:
                tqdm.write(f"Timeout error occurred. Retrying after 2 seconds...")
                await asyncio.sleep(2)

        await browser.close()
    
    return article_links, summaries_list

async def scrape_article_content(url):
    async with sem:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            while True:
                try:
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")

                    # Get the script tag which contain the desired ld+json data
                    script_tags = await page.query_selector_all('head > script[type="application/ld+json"]')
                    script_content = await script_tags[1].inner_text()

                    # Parse the JSON content
                    json_data = json.loads(script_content)

                    # Extract article's content (Title, article body, date published, keyphrases)
                    article_title = json_data.get("headline")
                    article_published = json_data.get("datePublished")
                    article_body = json_data.get("articleBody")
                    article_keyphrases = json_data.get("keywords")

                    # Get the genre of the news
                    article_genre_tags = await page.query_selector_all('span[itemprop="name"]')
                    article_genre = await article_genre_tags[1].inner_text()

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
                    tqdm.write(f"Timeout error occurred. Retrying after 2 seconds...")
                    await asyncio.sleep(2)

            await browser.close()
        return article_content


async def main():
    # Base monthly URLs starting with the first date (ex: https://www.tempo.co/indeks/2023-01-01/) in the year 2023.
    months = [f"{BASE_URL}2023-{month:02d}-01/" for month in range(1, 3)]  
    
    # Create task for each month
    tasks_index = [scrape_article_monthly(url) for url in months] 
    
    # Create multiple tasks at once and wait for all of them to complete
    start_time_index = time.perf_counter()
    results_index = await asyncio.gather(*tasks_index) 
    elapsed_time_index = time.perf_counter() - start_time_index
    sys.stdout.flush()    
    print("")
    print("\n")   

    # Combine all results into a single DataFrame (for all months)
    all_links = []
    all_summaries = []
    
    # Iterating over individual month data
    for result in results_index:
        all_links.extend(result[0])
        all_summaries.extend(result[1])
    
    # Create multiple tasks for extracting individual news content
    start_time_individual = time.perf_counter()
    tasks_individual = [scrape_article_content(url) for url in all_links] 
    results_individual_list = await tqdm.gather(*tasks_individual, desc="Scraping Individual Pages", total=len(all_links)) 
    elapsed_time_individual = time.perf_counter() - start_time_individual

    # Combining list of dictionaries into a single dictionary
    results_individual = defaultdict(list)
    for d in results_individual_list:
        for key, value in d.items():
            results_individual[key].extend(value)  # Combine the list values
    results_individual = dict(results_individual)

    # Saving to dataframe
    file_name = f"{RESULT_DIR}scraped_articles_merged_2023.csv"
    df = pd.DataFrame({
        "url": all_links,
        "title": results_individual["title"],
        "body": results_individual["body"],
        "summary": all_summaries,        
        "date": results_individual["date"],
        "genre": results_individual["genre"],
        "keyphrases": results_individual["keyphrases"],        
    })    
    df.to_csv(file_name, index=False)

    # Final Reporting
    sys.stdout.flush()    
    print("")
    print("\n")    
    print(f"Scraping complete. Total articles scraped: {len(all_links)}")
    print(f"Time taken for scraping the index page: {elapsed_time_index:.2f}s")      
    print(f"Time taken for scraping individual news page: {elapsed_time_individual:.2f}s")          
    print(f"Results saved to {file_name}")

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
