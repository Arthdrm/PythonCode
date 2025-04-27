"""
A Python script for performing news scrapping.

Author: Kadek Artha Darma Pradnyana
Date: 22 September 2024
"""
import asyncio
import pandas as pd
import time
import os
from playwright.sync_api import sync_playwright, TimeoutError

# Global Constants
SCRIPT_DIR = os.path.dirname(__file__)
RESULT_DIR = f"{SCRIPT_DIR}/scrapping_result/"
BASE_URL = "https://www.tempo.co/indeks/"


def main():
    url = f"{BASE_URL}2024-09-01/"
    file_name = f"{RESULT_DIR}test_scrap.csv"
    print("Scrapping running ====")
    scrapping_result = scrape_article_monthly(url)

    df = pd.DataFrame({
        'Link': scrapping_result[0],
        'Summary': scrapping_result[1]
    })
    df.to_csv(file_name, index=False)
    print("Amount of articles scrapped: {}".format(len(scrapping_result[0])))
    print("Scrapping complete =====")

def scrape_article_monthly(url):
    start_time = time.perf_counter()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()        
        while True:
            try:
                page.goto(url)
                article_links = []
                summaries_list = []
                # Collect all article links on the current page
                links = page.locator('article.text-card h2.title a')  
                summaries = page.locator('article.text-card p:not([class])')
                article_links.extend([link.get_attribute('href') for link in links.element_handles()])
                summaries_list.extend([summary.text_content() for summary in summaries.element_handles()])
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print("Scrapping took: {:.2f} s".format(elapsed_time))                
                break
            except TimeoutError as e:
                print("Time out error occured. Waiting for 2 seconds")
                time.sleep(2)        

        # Close browser
        browser.close()

    return article_links, summaries_list


if __name__ == "__main__":
    main()