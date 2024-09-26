"""
A Python script for performing news scrapping (async version).

Author: Kadek Artha Darma Pradnyana
Date: 22 September 2024
"""
import os
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time
from datetime import datetime, timedelta

# Global Constants
SCRIPT_DIR = os.path.dirname(__file__)
RESULT_DIR = f"{SCRIPT_DIR}/scrapping_result/"
BASE_URL = "https://www.tempo.co/indeks/"

# Asynchronous function to scrape articles for a particular month
async def scrape_article_monthly(url):
    # start_time = time.perf_counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        article_links = []
        summaries_list = []
        
        # Extract the year and month from the URL
        current_date = datetime.strptime(url.split("/")[-2], "%Y-%m-%d")
        next_month = current_date.replace(day=28) + timedelta(days=4)  # Ensures we roll over to the next month
        last_day_of_month = next_month - timedelta(days=next_month.day)
        
        while current_date <= last_day_of_month:
            try:
                formatted_url = f"{BASE_URL}{current_date.strftime('%Y-%m-%d')}/"
                print(f"Scraping {formatted_url}...")
                await page.goto(formatted_url, timeout=60000)  # Set a longer timeout
                
                # Collect all article links on the current page
                links = page.locator('article.text-card h2.title a')  
                summaries = page.locator('article.text-card p:not([class])')
                
                article_links.extend([await link.get_attribute('href') for link in await links.element_handles()])
                summaries_list.extend([await summary.text_content() for summary in await summaries.element_handles()])
                
                current_date += timedelta(days=1)  # Move to the next day
            except Exception as e:
                print(f"Error occurred: {e}. Retrying after 2 seconds...")
                await asyncio.sleep(2)

        await browser.close()
    
    # elapsed_time = time.perf_counter() - start_time
    # print(f"Scraping completed for {url}. Time taken: {elapsed_time:.2f}s")
    
    return article_links, summaries_list

# Main function to scrape articles for 12 months concurrently
async def main():
    months = [f"{BASE_URL}2023-{month:02d}-01/" for month in range(1, 13)]  # URLs for January to December
    tasks = [scrape_article_monthly(url) for url in months]  # Create tasks for each month
    
    results = await asyncio.gather(*tasks)  # Run all scraping tasks concurrently
    
    # Combine all results into a single DataFrame
    all_links = []
    all_summaries = []
    
    for result in results:
        all_links.extend(result[0])
        all_summaries.extend(result[1])
    
    df = pd.DataFrame({
        'Link': all_links,
        'Summary': all_summaries
    })
    
    file_name = f"{RESULT_DIR}scraped_articles_2023.csv"
    df.to_csv(file_name, index=False)
    print(f"Scraping complete. Total articles scraped: {len(all_links)}")
    print(f"Results saved to {file_name}")

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
