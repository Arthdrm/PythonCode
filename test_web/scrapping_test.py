from playwright.sync_api import sync_playwright

def scrape_article_links(url, max_pages=5):
    with sync_playwright() as p:
        # Launch a browser instance (can be 'firefox', 'webkit', or 'chromium')
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Initialize list to store article links
        article_links = []

       # Loop through pagination
        for _ in range(max_pages):
            # Collect all article links on the current page
            links = page.locator('div.item div.img-thumb-4 a')  # Updated selector for article links
            article_links.extend([link.get_attribute('href') for link in links.element_handles()])

            # Check if there is a next page button and navigate to the next page
            next_button = page.locator('a.next')  # Update with correct selector for the next button
            if next_button.is_visible():
                next_button.click()
                page.wait_for_load_state('load')
            else:
                break  # No more pages to navigate

        # Close browser
        browser.close()

    return article_links

# Example usage
url = 'https://www.suara.com/indeks/terkini/kotaksuara/2023?page=1'  
article_links = scrape_article_links(url)
print(article_links)
