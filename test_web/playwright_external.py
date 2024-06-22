import re
from playwright.sync_api import Playwright, sync_playwright, expect
import requests
import random

def run(playwright: Playwright, url, table_data, random_nim) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)
    page.get_by_role("button", name="Hitung IPK Semua Mahasiswa").click()

    # Assert text "Rata-rata IPK adalah <value>"
    expect(page.get_by_text("Rata-rata IPK adalah"), "Rata-rata IPK adalah 3.36").to_be_visible()

    # Assert 101 <tr> (include header) after clicking Hitung IPK Semua Mahasiswa button
    tr_elements = page.locator('#ipkTable tr')
    expect(tr_elements).to_have_count(101)

    # Asserting every value of IPK in the table (according to its NIM)
    id = 2 # Start position
    for x in range(len(table_data)):
        selector_nim = "#ipkTable > tbody > tr:nth-child({}) > td:nth-child(1)".format(id)
        selector_ipk = "#ipkTable > tbody > tr:nth-child({}) > td:nth-child(2)".format(id)
        nim_val = page.locator(selector_nim).inner_text()
        ipk_val_raw = table_data[nim_val]["ipk"]
        ipk_val = str(int(ipk_val_raw)) if ipk_val_raw.is_integer() else str(ipk_val_raw) # Determine whether to cast IPK value to integer first before casting it to string.
        expect(page.locator(selector_ipk)).to_have_text(ipk_val)     
        id += 1

    # Assert the IPK of 5 randomly selected NIM (Hitung IPK feature)
    for i in range(5):
        page.get_by_placeholder("Masukkan NIM").fill(random_nim[i]["nim"])
        page.get_by_role("button", name="Hitung IPK", exact=True).click()    
        ipk_val = str(int(random_nim[i]["ipk"])) if random_nim[i]["ipk"].is_integer() else str(random_nim[i]["ipk"]) # Determine whether to cast IPK value to integer first before casting it to string.
        expected_str = "Mahasiswa dengan NIM {} memiliki IPK {}".format(random_nim[i]["nim"], ipk_val)
        expect(page.locator("#result")).to_contain_text(expected_str)        


    # ---------------------
    context.close()
    browser.close()

def fetch_table(url):
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["body"]["ipk_per_nim"]

def fetch_random(url):
    random_nim = []
    list_nim = [random.randint(0, 100) for _ in range(5)]
    for nim in list_nim:
        nim_str = "{:03d}".format(nim) # Add "0" padding if the space is available.       
        response = requests.get(url + nim_str)
        response.raise_for_status()
        random_nim.append(response.json()["body"])
    return random_nim      


url_front_end = "https://dev.d2f1sduhafpfhd.amplifyapp.com/"
url_api_semua = "https://u4d4nidfz9.execute-api.ap-southeast-2.amazonaws.com/dev/semua"
url_api_individu = "https://u4d4nidfz9.execute-api.ap-southeast-2.amazonaws.com/dev/ipk?nim="
table_data = fetch_table(url_api_semua)
random_nim = fetch_random(url_api_individu)


with sync_playwright() as playwright:
    run(playwright, url_front_end, table_data, random_nim)
