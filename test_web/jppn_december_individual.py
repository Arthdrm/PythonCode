"""
A Python script for performing news scrapping (async version).

Author: Kadek Artha Darma Pradnyana
Date: 22 September 2024
"""
import os
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from tqdm.asyncio import tqdm
import time
import sys

# Global Constants
SCRIPT_DIR = os.path.dirname(__file__)
RESULT_DIR = f"{SCRIPT_DIR}/scrapping_result/"

# Create a semaphore to limit concurrent tasks
sem = asyncio.Semaphore(7)

# This function is only scraping 1 article at a time (but this function can be run concurrently)
async def scrape_article_content(url):
    async with sem:
        async with async_playwright() as p: 
            browser = await p.chromium.launch()
            page = await browser.new_page()
            complete_article_body = []
            overlay = False
            retry_attempt = 1
            article_content = {}
            while retry_attempt < 4:
                try:
                    # Going to the url
                    await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    # Getting the article body element (<p> elements)
                    article_body_tags = page.locator('div[itemprop="articleBody"] p')        
                    # Get the title tag
                    title_tag = page.locator('h1.judul')
                    # Get the genre tag
                    genre_tag = page.locator('div.breadcrumb a').nth(1)                    
                    # Get the keyphrases tags
                    keyphrases_tags = page.locator('div.tags > a:not(.text-tags)')
                    # Get the summary (description) tag
                    summary_tag = page.locator('div.text-center.relative > :first-child').first
                    # Extract the date
                    date_tag = page.locator('.date-publish')

                    # Extrating the text of these tags
                    article_body = await article_body_tags.all_inner_texts()
                    title = await title_tag.inner_text()
                    genre = await genre_tag.inner_text()
                    keyphrases= await keyphrases_tags.all_inner_texts()
                    summary = await summary_tag.inner_text()
                    date_str = await date_tag.inner_text()

                    # Processing date data
                    date_str = date_str.replace("\u2013", "-")
                    date_part = date_str.split("-")[0]
                    date = date_part.split(',')[1].strip() # Ex: 01 Januari 2009
                    id_eng_months = {
                        "Januari": "January",
                        "Februari": "February",
                        "Maret": "March",
                        "April": "April",
                        "Mei": "May",
                        "Juni": "June",
                        "Juli": "July",
                        "Agustus": "August",
                        "September": "September",
                        "Oktober": "October",
                        "November": "November",
                        "Desember": "December"
                    }   
                    for id_month, eng_month in id_eng_months.items():
                        date = date.replace(id_month, eng_month)                 

                    # Adding article body
                    complete_article_body.extend(article_body)

                    # In case of pagination, combine the article content
                    next_button = page.locator('.pagination a', has_text='Next').first
                    if await next_button.count() > 0:
                        # Going to the next page                    
                        await next_button.click()                        
                        await page.wait_for_load_state('domcontentloaded')
                        article_body_tags_next = page.locator('div[itemprop="articleBody"] p')
                        article_body_next = await article_body_tags_next.all_inner_texts()
                        complete_article_body.extend(article_body_next)

                    # Create a dictionary containing article's content
                    article_content = {
                        "url": url,
                        "title": title,
                        "body": " ".join(complete_article_body),
                        "genre": genre,
                        "date": date,                        
                        "keyphrases": keyphrases,
                        "summary": summary,
                        "overlay": overlay
                    }                    

                    break
                except Exception as e:
                    tqdm.write(f"An error occured to {url}. Retry attempt no: {retry_attempt}. Retrying after 3 seconds...")
                    overlay = True
                    complete_article_body.clear()
                    await asyncio.sleep(3)
                    retry_attempt += 1
            await browser.close()

        return article_content

async def main():
    # Load the index df
    df_index = pd.read_csv(r'C:\Users\User\Documents\Python_Projects\test_web\scrapping_result\december_jppn_index_2023.csv')
    all_links = df_index['url'].tolist()

    batch_size = 5000 
    batch_num = 19  
    for i in range(0, len(all_links), batch_size): 
        batch = all_links[i:i + batch_size]

        # Create multiple tasks for extracting individual news content
        start_time_individual = time.perf_counter()
        tasks_individual = [scrape_article_content(url) for url in batch] 
        results_individual_list = await tqdm.gather(*tasks_individual, desc="Scraping Individual Pages", total=len(batch))  # Return a list of dictionary
        elapsed_time_individual = time.perf_counter() - start_time_individual

        # Saving to dataframe
        df_final = pd.DataFrame(results_individual_list)
        file_name = f"{RESULT_DIR}jppn_2023_batch_{batch_num}.csv"  
        df_final.to_csv(file_name, index=False)

        # Final Reporting
        sys.stdout.flush()    
        sys.stderr.flush()
        print("-------")    
        print(f"Finished batch: {batch_num}")
        print(f"Time taken for scraping individual news page: {elapsed_time_individual:.2f}s")          
        print(f"Results saved to {file_name}")
        print("Break between batches for 20 seconds.............\n")
        batch_num += 1
        del results_individual_list, df_final, batch
        time.sleep(20)


# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())