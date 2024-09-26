"""
A Python script for performing news scrapping.

Author: Kadek Artha Darma Pradnyana
Date: 22 September 2024
"""

import pandas as pd
import time
from playwright.sync_api import sync_playwright, TimeoutError

# Global Constants
RESULT_DIR = "scrapping_result/"
BASE_URL = "https://www.tempo.co/indeks/"

def main():
    is_failed = True
    while is_failed:
        try:
            url = BASE_URL + "2024-09-01/"
            print("Scrapping running ====")
            scrapping_result = scrape_article_links(url)

            df = pd.DataFrame({
                'Link': scrapping_result[0],
                'Summary': scrapping_result[1]
            })
            df.to_csv(RESULT_DIR + 'test_1.csv', index=False)
            print("Amount of articles scrapped: {}".format(len(scrapping_result[0])))
            print("Scrapping complete =====")
            is_failed = False
        except TimeoutError as e:
            print(e)
            print("Time out error occured. Waiting for 2 seconds")
            time.sleep(2)
    print("Script finished.\n")

def scrape_article_links(url):
    start_time = time.time()
    with sync_playwright() as p:
        # Launch a browser instance (can be 'firefox', 'webkit', or 'chromium')
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        article_links = []
        summaries_list = []

        # Collect all article links on the current page
        links = page.locator('article.text-card h2.title a')  
        summaries = page.locator('article.text-card p:not([class])')
        article_links.extend([link.get_attribute('href') for link in links.element_handles()])
        summaries_list.extend([summary.text_content() for summary in summaries.element_handles()])

        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Scrapping took: {:.2f} s".format(elapsed_time))

        # Close browser
        browser.close()

    return article_links, summaries_list


if __name__ == "__main__":
    main()