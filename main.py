#!/usr/bin/python3
import logging
import sys
import numpy as np
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
import paramiko
import yaml


def interesting_property_determinator(latest_panda, new_entries, changed_prices_df):

    interesting=latest_panda.loc[new_entries]

    interesting=(interesting['bedrooms'] >= 2) & (interesting['price'] <= 600000)& (interesting['price'] >= 400000)

    filtered_list = interesting.index.tolist()


    logging.info(f"2 bedroom or more and 600k or less: ")
    logging.info(filtered_list)

    #find px changes
    px_change= changed_prices_df.to_dict(orient='index')



    # load templates folder to environment (security measure)
    env = Environment(loader=FileSystemLoader('template'))
    # load the `index.jinja` template
    index_template = env.get_template('index.jinja')
    output_from_parsed_template = index_template.render(mls=filtered_list, data =px_change)


    if os.name == 'nt':
        # write the parsed template
        with open("index.html", "w") as indexPage:
            indexPage.write(output_from_parsed_template)


        with open('config.yaml', 'r') as file:
            prime_service = yaml.safe_load(file)
            host = prime_service['host']['ip']
            port = prime_service['host']['port']
            password = prime_service['host']['password']
            username = prime_service['host']['username']

        transport_UploadFile = paramiko.Transport((host, port))

        transport_UploadFile.connect(username=username, password=password)

        sftp = paramiko.SFTPClient.from_transport(transport_UploadFile)

        sftp.put("index.html", f"/var/www/html/index.html")


        sftp.close()
        transport_UploadFile.close()
    else: # write the parsed template
        with open("/var/www/html/index.html", "w") as indexPage:
            indexPage.write(output_from_parsed_template)




def record_data(centris_list):
    original_df = pd.DataFrame(centris_list)

    today=datetime.now()
    today=today.strftime("%Y%m%d")

    if os.name == 'nt':
        today_file_path = f"./centris_{today}_{UUID}.pkl"
    else:
        today_file_path = f"/home/bloom/centris_scrap/webScrap_Selenium/centris_{today}_{UUID}.pkl"

    pd.to_pickle(original_df, today_file_path)
    time.sleep(10)
    logging.info(f"waited 10 seconds for file write to complete. ")



def scrap_pages(driver):
    sqft=0
    year=0
    parking=0

    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:

        str_price = listing.find_element(By.XPATH, './/*[@itemprop="price"]//following-sibling::span[1]').text
        str_price=str_price.replace('$','')
        str_price=str_price.replace(',', '')
        price=int(str_price)

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

    try:
        latest_panda = pd.read_pickle(latest_file)
    except Exception as e:
        logging.exception(e)
    try:
        secondLatest_panda = pd.read_pickle(secondLatest_file)
    except Exception as e:
        logging.exception(e)
    logging.info(f"latest file: {latest_file}")
    logging.info(f"2nd latest file: {secondLatest_file}")


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
    else:
        logging.info(f"no comparison done for there is less than 2 files")



if __name__ == '__main__':

    today=datetime.now()
    today=today.strftime("%Y%m%d")
    start_time = time.time()
    UUID = str(uuid.uuid4())[-4:]

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--skip_scrape", type=bool, default=False, help='dont scrape the webpage')
    parser.add_argument("-tp","--total_pages", type=int, help='number of pages to scrape')
    args = parser.parse_args()

    if os.name == 'nt':
        filename = f"centris_{today}_{UUID}_app.log"
    else:
        filename = f"/home/bloom/centris_scrap/webScrap_Selenium/centris_{today}_{UUID}_app.log"

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
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
        chrome_options.add_argument("--window-size=2560,1440")
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.53 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')

        driver_path = 'C:\\WebDriver\\bin\\chromedriver132\\chromedriver.exe'
        driver_path_ubuntu = r'/usr/local/bin/chromedriver'

        if os.name == 'nt':
            service = ChromeService(executable_path=driver_path) #win
        else:
            service = ChromeService(executable_path=driver_path_ubuntu)

        driver = webdriver.Chrome(service=service, options=chrome_options)

        centris_list = []

        url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'

        driver.get(url)
        time.sleep(3)
        driver.find_element(By.ID, 'didomi-notice-agree-button').click() #respect privacy button

        total_pages = driver.find_element(By.CLASS_NAME, 'pager-current').text.split('/')[1].strip()

        if args.total_pages is not None:
            total = args.total_pages
        else:
            total=int(total_pages)

        for i in range(0, total):


            try:
                scrap_pages(driver)
                driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                time.sleep(2)
            except ElementClickInterceptedException as initial_error:
                try:
                    if len(driver.find_elements(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']")) > 0:
                        driver.find_element(By.XPATH, ".//div[@class='DialogInsightLightBoxCloseButton']").click()
                        time.sleep(2)
                    print('pop-up closed')
                    scrap_pages(driver)
                    driver.find_element(By.CSS_SELECTOR, 'li.next> a').click()
                    time.sleep(2)
                except NoSuchElementException:
                    raise initial_error

        for item in centris_list:
            mls=item['mls']
            summaryURL = f'https://www.centris.ca/en/condos~for-sale~brossard/{mls}?view=Summary'
            logging.info(f"Getting detailed information for : {summaryURL}")

            driver.get(summaryURL)
            time.sleep(3)

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
    


