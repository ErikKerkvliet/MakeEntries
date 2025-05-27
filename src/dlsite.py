import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class DlSite:

    def __init__(self, glv):
        self.glv = glv
        self.pageUrl = 'https://www.dlsite.com'
        self.base_url = 'https:'
        self.dlsite_id = ''
        self.vndb_id = ''
        self.soup = None
        
    def get_entry_data(self, driver, dlsite_id, vndb_id):
        
        print('Get dlsite main data')
        
        self.dlsite_id = dlsite_id

        data = {}
        
        url = f'{self.pageUrl}/maniax/work/=/product_id/{dlsite_id}.html/?locale=ja_JP'

        self.click_language_and_confirm_age(driver, url)

        source = driver.page_source
        self.soup = BeautifulSoup(source, 'html.parser')

        data['cover'] = ''
        data['romanji'] = ''
        data['title'] = ''
        data['infopage'] = f'{self.pageUrl}/maniax/work/=/product_id/{self.dlsite_id}.html'
        data['developer1'] = ''
        data['developer2'] = ''
        data['released'] = self.get_release_date()
        data['chars'] = []
        data['samples'] = []

        data = self.get_images(data)

        return data

    def get_images(self, data):

        img_tags = self.soup.find_all('img')
        data_src_tags = self.soup.find_all('div', attrs={'data-src': True})

        image_urls = []

        # Extract from img tags
        for img in img_tags:
            src = img.get('src')
            if src and '_img_smp' in src and src.endswith('.jpg'):
                full_url = urljoin(self.base_url, src.replace('///', '//'))
                image_urls.append(full_url)

        for div in data_src_tags:
            data_src = div.get('data-src')
            if data_src and data_src.endswith('_img_main.jpg'):
                # Construct full URL
                full_url = urljoin(self.base_url, data_src.replace('///', '//'))
                image_urls.append(full_url)

        # Extract from data-src attributes in div tags
        for div in data_src_tags:
            data_src = div.get('data-src')
            if data_src and '_img_smp' in data_src and data_src.endswith('.jpg'):
                full_url = urljoin(self.base_url, data_src.replace('///', '//'))
                image_urls.append(full_url)

        image_urls = list(set(image_urls))

        root = '{}/{}'.format(self.glv.app_folder, self.glv.vndb_id)
        root_temp = '{}/samples'.format(root)

        for url in image_urls:
            # Extract the image filename from the URL
            filename = os.path.basename(url)
            save_path = os.path.join(root_temp, filename)
            if 'main' in url and data['cover'] == '':
                data['cover'] = save_path
                save_path = f'{root}/_cover_1.jpg'
                if os.path.exists(save_path):
                    save_path = f'{root}/_cover_2.jpg'
                    data['cover2'] = save_path
                else:
                    data['cover1'] = save_path
            self.download_image(url, save_path)

        return data

    @staticmethod
    def download_image(url, save_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check for HTTP errors
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")

    def get_release_date(self):
        # Initialize release_date variable
        release_date = None

        # Find the table with id 'work_outline'
        work_outline_table = self.soup.find('table', id='work_outline')
        if work_outline_table:
            # Find all rows in the table
            rows = work_outline_table.find_all('tr')
            for row in rows:
                header = row.find('th')
                if header and '販売日' in header.text:
                    # Extract the date from the corresponding 'td'
                    date_td = row.find('td')
                    if date_td:
                        # Extract text and convert to desired format (YYYY/MM/DD)
                        date_text = date_td.get_text(strip=True)
                        # Assuming the date is in the format 'YYYY年MM月DD日'
                        import re
                        match = re.match(r'(\d{4})年(\d{2})月(\d{2})日', date_text)
                        if match:
                            year, month, day = match.groups()
                            return f"{year}/{month}/{day}"
                        break

    @staticmethod
    def click_language_and_confirm_age(driver, url):
        driver.get(url)

        try:
            # Initialize WebDriverWait
            wait = WebDriverWait(driver, 10)  # Timeout after 10 seconds

            # ---------------------------
            # Step 1: Handle Language Selection
            # ---------------------------

            # Wait until the language selection box is present
            language_box = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'type_lang_select'))
            )

            # Locate the "日本語" link by link text
            japanese_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, '日本語'))
            )

            # Click the "日本語" link
            japanese_link.click()
            print("Clicked the '日本語' (Japanese) language link successfully.")

            # Optional: Wait for the page to load after clicking language
            time.sleep(1)

            # ---------------------------
            # Step 2: Handle Age Confirmation
            # ---------------------------

            # Wait until the age confirmation box is present
            age_confirm_box = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'type_adultcheck'))
            )

            # Locate the "はい" link by link text
            yes_button = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'はい'))
            )

            # Click the "はい" button
            yes_button.click()
            print("Clicked the 'はい' (Yes) button successfully.")

            # Optional: Wait for some time to observe the result
            time.sleep(1)

        except Exception as e:
            print(f"An error occurred: {e}")
