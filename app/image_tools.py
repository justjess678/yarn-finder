import json
import os
import shutil
import urllib

import requests
from numpy.f2py.f90mod_rules import options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Set the path to the Chromedriver
DRIVER_PATH = '../lib/chromedriver-linux64/chromedriver'
SAVE_PATH = '../images/img.jpg'

if not os.path.isdir('../images'):
    os.mkdir('../images')
if not os.path.isdir('../reference'):
    os.mkdir('../reference')

def clear_data():
    if os.path.isfile('yarn_data.json'):
        os.remove('yarn_data.json')
    folder = '../images'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def read_data():
    with open('yarn_data.json', 'r') as file:
        data = file.read()
    return json.loads(data)

def make_data():
    clear_data()
    if not os.path.isfile('yarn_data.json'):
        # scrape those yarns
        ice_yarns = IceYarnsScraper()

        ice_yarns.get_number_of_pages()
        ice_yarns.get_yarn_pages()
        links = ice_yarns.yarn_links

        # get images for each
        for link in links:
            ice_yarns.get_photo(link)

        result = ice_yarns.get_output()
        ice_yarns.quit()

        print(f"Result: {result}")

        with open('yarn_data.json', 'w') as fp:
            json.dump(result, fp)

def get_image_by_url(url):
    try:
        response = requests.get(url, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            with open(SAVE_PATH, 'wb') as file:
                shutil.copyfileobj(response.raw, file)
            response.close()
            return True
        else:
            print(f"Failed to retrieve image. HTTP status code: {response.status_code}")
            response.close()
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        response.close()
        return False


class Scraper():

    def __init__(self):
        # Initialize the Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Enable headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)

    def go_to_page(self, url:str):
        # Navigate to the URL
        self.driver.get(url)

    def quit(self):
        # It's a good practice to close the browser when done
        self.driver.quit()


class IceYarnsScraper(Scraper):

    def __init__(self):
        super().__init__()
        self.yarn_links = []
        self.page_numbers = 1 # debug 371
        self.output = {}

    def get_yarn_pages(self):
        for i in range (1, self.page_numbers):
            self.driver.get(f"https://www.iceyarns.net/yarn/page/{i}")
            print(f'Scanning page {i}/{self.page_numbers}')
            try:
                ul_element = self.driver.find_element(By.ID, 'innerlist')
                a_elements = ul_element.find_elements(By.XPATH, './/li//a')

                if not a_elements:
                    print("The ul with ID 'innerlist' is empty or contains no 'a' elements.")
                else:
                    for a in a_elements:
                        if not self.is_lot(a.text):
                            href = a.get_attribute('href')
                            self.yarn_links.append(f"{href}")

            except Exception as e:
                print(f"An error occurred: {e}")

    def get_photo(self, url:str):
        self.driver.get(url)
        try:
            img_element = self.driver.find_element(By.XPATH,
                                                   '/html/body/div[4]/div[5]/div[1]/div[1]/div[1]/div[1]/ul[@class="cloud_small"]/li[2]/a/img')
            img_url = img_element.get_attribute('src')

            name = self.driver.find_element(By.XPATH, '//*[@id="pdm"]/div[2]/div[@class="product-detail-title"]/span')
            text = name.text

            if not self.is_lot(text):
                print(f'Getting photo for {text}')
                item = {"name": text, "image_url": img_url}
                self.output[url] = item
        except Exception as e:
            print(f"An error occurred: {e}")


    def get_output(self):
        return self.output

    def get_number_of_pages(self):
        print(f'Getting pages...')
        self.driver.get("https://www.iceyarns.net/yarn/page/1")
        self.page_numbers = 1
        while self.yarn_page_exists() or self.page_numbers < 100:
            self.page_numbers = self.page_numbers + 1
            self.driver.get(f"https://www.iceyarns.net/yarn/page/{self.page_numbers}")
        print(f'{self.page_numbers} pages')


    def yarn_page_exists(self):
        try:
            # Locate the ul element by its ID
            ul_element = self.driver.find_element(By.ID, 'innerlist')

            # Check if the ul element contains any child elements
            if len(ul_element.find_elements(By.TAG_NAME, 'li')) == 0:
                # Take action if the ul is empty
                print("The ul with ID 'innerlist' is empty.")
                return False
            else:
                return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def is_lot(self, name:str):
        return ("Lot" in name or "Shades" in name or "Mixed" in name or "Leftover" in name or "Needle" in name
                or "Hook" in name)
