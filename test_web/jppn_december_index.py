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
from tqdm.asyncio import tqdm
import time
import sys
from collections import defaultdict
from itertools import chain
import re

# Global Constants
SCRIPT_DIR = os.path.dirname(__file__)
RESULT_DIR = f"{SCRIPT_DIR}/scrapping_result/"
BASE_URL = "https://www.jpnn.com/indeks"

# Create a semaphore to limit concurrent tasks
# sem = asyncio.Semaphore(10)

# Asynchronous function to scrape articles for a particular month
async def scrape_article_monthly(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        article_links = []
        
        # Finding the date information on the url
        # Ex: https://www.jpnn.com/indeks?id=&d=01&m=10&y=2024&tab=all        
        url_date_pattern = r"d=(\d{2})&m=(\d{2})&y=(\d{4})"
        match = re.search(url_date_pattern, url)      
        day_url = match.group(1)
        month_url = match.group(2)
        year_url = match.group(3)
        date_url = f"{year_url}-{month_url}-{day_url}"

        # Extract the year and month from the URL
        current_date = datetime.strptime(date_url, "%Y-%m-%d")
        # Getting the last date of the current month (month provided by the URL)
        next_month = current_date.replace(day=28) + timedelta(days=4)  
        last_day_of_month = next_month - timedelta(days=next_month.day)

        # Total number of days to scrape (offset +1 for loop)
        total_days = (last_day_of_month - current_date).days + 1  

        # Extracting month name & year (for progress bar descriptions)
        month_name = current_date.strftime('%B')  # Get the full month name
        year = current_date.strftime('%Y')  # Get the year
        
        # Extracting current date, month, and year
        current_month = current_date.strftime('%m')
        current_year = current_date.strftime('%Y')

        # Progress bar setup
        async for _ in tqdm(range(total_days), desc=f"Progress {month_name} {year}".ljust(24)):
            try:
                current_day = current_date.strftime('%d')
                formatted_url = f"{BASE_URL}?id=&d={current_day}&m={current_month}&y={current_year}&tab=all"
                await page.goto(formatted_url, timeout=60000, wait_until="domcontentloaded")
                # Collect all article links on the current page
                links = page.locator('h1 a')
                article_links.extend([await link.get_attribute('href') for link in await links.all()])
                
                # Handle Pagination
                while True:
                    # Checking the next button
                    next_button = page.locator('.pagination a', has_text='Next').first
                    if await next_button.count() > 0:
                        await next_button.click()                        
                        await page.wait_for_load_state('domcontentloaded')
                        links_next = page.locator('h1 a')
                        article_links.extend([await link.get_attribute('href') for link in await links_next.all()])
                    else:
                        break
                current_date += timedelta(days=1)  # Move to the next day
            except Exception as e:
                tqdm.write(f"Timeout error occurred. Retrying after 2 seconds...")
                await asyncio.sleep(2)

        await browser.close()
    
    return article_links

async def main():
    # URL format: https://www.jpnn.com/indeks?id=&d=02&m=10&y=2024&tab=all
    for year in range(2023, 2024):
        # Base monthly URLs starting with the first date in each month
        months = [f"{BASE_URL}?id=&d=01&m={month:02d}&y={year}&tab=all" for month in range(12, 13)]  
        
        # Create task for each month
        tasks_index = [scrape_article_monthly(url) for url in months] 
        
        # Create multiple tasks at once and wait for all of them to complete
        start_time_index = time.perf_counter()
        results_index = await asyncio.gather(*tasks_index) 
        elapsed_time_index = time.perf_counter() - start_time_index

        # Flatten list
        all_links = list(chain.from_iterable(results_index))
        
        # Saving to dataframe
        file_name = f"{RESULT_DIR}december_jppn_index_{year}.csv"
        df = pd.DataFrame({
            "url": all_links     
        })    
        df.to_csv(file_name, index=False)

        # Final Reporting
        sys.stdout.flush()    
        print("")  
        print(f"Scraping complete. Total articles scraped: {len(all_links)}")
        print(f"Time taken for scraping the index page: {elapsed_time_index:.2f}s")      
        print(f"Results saved to {file_name}")

        # Small break
        time.sleep(10)

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
