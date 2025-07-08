import time
import os
import os.path
import re
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from selenium.common.exceptions import TimeoutException
from PIL import Image


class Getchu:

    def __init__(self, globalvar):
        self.glv = globalvar
        self.getchu_id = ''
        self.page_url = 'http://www.getchu.com'
        self.lines = []
        self.char_nr = 0
        self.char_nrs = []
        self.nrs = {}
        self.data = None

    @staticmethod
    def find_str(full, sub):
        sub_index = 0
        position = -1
        for ch_i, ch_f in enumerate(full):
            if ch_f.lower() != sub[sub_index].lower():
                position = -1
                sub_index = 0
            if ch_f.lower() == sub[sub_index].lower():
                if sub_index == 0:
                    position = ch_i

                if (len(sub) - 1) <= sub_index:
                    break
                else:
                    sub_index += 1

        return position

    def get_entry_data(self, web_driver, getchu_id, vndb_id):
        self.glv.log('')
        self.glv.log('Getting site main data')

        data = {
            'released': '0000-00-00',
            'cover': '',
            'infopage': '',
            'chars': [],
            'samples': []
        }

        self.getchu_id = getchu_id

        web_driver.get('{}/soft.phtml?id={}'.format(self.page_url, self.getchu_id))

        source = web_driver.page_source

        spans = None
        if 'gc=gc">' in source:
            spans = self.glv.get_elements('tag', 'a')

        try:
            for span in spans:
                if '【は い】' in span.text or '【すすむ】' in span.text:
                    span.click()
                    break
        except Exception as e:
            print("Error clicking on 'はい' span:", e)
            pass

        time.sleep(3)

        js = '$("#buyee-bcSection").remove()'
        web_driver.execute_script(js)

        url = '{}/soft.phtml?id={}'.format(self.page_url, self.getchu_id)

        delay = 5  # seconds
        try:
            WebDriverWait(web_driver, delay).until(ec.presence_of_element_located((By.CLASS_NAME, 'chara-name')))
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
         
        source = web_driver.page_source

        start = self.find_str(source, '<div class="tabletitle">&nbsp;キャラクター</div>')
        sub_str = source[start:]

        end = self.find_str(sub_str, '</tbody></table>')
        sub_str = sub_str[:end]

        char_trs = sub_str.split('<tr>')

        data['infopage'] = url

        if 'NOW PRINTING' not in source:
            data['cover'] = '{}/brandnew/{}/c{}package.png'.format(self.page_url, self.getchu_id, self.getchu_id)

        a_s = self.glv.get_elements('tag', 'a')

        for a in a_s:
            href = a.get_attribute('href')
            if href is not None and 'start_date' in href:
                data['released'] = a.get_attribute('innerHTML')

        self.get_character_data(char_trs, data)

        data['samples'] = []
        self.data = data

        # if 'anidb' in self.glv.db_label:
        #     return data

        self.glv.log('Getting screenshot images')

        self.download_images(web_driver, vndb_id)

        return data

    def get_character_data(self, char_trs, data):
        self.glv.log('Getting getchu character data')
        for i, tr in enumerate(char_trs):
            if i == 0:
                continue

            imgs = tr.split('src=".')

            img1 = ''
            if len(imgs) == 1:
                continue

            data['chars'].append([])
            data['chars'][-1] = {}

            if len(imgs) > 1:
                img1 = imgs[1].split('.png"')
                img1 = self.page_url + img1[0] + '.png'

            img2 = ''
            if len(imgs) > 2:
                img2 = imgs[-1].split('.png"')
                img2 = self.page_url + img2[0] + '.png'
                img2 = img2.replace('_s', '')

            cup = ''
            if len(imgs) > 1:
                if 'カップ' in imgs[1]:
                    cup_split = imgs[1].split('カップ')[0]
                    cup = cup_split[-1]
                elif '<span>' in imgs[1]:
                    span_split = imgs[1].split('span')[1]
                    if '（' in span_split:
                        cup_split = span_split.split('（')[-1]
                        cup = cup_split[0]
                elif '<b>' in imgs[1] and 'font' not in imgs[1]:
                    b_split = imgs[1].split('<b>')[1]
                    if '（' in b_split or '(' in b_split:
                        cup_split = ['']
                        if '（' in b_split:
                            cup_split = b_split.split('（')[-1]
                        if '(' in b_split:
                            cup_split = b_split.split('(')[-1]

                        if cup_split.__class__.__name__ == 'list':
                            cup = cup_split[0]
                        else:
                            cup = cup_split
                if len(cup) != 1:
                    cup = ''

            name = ''
            if 'class="chara-name">' in tr:
                name = tr.split('class="chara-name">')

            if len(name) > 1:
                if '</charalist>' in tr:
                    name = tr.split('</charalist>')[0]
                    name = name.split('<charalist>')[-1]
                    name = self.split_name_on_parenthesis(name)
                else:
                    if '</h2>' in name[1]:
                        name = name[1].split('</h2>')[0]
                        name = self.split_name_on_parenthesis(name)
                    if '<br>' in name:
                        name = name.split('<br>')[-1]
                    if '<br />' in name:
                        name = name.split('<br />')[-1]
                    if '<br/>' in name:
                        name = name.split('<br/>')[-1]
                    if len(name) > 1 and 'CV' in name:
                        name = name.split('CV')[0]

                if name.__class__.__name__ == 'list':
                    name = name[0]

                name = name.replace('　', ' ')
                name = name.replace('\n', '')
                name_text = name.strip(' ')
                name = re.sub(r'<[^>]+>', '', name_text).strip(' ')

            data['chars'][-1]['name'] = name.replace('<strong>', '').replace('</strong>', '')
            data['chars'][-1]['romanji'] = ''
            data['chars'][-1]['age'] = ''
            data['chars'][-1]['cup'] = cup
            data['chars'][-1]['measurements'] = ''
            data['chars'][-1]['height'] = ''
            data['chars'][-1]['weight'] = ''
            data['chars'][-1]['gender'] = 'female'
            data['chars'][-1]['img1'] = img1.split('"')[0]
            data['chars'][-1]['img2'] = img2.split('"')[0]

            self.glv.log('-------------------------------------------------------------')
            self.glv.log('Name: {}'.format(data['chars'][-1]['name']))
            self.glv.log('Romanji: {}'.format(data['chars'][-1]['romanji']))
            self.glv.log('Gender: {}'.format(data['chars'][-1]['gender']))
            self.glv.log('Height: {}'.format(data['chars'][-1]['height']))
            self.glv.log('Weight: {}'.format(data['chars'][-1]['weight']))
            self.glv.log('Measurements: {}'.format(data['chars'][-1]['measurements']))
            self.glv.log('Age: {}'.format(data['chars'][-1]['age']))
            self.glv.log('Cup: {}'.format(data['chars'][-1]['cup']))
            self.glv.log('Image 1: {}'.format(data['chars'][-1]['img1']))
            self.glv.log('Image 2: {}'.format(data['chars'][-1]['img2']))

    @staticmethod
    def split_name_on_parenthesis(name):
        name = name.split('（')[0]
        name = name.split('(')[0]
        name = name.split('「')[0]
        name = name.split('「')[0]
        name = name.split('「')[0]
        name = name.split('『')[0]

        return name

    def download_images(self, driver, vndb_id):
        script = "$('.highslide').attr('onclick', 'window.open(this)');$('.highslide').attr('onkeypress', '')"
        driver.execute_script(script)
        if 'anidb' in self.glv.db_label:
            script = "$('.highslide').first().click()"
            driver.execute_script(script)
            high_slide_images = [self.glv.get_elements('class', 'highslide', True)]
        else:
            script = "$('.highslide').click()"
            driver.execute_script(script)
            high_slide_images = self.glv.get_elements('class', 'highslide')

        root = '{}/{}'.format(self.glv.app_folder, vndb_id)
        root_temp = '{}/temp'.format(root)

        self.glv.sleep(2)

        images = self.glv.get_elements('tag', 'img')
        char_nr = 1
        for image in images:
            src = image.get_attribute('src')
            image_name = src.split('/')[-1]

            if '_' not in image_name and 'charab' not in image_name and 'chara' in image_name:
                nr = image_name.split('chara')[1].split('.')[0]
                self.nrs[nr] = char_nr
                self.char_nrs.append(char_nr)
                img_name = '__img{}'.format(char_nr)
                char_nr += 1
                self.save_image_screenshot(driver, root_temp, image, img_name)

        length = len(high_slide_images)
        for i in range(0, length):
            tab = length - i
            driver.switch_to.window(driver.window_handles[tab])

            url = driver.current_url

            if 'anidb.net' in self.glv.db_site and 'package' not in url:
                continue

            if '_' in url or not ('chara' in url or 'table' in url or 'package' in url or 'sample' in url):
                continue

            tab_img = self.glv.get_element('tag', 'img')
            if tab_img == 0:
                continue
            try:
                WebDriverWait(driver, 1).until(
                    ec.presence_of_element_located((By.TAG_NAME, 'img')))
            except TimeoutException:
                print("Loading took too much time!")

            self.save_image_screenshot(driver, root_temp, tab_img)

        self.glv.log('')

    def save_image_screenshot(self, driver, save_location, image, name=''):

        if name == '':
            src = image.get_attribute('src')
            if 'charab' in src:
                nr = src.split('charab')[1].split('.')[0]
                if nr not in self.nrs.keys():
                    return

                image_name = f'char{self.nrs[nr]}.png'
            else:
                image_name = src.split('/')[-1].split('.')[0] + '.png'
        else:
            image_name = name + '.png'

        location = image.location_once_scrolled_into_view

        self.glv.log('Save: {} to: {}/'.format(image_name, save_location))

        size = image.size

        driver.save_screenshot(image_name)

        image = Image.open(image_name)
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        image = image.crop((left, top, right, bottom))  # defines crop points

        full_image_name = '{}/{}'.format(save_location, image_name)
        image.save(full_image_name, 'png')  # saves new cropped image

        count = 0
        while not os.path.isfile(full_image_name):
            time.sleep(0.1)
            count += 1

        if count == 5:
            input("Waiting for input.")

        new_image = full_image_name.replace('.png', '.jpg')
        if '/temp/' in full_image_name and '__img' in full_image_name:
            nr = re.findall(r'\d+', full_image_name.split('/')[-1])[0]

            new_image = new_image.replace(new_image.split('/temp/')[-1], f'{nr}/__img.jpg')
            new_image = new_image.replace('/temp/', f'/chars/')
            new_folder = new_image.split('/__')[0]
            if not os.path.isdir(new_folder):
                os.makedirs(new_folder)

        count = 0
        while not os.path.isfile(full_image_name):
            time.sleep(0.1)
            count += 1

        if count == 5:
            input("Waiting for input.")

        command = 'convert {} {}'.format(full_image_name, new_image)
        os.system(command)

        while not os.path.isfile(new_image):
            time.sleep(0.1)
            count += 1

        if count == 5:
            input(new_image)

        command = 'rm {}'.format(image_name)

        os.system(command)



