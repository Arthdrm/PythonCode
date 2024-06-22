import requests
import json
from collections import OrderedDict
import random

def fetch_and_parse_json(url):
    # Send a GET request to the URL
    response = requests.get(url)
    # Raise an exception if the request was not successful
    response.raise_for_status()
    
    # Parse the JSON response to a dictionary
    data = response.json()

    return data["body"]["ipk_per_nim"]

# URL of the API endpoint
# url = 'https://u4d4nidfz9.execute-api.ap-southeast-2.amazonaws.com/dev/semua'

# Fetch and parse the JSON data
# json_data = fetch_and_parse_json(url)

# print(json_data)



# for key, val in json_data.items():
#     print(val)
#     print("Key: {}, Val: {}".format(key, val["ipk"]))


def fetch_random(url):
    random_nim = []
    list_nim = [random.randint(0, 100) for _ in range(5)]
    print(list_nim)
    for nim in list_nim:
        nim_str = "{:03d}".format(nim) # Add "0" padding if the space is available.
        response = requests.get(url + nim_str)
        response.raise_for_status()
        random_nim.append(response.json()["body"])
    return random_nim      


url_api_individu = "https://u4d4nidfz9.execute-api.ap-southeast-2.amazonaws.com/dev/ipk?nim="
random_nim = fetch_random(url_api_individu)
print(random_nim)