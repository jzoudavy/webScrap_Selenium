from sqlite3 import Error
import logging
import numpy as np
from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException

from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import uuid
import glob
import os
import os.path
from os import path
from send_email import *

def interesting_property_determinator(latest_panda, new_entries, changed_prices_df):
    interesting=latest_panda.loc[new_entries]['bedrooms'] >= 2
    x= changed_prices_df.index.intersection(new_entries)

    if not x.empty:
        px_interesting= changed_prices_df.loc[new_entries]['bedrooms'] >= 2
        logging.info(px_interesting)

    logging.info(f"Actually interesting: ")
    logging.info(interesting)




def record_data(centris_list):
    original_df = pd.DataFrame(centris_list)

    today=datetime.now()
    today=today.strftime("%Y%m%d")
    today_file_path=f"./Centris_{today}_{UUID}.pkl"
    pd.to_pickle(original_df, today_file_path)



def scrap_pages(driver):
    sqft=0
    year=0
    parking=0

    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:

        price = listing.find_element(By.XPATH, './/*[@itemprop="price"]//following-sibling::span[1]').text

        mls = listing.find_element(By.XPATH, './/*[@class="a-more-detail"]').get_attribute('data-mlsnumber')
        logging.info(f"Trowling through centris listing page: {mls}")


        prop_type = listing.find_element(By.XPATH,".//div[@class='location-container']/div[@class='category']").text

        addr = listing.find_element(By.XPATH, ".//div[@class='location-container']/div[@class='address']").text
        city = addr.split('\n')[1]
        sector = addr.split('\n')[2]
        if prop_type != 'Land for sale' and prop_type != 'Lot for sale':
            try:
                bedrooms = int(listing.find_element(By.XPATH, ".//div[@class='cac']").text)
            except NoSuchElementException:
                bedrooms = 0
            try:
                bathrooms = int(listing.find_element(By.XPATH, ".//div[@class='sdb']").text)
            except NoSuchElementException:
                bathrooms = 0

            listing_item = {
                'mls': mls,
                'price': price,
                'address': addr,
                'property type': prop_type,
                'city': city,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'sector': sector,
                'living sqft': sqft,
                'lot sqft': sqft,
                'year': year,
                'parking': parking
            }

            centris_list.append(listing_item)





def flag_new_listings(latest_file, secondLatest_file):


    latest_panda = pd.read_pickle(latest_file)
    secondLatest_panda = pd.read_pickle(secondLatest_file)


    latest_panda=latest_panda.set_index('mls')
    latest_panda=latest_panda.sort_index()
    secondLatest_panda=secondLatest_panda.set_index('mls')
    secondLatest_panda=secondLatest_panda.sort_index()

    new_entries = latest_panda.index.difference(secondLatest_panda.index)
    removed_entries = secondLatest_panda.index.difference(latest_panda.index)


    #find px changes
    common_mls = latest_panda.index.intersection(secondLatest_panda.index)
    price_changes = latest_panda.loc[common_mls, 'price'] != secondLatest_panda.loc[common_mls, 'price']
    changed_prices_df = latest_panda.loc[common_mls][price_changes] #only the ones where price changed
    # Add the old price from secondLatest_panda for reference
    changed_prices_df['old_price'] = secondLatest_panda.loc[changed_prices_df.index, 'price']
    # Rename column for clarity
    changed_prices_df = changed_prices_df.rename(columns={'price': 'new_price'})


    #send_template_email(new_entries, removed_entries, changed_prices_df)
    logging.info(f"new lists: ")
    logging.info(new_entries)
    logging.info(f"removed lists: ")
    logging.info(removed_entries)
    logging.info(f"price changes: ")
    logging.info(changed_prices_df)


    interesting_property_determinator(latest_panda, new_entries, changed_prices_df)




def flag_changes():

    files = list(filter(os.path.isfile, glob.glob("*.pkl")))
    files.sort(key=lambda x: os.path.getmtime(x))

    if len(files)> 1:
        latest_file=files[-1]
        secondLatest_file=files[-2]
        flag_new_listings(latest_file, secondLatest_file)



if __name__ == '__main__':


    today=datetime.now()
    today=today.strftime("%Y%m%d")
    start_time = time.time()
    UUID = str(uuid.uuid4())[-4:]

    logging.basicConfig(
        filename=f"centris_{today}_{UUID}_app.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    skip_scrape= True
    if skip_scrape:




        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)

        driver_path = 'C:\\WebDriver\\bin\\chromedriver132\\chromedriver.exe'
        options = webdriver.ChromeOptions()
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        centris_list = []

        url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'

        driver.get(url)
        time.sleep(2)
        driver.find_element(By.ID, 'didomi-notice-agree-button').click()

        total_pages = driver.find_element(By.CLASS_NAME, 'pager-current').text.split('/')[1].strip()

        for i in range(0, int(total_pages)):
        #for i in range(1):

            try:
                scrap_pages(driver)
                driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                time.sleep(0.5)
            except ElementClickInterceptedException as initial_error:
                try:
                    if len(driver.find_elements(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']")) > 0:
                        driver.find_element(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']").click()
                        time.sleep(0.5)
                    print('pop-up closed')
                    scrap_pages(driver)
                    driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                    time.sleep(0.3)
                except NoSuchElementException:
                    raise initial_error

        for item in centris_list:
            mls=item['mls']
            summaryURL = f'https://www.centris.ca/en/condos~for-sale~brossard/{mls}?view=Summary'
            logging.info(f"Getting detailed information for : {summaryURL}")

            driver.get(summaryURL)
            time.sleep(1)

            carac_title = driver.find_elements(By.CLASS_NAME, 'carac-title')

            carac_value = driver.find_elements(By.CLASS_NAME, 'carac-value')


            carac_dict = {i.text: j.text for i,j in zip(carac_title, carac_value)}

            item['year']= carac_dict['Year built']
            if item['property type']=='Condo for sale':
                if 'Net area' in carac_dict.keys():
                    item['living sqft'] = carac_dict['Net area']
            if item['property type']=='Duplex for sale':
                item['living sqft'] = carac_dict['Lot area']
            if item['property type']=='House for sale':
                if 'Living area' in carac_dict.keys():
                    item['living sqft'] = carac_dict['Living area']
                if 'Lot area' in carac_dict.keys():
                    item['lot sqft'] = carac_dict['Lot area']
            if 'Parking (total)' in carac_dict.keys():
                item['parking'] = carac_dict['Parking (total)']





        driver.close()

        record_data(centris_list)

    flag_changes()
    end_time=time.time()
    elapsed_seconds =end_time-start_time
    elapsed_time=elapsed_seconds/60
    logging.info(f"excution time is {elapsed_time:.2f}")
    


