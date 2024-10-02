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
sem = asyncio.Semaphore(2)

async def scrape_article_content(url):
    async with sem:
        async with async_playwright() as p: 
            browser = await p.chromium.launch()
            page = await browser.new_page()
            complete_article_body = []

            while True:
                try:
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

                    # Extrating the text of these tags
                    article_body = await article_body_tags.all_inner_texts()
                    title = await title_tag.inner_text()
                    genre = await genre_tag.inner_text()
                    keyphrases= await keyphrases_tags.all_inner_texts()
                    summary = await summary_tag.inner_text()

                    # Adding article body
                    complete_article_body.extend(article_body)

                    # In case of pagination, combine the article content
                    while True:
                        # Checking the next button
                        next_button = page.locator('.pagination a', has_text='Next').first
                        if await next_button.count() > 0:
                            await next_button.click()                        
                            await page.wait_for_load_state('domcontentloaded')
                            article_body_tags_next = page.locator('div[itemprop="articleBody"] p')
                            article_body_next = await article_body_tags_next.all_inner_texts()
                            complete_article_body.extend(article_body_next)
                        else:
                            break

                    # Create a dictionary containing article's content
                    article_content = {
                        "url": url,
                        "title": title,
                        "body": " ".join(complete_article_body),
                        "genre": genre,
                        "keyphrases": keyphrases,
                        "summary": summary
                    }                    

                    break
                except Exception as e:
                    tqdm.write(f"{e} occurred. Retrying after 2 seconds...")
                    await asyncio.sleep(2)

        return article_content

async def main():
    all_links = [
        "https://www.jpnn.com/news/sule-ungkap-alasan-turun-tangan-membela-mahalini",
        "https://www.jpnn.com/news/komdis-pssi-beri-hukuman-tambahan-kepada-marc-klok-persib-harus-bersabar",
        "https://www.jpnn.com/news/prudential-indonesia-dorong-program-pengembangan-anak-di-rote-ndao-ntt",
        "https://jogja.jpnn.com/jogja-terkini/9706/indikasi-suap-mencuat-dalam-upaya-pembangunan-liquid-di-sleman",
        "https://jabar.jpnn.com/jabar-terkini/20357/pemkot-bandung-segera-buka-akses-sementara-exit-tol-149",
        "https://jateng.jpnn.com/kriminal/13692/polda-jateng-periksa-47-saksisoal-kasus-kematian-dr-aulia-risma-ppds-undip",
        "https://jabar.jpnn.com/jabar-terkini/20355/pemkab-karawang-siagakan-ratusan-faskes-demi-layani-penderita-tbc",
        "https://jabar.jpnn.com/olahraga/20356/rezaldi-hehanusa-perpanjang-kontrak-bersama-persib-bandung",
        "https://www.jpnn.com/news/mahasiswa-papua-ajak-calon-kepala-daerah-kampanyekan-pilkada-damai",
        "https://www.jpnn.com/news/rekaman-cctv-pembubaran-diskusi-fta-di-kemang-disita-polisi-begini-aksi-si-rambut-kuncir"
    ]

    # Create multiple tasks for extracting individual news content
    start_time_individual = time.perf_counter()
    tasks_individual = [scrape_article_content(url) for url in all_links] 
    results_individual_list = await tqdm.gather(*tasks_individual, desc="Scraping Individual Pages", total=len(all_links)) 
    elapsed_time_individual = time.perf_counter() - start_time_individual

    with open('data_jppn.json', 'w') as f:
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
    print(f"Time taken for scraping individual news page: {elapsed_time_individual:.2f}s")          
    # print(f"Results saved to {file_name}")

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())