import os
import shutil
import sys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
from random import uniform
import urllib.request
import subprocess
from Db import DB

from PIL import Image


class Globalvar:

    def __init__(self):
        self.errorMessage = 'Start\n'
        self.db = DB(self)
        self.connection = self.db.connection
        self.home = '/home/erik'  # os.path.expanduser('~')
        self.app_folder = '{}/MakeEntries'.format(self.home)
        self.img_folder = '{}/entry_images'.format(self.app_folder)
        self.downloadFolder = ''
        self.entry_id = None
        self.test = False
        self.developer = 9999999
        self.character = 9999999

        self.entries_table = None
        self.characters_table = None
        self.developers_table = None
        self.entry_characters_table = None
        self.entry_developers_table = None
        self.driver = None

    def set_test(self, state):
        self.test = state

    def get_test(self):
        return self.test

    def get_developer(self):
        return self.developer

    def get_character(self):
        return self.character

    def set_tables(self):
        self.entries_table = 'entries' if not self.test else 'entries_2'
        self.characters_table = 'characters' if not self.test else 'characters_2'
        self.developers_table = 'developers' if not self.test else 'developers_2'
        self.entry_characters_table = 'entry_characters' if not self.test else 'entry_characters_2'
        self.entry_developers_table = 'entry_developers' if not self.test else 'entry_developers_2'

    def log(self, message, log_type='message', browser=None):
        message = str(message)
        self.errorMessage += message
        self.errorMessage += '\n'
        print(message)
        if log_type == 'error':
            browser.quit()

    @staticmethod
    def get_screen_resolution():
        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',
                                  shell=True,
                                  stdout=subprocess.PIPE
                                  ).communicate()[0]
        resolution = output.split()[0].split(b'x')
        return [int(resolution[0]), int(resolution[1])]

    def set_download_dir(self, vndb_id):
        self.downloadFolder = '{}/{}/temp'.format(self.app_folder, vndb_id)

    def get_download_dir(self):
        return self.downloadFolder

    def set_driver(self, driver):
        self.driver = driver

    def get_driver(self):
        return self.driver

    @staticmethod
    def get_source():
        with open('/home/erik/test.txt', 'r+') as f:
            # f.write(source)
            line = '<html>'
            lines = []
            while line != '</html>':
                line = f.readline().strip('\n')
                lines.append(line)

            return lines

    @staticmethod
    def sleep(start, to=0):
        if to != 0:
            sleep = uniform(start, to)
        else:
            sleep = start

        time.sleep(sleep)

    def get_element_old(self, driver, by, value, wait=0, depth=0):
        original_driver = self.driver
        self.driver = driver
        result = self.get_element(by, value, wait, depth)
        self.driver = original_driver
        return result

    def get_elements_old(self, driver, by, value, wait=0, depth=0):
        original_driver = self.driver
        self.driver = driver
        result = self.get_elements(by, value, wait, depth)
        self.driver = original_driver
        return result

    # by can be id / css_selector / xpath / tag / name / link_text / partial_text / class
    def get_element(self, by, value, wait=1, depth=0):
        by = self.un_simplify(by)
        # If the element isn't found after 3 iterations return 0
        if depth >= 2:
            self.log("Can't find element '{0}', even after searching a long time".format(value))
            return 0

        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            # Wait a while and try again
            time.sleep(wait)
            return self.get_element(by, value, 1, depth + 1)

    # by can be css_selector / xpath / tag / name / link_text / class
    def get_elements(self, by, value, wait=1, depth=0, single=False):
        by = self.un_simplify(by)
        # if the element is not found after 3 iterations return 0
        if depth >= 2:
            self.log("Can't find element '{0}', even after searching a long time".format(value))
            return 0

        try:
            if single:
                return self.driver.find_elements(by, value)[0]
            return self.driver.find_elements(by, value)
        except NoSuchElementException:
            # Wait a while and try again
            time.sleep(wait)
            return self.get_elements(by, value, 1, depth + 1)

    def get_element_in_element(self, parent_element, by, value, single=False):
        main_driver = self.driver
        self.driver = parent_element

        result = self.get_elements(by, value, 1, 0, single)

        self.driver = main_driver

        return result

    @staticmethod
    def un_simplify(by):
        if by in [By.ID, By.XPATH, By.XPATH]:
            return by
        elif by == 'css':
            return By.CSS_SELECTOR
        elif by == 'tag':
            return By.TAG_NAME
        elif by == 'text' or by == 'link_text':
            return By.LINK_TEXT
        elif by == 'partial_text':
            return By.PARTIAL_LINK_TEXT
        elif by == 'class':
            return By.CLASS_NAME
        else:
            return by

    def make_main_dirs(self, vndb_id):
        if not os.path.isdir(self.app_folder):
            os.makedirs(self.app_folder, mode=0o7777)

        if not os.path.isdir("{}/{}/temp".format(self.app_folder, vndb_id)):
            os.makedirs("{}/{}/temp".format(self.app_folder, vndb_id), mode=0o7777)

        if not os.path.isdir("{}/{}".format(self.app_folder, vndb_id)):
            os.makedirs("{}/{}".format(self.app_folder, vndb_id), mode=0o7777)

        if not os.path.isdir("{}/{}/samples".format(self.app_folder, vndb_id)):
            os.makedirs("{}/{}/samples".format(self.app_folder, vndb_id), mode=0o7777)

        if not os.path.isdir("{}/{}/chars".format(self.app_folder, vndb_id)):
            os.makedirs("{}/{}/chars".format(self.app_folder, vndb_id), mode=0o7777)

    def make_char_dir(self, vndb_id, char_id):
        folder = "{}/{}/chars/{}".format(self.app_folder, vndb_id, char_id)
        if not os.path.isdir(folder):
            os.makedirs("{}/{}/chars/{}".format(self.app_folder, vndb_id, char_id), mode=0o7777)

    def download_images(self, data, vndb_id):
        self.set_download_dir(vndb_id)

        chars = data['chars']
        samples = data['samples']

        root = '{}/{}'.format(self.app_folder, vndb_id)

        if data['cover1'] != '':
            self.download_url(data['cover1'], '_cover_1')
            data['cover1'] = '{}/_cover_1.jpg'.format(root)
        if data['cover2'] != '':
            self.download_url(data['cover2'], '_cover_2')
            data['cover2'] = '{}/_cover_2.jpg'.format(root)

        for j, char in enumerate(chars):
            img2 = ''
            j_up = j + 1

            root_char = '{}/chars/{}'.format(root, j_up)

            self.make_char_dir(vndb_id, j_up)

            self.download_url(char['img1'], '__img{}.jpg'.format(j_up))

            img1 = '{}/__img.jpg'.format(root_char)
            if char['img2'] != '' and char['img2'].split('"')[0] != '':
                self.download_url(char['img2'], 'char{}'.format(j_up))

                img2 = '{}/char.jpg'.format(root_char)

            data['chars'][j]['img1'] = img1
            data['chars'][j]['img2'] = img2

        root_samples = '{}/samples'.format(root)
        new_samples = []
        for i, sample in enumerate(samples):
            i_up = i + 1
            self.download_url(sample, 'sample{}'.format(i_up))

            new_samples.append('{}/sample{}.jpg'.format(root_samples, i_up))

        data['samples'] = new_samples

    def download_url(self, url, filename):
        url = url.split('"')[0]

        if 'vndb.org' in url:
            self.log('Download url: {} to: {}'.format(url, filename))

            self.sleep(0.5)

            try:
                urllib.request.urlretrieve(url, '{}/{}'.format(self.downloadFolder, filename))
                self.log('Downloaded')
            except Exception as exc:
                self.log(exc)

                print(type(exc))
                print(exc.args)
                print(exc)
                print(url)
                return

            return

    @staticmethod
    def convert_to_jpg(file_path, save_path):
        image = Image.open(file_path)
        image.save(save_path)

    @staticmethod
    def clean_string(string):
        string = string.replace('&amp;', '&')
        string = string.replace('&nbsp;', ' ')
        string = string.replace('&lt;', '<')
        string = string.replace('&gt;', '>')
        string = string.replace('&quot;', '"')
        string = string.replace('&apos;', "'")
        string = string.replace('&cent;', '¢')
        string = string.replace('&pound;', '£')
        string = string.replace('&yen;', '¥')
        string = string.replace('&euro;', '€')
        string = string.replace('&copy;', '©')
        string = string.replace('&reg;', '®')

        return string

    def clean_folder(self, start='false'):
        folder = self.app_folder

        if start == 'true':
            path = '/var/www/Hcapital/entry_images/entries/999999'

            if os.path.isdir(path):
                self.clean_folder(path)
                shutil.rmtree(path)

            for i in range(100):
                try:
                    path = '/var/www/Hcapital/entry_images/char/{}'.format(999901 + i)

                    if os.path.isdir(path):
                        self.clean_folder(path)
                        os.rmdir(path)
                except:
                    continue

        if start != 'false' and start != 'true':
            folder = start

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

            if not os.path.isdir(folder + '/temp') and 'char' not in folder:
                os.mkdir(folder + '/temp')

    def quit(self):
        print('Closing application')

        self.driver.quit()
        sys.exit()
