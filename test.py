import numpy as np
from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd

import sqlite3 as sl

url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'


def scrap_pages(driver):
    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:

        print(listing.text.split('\n'))

        price = listing.find_element(By.XPATH, ".//div[@class='price']/meta[@itemprop='price']").text
        mls = listing.find_element(By.XPATH, ".//div[@id='MlsNumberNoStealth']/p").text
        print(f"mls is {mls} price is {price}")
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


if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    #chrome_options.add_argument("headless")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    centris_list = []

    driver.get(url)

    total_pages = driver.find_element(By.CLASS_NAME, 'pager-current').text.split('/')[1].strip()
    # scrap
    scrap_pages(driver)
    #driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()

    df = pd.DataFrame(centris_list)
    print(df)
