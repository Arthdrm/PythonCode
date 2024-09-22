from playwright.sync_api import sync_playwright

def scrape_article_links(url):
    with sync_playwright() as p:
        # Launch a browser instance (can be 'firefox', 'webkit', or 'chromium')
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        article_links = []
        summaries_list = []

        # Collect all article links on the current page
        links = page.locator('article.text-card h2.title a')  # Updated selector for article links
        summaries = page.locator('article.text-card p')
        article_links.extend([link.get_attribute('href') for link in links.element_handles()])
        summaries_list.extend([summary.text_content() for summary in summaries.element_handles()])

        # Close browser
        browser.close()

    return article_links, summaries_list

# Example usage
url = 'https://www.tempo.co/indeks/2024-09-01/'  
(article_links, summaries) = scrape_article_links(url)
for link in article_links:
    print("- {}".format(link))
for summary in summaries:
    print("- {}".format(summary))