from selenium import webdriver

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd

url = 'https://www.centris.ca/en/properties~for-sale~brossard?view=Thumbnail'


def scrap_pages(driver):
    listings = driver.find_elements(By.CLASS_NAME, 'description')

    if listings[-1].text.split('/n')[0] == '': del listings[-1]

    for listing in listings:
        print(listing.text.split('\n'))
        price = listing.text.split('\n')[0]

        prop_type = listing.text.split('\n')[1]
        addr = listing.text.split('\n')[2]
        city = listing.text.split('\n')[3]
        sector = listing.text.split('\n')[4]
        bedrooms = listing.text.split('\n')[5]
        bathrooms = listing.text.split('\n')[6]

        listing_item = {
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


    centris_list=[]

    driver.get(url) 

    total_pages = driver.find_element(By.CLASS_NAME,'pager-current').text.split('/')[1].strip() 
    
    for i in range(1,int(total_pages)):
        scrap_pages(driver)
        driver.find_element(By.CSS_SELECTOR,'li.next> a').click()
        time.sleep(0.8)


    df = pd.DataFrame(centris_list)

    print(df)






