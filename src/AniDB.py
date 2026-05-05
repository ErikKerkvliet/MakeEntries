import os

import requests
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()


class AniDB:

    def __init__(self, glv):
        self.glv = glv
        self.pageUrl = 'https://www.anidb.net'
        self.base_url = 'https:'
        self.anidb_id = ''

    def login(self):
        print('Log into AniDB')

        self.glv.driver.get(self.pageUrl)

        wait = WebDriverWait(self.glv.driver, 15)

        user_field = wait.until(EC.presence_of_element_located((By.NAME, 'xuser')))
        user_field.clear()
        user_field.send_keys(os.getenv("ANIDB_USER"))

        pass_field = self.glv.driver.find_element(By.NAME, 'xpass')
        pass_field.clear()
        pass_field.send_keys(os.getenv("ANIDB_PASSWORD"))

        self.glv.driver.find_element(By.CSS_SELECTOR, 'button[name="do.auth"]').click()

        # Wait until the login form disappears (successful login redirects away)
        wait.until(EC.invisibility_of_element_located((By.NAME, 'xuser')))

    def get_entry_data(self, driver, anidb_id):
        print('Get AniDB main data')

        self.login()

        self.anidb_id = anidb_id

        data = {}

        url = f'{self.pageUrl}/anime/{anidb_id}'
        driver.get(url)

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'label[itemprop="alternateName"]')))

        data['title'] = self.get_title()

        js = 'return document.querySelectorAll(\'span[itemprop="name"]\')[3].innerHTML'
        data['romanji'] = driver.execute_script(js)

        js = 'return document.querySelector(\'img[itemprop="image"]\').src'
        data['cover'] = driver.execute_script(js)

        data['infopage'] = url
        data['webpage'] = ''

        developer = self.glv.db.find_developer_by_anidb_id(self.anidb_id)
        if developer and len(developer) > 0:
            data['developer1'] = developer[0][1] if developer[0][1] else ''
            data['developer1_id'] = str(developer[0][0]) if developer[0][0] else ''
        else:
            data['developer1'] = ''
            data['developer1_id'] = ''

        data['developer2'] = ''
        data['released'] = ''
        data['chars'] = []
        data['samples'] = []

        self.download_cover()
        return data

    def get_developer(self):
        self.glv.driver = self.glv.driver
        return ''

    @staticmethod
    def get_char_data():
        return {
            'chars': [],
        }

    def get_title(self):
        js = 'return document.querySelector(\'label[itemprop="alternateName"]\').innerHTML'
        title = self.glv.driver.execute_script(js)

        series = self.glv.db.get_series_by_anidb_id(self.anidb_id)
        count = 1 if not series else len(series)

        nr = str(count).zfill(2)
        full_title = f'{title} Vol. {nr}'

        while self.glv.db.check_duplicate(full_title, entry_type='ova'):
            count += 1
            nr = str(count).zfill(2)
            full_title = f'{title} Vol. {nr}'

        return full_title

    def download_cover(self):
        js = 'return document.querySelector("picture img").src'
        url = self.glv.driver.execute_script(js)
        save_path = f'{self.glv.app_folder}/{self.glv.vndb_id}/_cover_2.jpg'
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
