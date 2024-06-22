import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://dev.d2f1sduhafpfhd.amplifyapp.com/")
    page.get_by_role("button", name="Hitung IPK Semua Mahasiswa").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
