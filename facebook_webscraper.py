import json
import os
import shutil
import sqlite3
import time
from datetime import datetime, timedelta

import pandas as pd
import patoolib
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

FACEBOOK_URL = "https://www.facebook.com/groups/EgyTA/announcements"
DOWNLOADED_LIST_JSON_PATH = "downloaded_list.json"

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get(FACEBOOK_URL)
time.sleep(3)

close_button = driver.find_element(By.XPATH, "//div[@aria-label='Close']")
close_button.click()
see_more_button = driver.find_element(By.XPATH, "//div[text()='See more']")
driver.execute_script("arguments[0].click();", see_more_button)

posts = driver.find_elements(By.TAG_NAME, "a")
media_fire_posts = []
downloaded_media_fire_files = []
files_to_unzip = []

# load previously downloaded media fire files
print("started loading downloaded list json file")
try:
    with open(DOWNLOADED_LIST_JSON_PATH, 'r') as file:
        downloaded_media_fire_files.extend(json.load(file))
        print("downloaded list file loaded successfully")
except FileNotFoundError:
    print("could not find downloaded list file")

for post in posts:
    if "mediafire.com/folder" in post.text and post.text not in downloaded_media_fire_files:
        media_fire_posts.append(post.text)
        downloaded_media_fire_files.append(post.text)

for media_fire_link in media_fire_posts:
    driver.get(media_fire_link)
    time.sleep(3)
    needed_file = driver.find_element(
        By.XPATH,
        "//a[contains(@class, 'foldername') and contains(@title, 'تنفيذات الجلسة.rar')]"
    )
    download_page_link = needed_file.get_attribute("href")
    driver.get(download_page_link)
    download_button = driver.find_element(By.ID, "downloadButton")
    download_link = download_button.get_attribute("href")

    # get date of the file
    ul_element = driver.find_element(By.CSS_SELECTOR, "ul.details")
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")
    li_text = li_elements[1].text
    file_date = li_text.split(": ", 1)[1]
    date_obj = datetime.strptime(file_date, "%Y-%m-%d %H:%M:%S")
    new_date_obj = date_obj - timedelta(days=1)
    file_actual_date = new_date_obj.strftime("%Y-%m-%d")

    # save rar file
    print(f"started saving {file_actual_date}.rar")
    file_response = requests.get(download_link)
    file_name = f"{file_actual_date}.rar"
    files_to_unzip.append(file_name)
    if file_response.ok:
        with open(file_name, "wb") as file:
            file.write(file_response.content)
        print(f"file {file_name} saved successfully")

# save links of the downloaded files
print("started saving downloaded list")
with open("downloaded_list.json", 'w') as file:
    json.dump(downloaded_media_fire_files, file)
    print("downloaded list saved successfully")

# unrar rar files
print("started unzipping rar files")
os.makedirs("data", exist_ok=True)
for rar_file in files_to_unzip:
    rar_dir = rar_file.split(".")[0]
    patoolib.extract_archive(rar_file, outdir=rar_dir)
    extracted_file = os.listdir(rar_dir)[0]
    new_file_name = f"{rar_dir}.xlsx"
    new_file_path = os.path.join(f"{os.getcwd()}/data", new_file_name)
    old_file_path = os.path.join(rar_dir, extracted_file)
    shutil.move(old_file_path, new_file_path)
    shutil.rmtree(rar_dir)

# delete unneeded zip files
print("started deleting zip files")
for zip_file in files_to_unzip:
    if os.path.exists(zip_file):
        os.remove(zip_file)
        print(f"file {zip_file} deleted successfully")

# dump data into db
print("started dumping data into db")
excel_files = os.listdir("data")
for excel_file in excel_files:
    date_str = excel_file.split(".")[0]
    date = datetime.strptime(date_str, "%Y-%m-%d")

    conn = sqlite3.connect('sqlite.db')
    cursor = conn.cursor()

    # add check that date not in db
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    is_db_empty = False if len(cursor.fetchall()) > 0 else True
    date_exists = False

    if not is_db_empty:
        cursor.execute("SELECT COUNT(*) FROM Trades WHERE date = ?", (date,))
        date_exists = True if len(cursor.fetchall()) > 0 else False

    if date_exists:
        print(f"Skipping dumping {excel_file} as the date already exists in db")
        continue

    df = pd.read_excel(f"data/{excel_file}", sheet_name="Sheet1")
    df.rename(columns={"الرمز": "code", "السهم": "name", "السعر": "price", "الكمية": "quantity", "التغير": "change",
                       "النوع": "type", "قيمة التداول": "trading_value"},
              inplace=True)

    df = df.assign(date=date)
    df.drop(columns=["الوقت", "التغير%"])

    print(f"started dumping {excel_file} into db")
    df.to_sql('Trades', conn, if_exists='append', index=False)

    conn.commit()
    conn.close()
    print(f"{excel_file} dumped into db successfully")

# delete unneeded data directory
print("started deleting data directory")
shutil.rmtree("data")
print("data files removed successfully")
