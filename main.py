from sqlite3 import Error

import numpy as np
from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException

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
url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'
import os.path
from os import path
from send_email import *

def record_data(centris_list):
    original_df = pd.DataFrame(centris_list)

    today=datetime.now()
    today=today.strftime("%Y%m%d")
    today_file_path=f"./test_{today}_{str(uuid.uuid4())[-4:]}.pkl"
    pd.to_pickle(original_df, today_file_path)



def scrap_pages(driver):
    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:
        price = listing.find_element(By.XPATH, './/*[@itemprop="price"]//following-sibling::span[1]').text
        price = price + "_" + str(uuid.uuid4())[-4:]
        mls = listing.find_element(By.XPATH, './/*[@class="a-more-detail"]').get_attribute('data-mlsnumber')
        #mls = mls+"_"+ str(uuid.uuid4())[-4:]


        prop_type = listing.find_element(By.XPATH,
                                         ".//div[@class='location-container']/span[@itemprop='category']").text
        addr = listing.find_element(By.XPATH, ".//div[@class='location-container']/span[@class='address']").text
        city = addr.split('\n')[1]
        sector = addr.split('\n')[2]
        if prop_type == 'Land for sale' or prop_type == 'Lot for sale':
            bedrooms = 'NA'
            bathrooms = 'NA'
        else:
            bedrooms = listing.find_element(By.XPATH, ".//div[@class='cac']").text
            bathrooms = listing.find_element(By.XPATH, ".//div[@class='sdb']").text

        listing_item = {
            'mls': mls,
            'price': price,
            'Address': addr,
            'property Type': prop_type,
            'city': city,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'sector': sector

        }

        centris_list.append(listing_item)


def flag_new_listings(latest_file, secondLatest_file):


    latest_panda = pd.read_pickle(latest_file)
    secondLatest_panda = pd.read_pickle(secondLatest_file)


    print(secondLatest_panda)
    print(latest_panda)

    latest_panda.set_index('mls')
    latest_panda.sort_index()
    secondLatest_panda.set_index('mls')
    secondLatest_panda.sort_index()

    price_changed_search_result=[]
    newListing_search_result=[]
    removedListing_search_result=[]

    # no new MLS listings, check if price changed
    if latest_panda.size == secondLatest_panda.size:

        latest_diff=latest_panda.compare(secondLatest_panda)
        for index in latest_diff.index:
            _mls=latest_panda.loc[index]['mls']
            _new_price=latest_panda.loc[index]['price']
            _old_price=secondLatest_panda.loc[index]['price']
            _content_str=f'listing {_mls} has changed its price from {_old_price} to {_new_price}'
            price_changed_search_result.append(_content_str)

    # returns new listings in latest_panda
    if latest_panda.size > secondLatest_panda.size:
        new_listing_panda=pd.concat([secondLatest_panda, latest_panda]).drop_duplicates(keep=False)
        print(new_listing_panda)
        for index in new_listing_panda.index:
            _mls=new_listing_panda.loc[index]['mls']
            _price=new_listing_panda.loc[index]['price']

            _content_str = f'New listing {_mls} is on sale at {_price}'
            newListing_search_result.append(_content_str)



    #removed listings
    if latest_panda.size < secondLatest_panda.size:
        removed_listing_panda=pd.concat([latest_panda, secondLatest_panda]).drop_duplicates(keep=False)
        for index in removed_listing_panda.index:
            _mls=removed_listing_panda.loc[index]['mls']

            _content_str = f'Listing {_mls} has disappeared'
            removedListing_search_result.append(_content_str)





    send_template_email(price_changed_search_result,newListing_search_result,removedListing_search_result)





def flag_renewaled_listings(files, latest_file, secondLatest_file):
    # for when agents remove an old list, and upload it again as a new listing
    # this function needs to troule through all the old pkl files and check because sometimes agents can wait a week or two before relisting
    latest_panda = pd.read_pickle(latest_file)
    secondLatest_panda = pd.read_pickle(secondLatest_file)




    sendEmail(subject='Same house relisted with different MLS number')


def flag_changes():

    files = list(filter(os.path.isfile, glob.glob("*.pkl")))
    files.sort(key=lambda x: os.path.getmtime(x))

    if len(files)> 1:
        latest_file=files[-1]
        secondLatest_file=files[-2]

        flag_new_listings(latest_file, secondLatest_file)
        #flag_renewaled_listings(files, latest_file, secondLatest_file)



if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    centris_list = []

    driver.get(url)

    total_pages = driver.find_element(By.CLASS_NAME, 'pager-current').text.split('/')[1].strip()

    #for i in range(1, int(total_pages)):
    for i in range(0,1):

        try:
            scrap_pages(driver)
            driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
            time.sleep(0.3)
        except ElementClickInterceptedException as initial_error:
            try:
                if len(driver.find_elements(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']")) > 0:
                    driver.find_element(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']").click()
                    time.sleep(0.3)
                print('pop-up closed')
                scrap_pages(driver)
                driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                time.sleep(0.3)
            except NoSuchElementException:
                raise initial_error

    record_data(centris_list)
    
    flag_changes()
    


