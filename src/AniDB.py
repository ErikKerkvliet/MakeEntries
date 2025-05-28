import os

import requests
from dotenv import load_dotenv

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

        self.glv.sleep(1)

        user = os.getenv("ANIDB_USER")
        js = f'$(\'input[name="xuser"]\').val("{user}")'
        self.glv.run_js(js)

        password = os.getenv("ANIDB_PASSWORD")
        js = f'$(\'input[name="xpass"]\').val("{password}")'
        self.glv.run_js(js)

        self.glv.sleep(1)

        js = '$(\'button[name="do.auth"]\').click()'
        self.glv.run_js(js)

    def get_entry_data(self, driver, anidb_id):
        print('Get AniDB main data')

        self.login()

        self.anidb_id = anidb_id

        data = {}

        url = f'{self.pageUrl}/anime/{anidb_id}'

        driver.get(url)

        data['title'] = self.get_title()

        js = '$(\'span[itemprop="name"]\')[3].innerHTML'
        data['romanji'] = self.glv.run_js(js, True)

        js = '$(\'img[itemprop="image"]\').attr("src")'
        data['cover'] = self.glv.run_js(js, True)

        data['infopage'] = url
        data['webpage'] = ''

        developer = self.glv.db.find_developer_by_anidb_id(self.anidb_id)
        if developer == 0:
            developer = ''

        data['developer1'] = developer
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
        js = '$(\'label[itemprop="alternateName"]\').html()'
        title = self.glv.run_js(js, True)

        series = self.glv.db.get_series_by_anidb_id(self.anidb_id)
        count = 1 if not series else len(series)

        nr = str(count).zfill(2)
        full_title =  f'{title} Vol. {nr}'

        while self.glv.db.check_duplicate(full_title, type='ova'):
            count += 1
            nr = str(count).zfill(2)
            full_title = f'{title} Vol. {nr}'

        return full_title

    def download_cover(self):
        js = '$("picture img").first().attr("src")'
        url = self.glv.run_js(js, True)
        save_path = f'{self.glv.app_folder}/{self.glv.vndb_id}/_cover_2.jpg'
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check for HTTP errors
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
