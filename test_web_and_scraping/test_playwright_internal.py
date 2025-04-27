import re
import time
from playwright.sync_api import Playwright, sync_playwright, expect
 
# Testing scenario
def run(playwright: Playwright) -> None:
    # setup browser and access the page
    browser = playwright.chromium.launch(headless=False, slow_mo=100) # with slow motion
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://pplfe-production-79c8.up.railway.app/") # access the page
 
    # generate single ipk
    page.get_by_role("row", name="1 8770034002 Teknik Komputer").get_by_role("button").click()
    page.get_by_role("row", name="2 6293338171 Teknik Komputer").get_by_role("button").click()
    page.get_by_role("row", name="3 2422192164 Teknik").get_by_role("button").click()
    page.get_by_role("button", name="Generate All IPK").click()
 
    # validate the output (after IPK has been generated)
    expect(page.locator("#app > div > div:nth-child(2) > div > div.v-table__wrapper > table > tbody > tr:nth-child(1) > td:nth-child(7) > span")).to_have_text("1.8333333333333333")
    expect(page.locator("#app > div > div:nth-child(2) > div > div.v-table__wrapper > table > tbody > tr:nth-child(2) > td:nth-child(7) > span")).to_have_text("0")
    expect(page.locator("#app > div > div:nth-child(2) > div > div.v-table__wrapper > table > tbody > tr:nth-child(3) > td:nth-child(7) > span")).to_have_text("0.8")
    expect(page.locator("#app > div > div:nth-child(2) > div > div.v-table__wrapper > table > tbody > tr:nth-child(4) > td:nth-child(7) > span")).to_have_text("2.2222222222222223")
 
    # validate pagination functionality (example 10 page)
    page.get_by_label("Page 1, Current page").click()
    page.get_by_label("Go to page 2").click()
    page.get_by_label("Go to page 3").click()
    page.get_by_label("Go to page 4", exact=True).click()
    page.get_by_label("Go to page 5").click()
    page.get_by_label("Go to page 6").click()
    page.get_by_label("Go to page 7").click()
    page.get_by_label("Go to page 8").click()
    page.get_by_label("Go to page 9").click()
    page.get_by_label("Go to page 10").click()
 
    # validate show specific amount (except 5)
    page.locator("div").filter(has_text=re.compile(r"^10$")).first.click()
    page.get_by_role("option", name="20").click()
    page.locator("div").filter(has_text=re.compile(r"^20$")).first.click()
    page.get_by_role("option", name="50").click()
    page.locator("div").filter(has_text=re.compile(r"^50$")).first.click()
    page.get_by_role("option", name="100").click()
    page.locator("div").filter(has_text=re.compile(r"^100$")).first.click()
    page.get_by_role("option", name="4425").click()
 
    # end process
    context.close()
    browser.close()
 
if __name__ == "__main__":
    # Run the playwright scenario (with synchronous API)
    with sync_playwright() as playwright:
        run(playwright)