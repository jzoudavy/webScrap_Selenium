
import logging

from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException
import argparse
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from datetime import datetime
import uuid
import glob
import os
import os.path
from jinja2 import Environment, FileSystemLoader





def scrap_pages(driver):
    sqft=0
    year=0
    parking=0

    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:

        price=12333

        mls = '12333'

        prop_type = 'test'
        addr = 'test'
        city = 'test'
        sector = 'test'
        bedrooms = 1
        bathrooms=1
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






if __name__ == '__main__':

    today=datetime.now()
    today=today.strftime("%Y%m%d")
    start_time = time.time()
    UUID = str(uuid.uuid4())[-4:]

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--skip_scrape", type=bool, default=False, help='dont scrape the webpage')
    parser.add_argument("-tp","--total_pages", type=int, help='number of pages to scrape')
    args = parser.parse_args()



    filename = f"centris_{today}_{UUID}_app.log"

    logging.basicConfig(
        filename=filename,
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M",
        force=True
    )

    logging.info(f"We are starting the app")
    logging.info(f"We are scraping : {args.total_pages}")

    if not args.skip_scrape:
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        #headless and block anti-headless
        chrome_options.add_argument('--headless')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')

        driver_path = 'C:\\WebDriver\\bin\\chromedriver132\\chromedriver.exe'
        driver_path_ubuntu = r'/usr/lib/chromium-browser/chromedriver'

        if os.path.exists(driver_path):
            service = ChromeService(executable_path=driver_path)
        else:
            service = ChromeService(executable_path=driver_path_ubuntu)

        driver = webdriver.Chrome(service=service, options=chrome_options)

        centris_list = []

        url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'

        driver.get(url)
        time.sleep(5)
        driver.find_element(By.ID, 'didomi-notice-agree-button').click()

        total_pages = driver.find_element(By.CLASS_NAME, 'pager-current').text.split('/')[1].strip()

        if args.total_pages is not None:
            total = args.total_pages
        else:
            total=int(total_pages)
        ''' 
        for i in range(0, total):


            try:
                scrap_pages(driver)
                driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                time.sleep(3)
            except ElementClickInterceptedException as initial_error:
                try:
                    if len(driver.find_elements(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']")) > 0:
                        driver.find_element(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']").click()
                        time.sleep(3)
                    print('pop-up closed')
                    scrap_pages(driver)
                    driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                    time.sleep(3)
                except NoSuchElementException:
                    raise initial_error

        '''



        driver.close()

    end_time=time.time()
    elapsed_seconds =end_time-start_time
    elapsed_time=elapsed_seconds/60
    logging.info(f"excution time is {elapsed_time:.2f}")
    


