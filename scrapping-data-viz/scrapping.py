import subprocess
import sys

# No need to include sadness (as it's already collected)
search_queries = {
    "generic": "prabowo",
    "anger": "(prabowo OR gibran OR wowo) (paok OR babi OR biadab OR benci OR sialan OR tai OR geram OR dengki OR tolol OR bajingan)",
    "sadness": "(prabowo OR gibran OR wowo) (sedih OR duka OR pilu OR susah OR muram OR derita OR tangis OR nangis OR murung OR luka OR tragis OR menyedihkan OR merana)",
    "suprise": "(prabowo OR gibran OR wowo) (kagum OR tercengang OR kejut OR tertegun OR kagum OR melongo OR terpukau)",
    "joy": "(prabowo OR gibran OR wowo) (menang OR riang OR gembira OR ceria OR hibur OR bahagia OR senang OR seneng OR girang OR lucu OR menyenangkan OR happy OR sukacita)",
    "disgust": "(prabowo OR gibran OR wowo) (jijik OR mual OR enggan OR muntah OR goblok OR muak OR najis OR jorok OR busuk OR jengkel OR bau OR kotor)",
    "fear": "(prabowo OR gibran OR wowo) (cemas OR gelisah OR ngeri OR khawatir OR takut OR merinding OR gemetar OR ancam OR panik OR ketir)"
}

date_range = {
    "november":["28-11-2023", "30-11-2023"],
    "december":["01-12-2023", "30-12-2023"],
    "january":["01-01-2024", "31-01-2024"],
    "february":["01-02-2024", "29-02-2024"],
    "march":["01-03-2024", "17-03-2024"]
}

# date_range = {
#     "november":["28-11-2023", "29-11-2023"]
# }

# Constructing the run command from terminal arguments
token = sys.argv[1]
emotion = sys.argv[2]
command = {
    "package" : "npx",
    "scrapper" : "tweet-harvest@latest",
    "token_option" : "-t",
    "token_value" : token,
    "search_option" : "-s",
    "search_value" : search_queries[emotion],
    "limit_option" : "-l",
    "limit_value" : "50000",
    "tab_option": "--tab",
    "tab_value" : "LATEST",
    "date_start_option" : "-f",
    "date_start_value" : None,
    "date_end_option" : "-to",
    "date_end_value" : None
}

# Scraping
for date in date_range.values():
    command["date_start_value"] = date[0]
    command["date_end_value"] = date[1]
    list_command = [value for value in command.values()]
    print("====== Start Scrapping ... ======")
    result = subprocess.run(list_command, capture_output=True, text=True, shell=True)
    result_list = str(result.stdout).split("\n")
    print("====== Scrapping successful...======")
    print("====== Result: {} =====\n".format(result_list[-2]))   

# temp_command_1 = 'npx tweet-harvest@latest -t 5aa215dfb6a1756ff296181ddac3f2bc3939c839 -s bakso -l 30 --tab LATEST'.split()
