from Getchu import Getchu
from Vndb import Vndb
from Dlsite import DlSite
from Globalvar import Globalvar
from AskEntry import AskEntry
from MainUI import MainUI
from ErrorHandler import ErrorHandler

import logging
from tkinter import Image 
import sys
import time
import traceback
import re


from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Main:
    
    def exit(self):
        print('close')
        sys.exit()

    def __init__(self, driver):
        self.glv = Globalvar()
        self.glv.driver = driver
        logging.basicConfig(filename='{}/log.txt'.format(self.glv.app_folder), level=logging.ERROR)

    def start(self):
        self.vndbId = '46979'
        self.siteId = '273165'

        self.glv.set_test(False)
        self.glv.set_tables()
        if self.glv.get_test():
            self.glv.clean_folder('true')
            self.glv.db.delete_all_test_rows()

        vndb = Vndb(self.glv)


        resolution = self.glv.get_screen_resolution()
        locX = resolution[0] - 220
        locY = resolution[1] - 190

        self.glv.log('Getting entry nrs.')

        # self.askEntry = AskEntry(self, self.glv)
        # self.askEntry.title('Entry nrs.')
        #
        # self.askEntry.geometry("170x109+{}+{}".format(locX, locY))
        # self.askEntry.wm_attributes("-topmost", 1)
        #
        # self.askEntry.protocol("WM_DELETE_WINDOW", lambda:self.exit())
        #
        # try:
        #     img = Image("photo", file="icon.gif")
        #     self.askEntry.call('wm','iconphoto', self.askEntry, img)
        # except:
        #     pass
        #
        # self.askEntry.resizable(False, False)
        #
        # self.askEntry.mainloop()

        self.glv.log('Url vndb: {}'.format(self.vndbId))
        self.glv.log('Url getchu: {}'.format(self.siteId))

        if 'R' in self.siteId or 'V' in self.siteId:
            site = DlSite(self.glv)
        else:
            self.vndbId = re.sub("\D", "", self.vndbId)
            self.siteId = re.sub("\D", "", self.siteId)
            
            site = Getchu(self.glv)

        self.glv.make_main_dirs(self.vndbId)

        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory": '{}/{}/temp'.format(self.glv.app_folder, self.vndbId),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--ignore-certificate-errors')

        self.glv.driver = webdriver.Chrome(options=options)
        # driver.set_window_size(1280, 100)

        self.glv.log('=============================================================')

        dataVndb = vndb.get_entry_data(self.glv.driver, self.vndbId)

        if dataVndb['title'] == '' and dataVndb['romanji'] != '':
            dataVndb['title'] = dataVndb['romanji']
            dataVndb['romanji'] = ''

        self.glv.db.check_duplicate(dataVndb['title'], dataVndb['romanji'], self.glv.driver)

        charsVndb = vndb.get_char_data(self.glv.driver)

        for char in charsVndb['chars']:
            self.glv.log('-------------------------------------------------------------')
            self.glv.log('Name: {}'.format(char['name']))
            self.glv.log('Romanji: {}'.format(char['romanji']))
            self.glv.log('Gender: {}'.format(char['gender']))
            self.glv.log('Height: {}'.format(char['height']))
            self.glv.log('Weight: {}'.format(char['weight']))
            self.glv.log('Measurements: {}'.format(char['measurements']))
            self.glv.log('Age: {}'.format(char['age']))
            self.glv.log('Cup: {}'.format(char['cup']))
            self.glv.log('Image 1: {}'.format(char['img1']))

        dataVndb = {**dataVndb, **charsVndb}

        self.glv.log('')
        self.glv.log('=============================================================')

        self.glv.log('Getting site data')
        dataSite = site.get_entry_data(self.glv.driver, self.siteId, self.vndbId)

        chars = []
         
        data = {}
        data['title'] = dataVndb['title']
        data['romanji'] = dataVndb['romanji']
        data['developer0'] = dataVndb['developer0']
        data['developer1'] = dataVndb['developer1']
        data['developer2'] = dataVndb['developer2']
        data['webpage'] = dataVndb['webpage']
        data['infopage'] = dataSite['infopage']
        data['cover1'] = dataSite['cover']
        data['cover2'] = dataVndb['cover']
        data['released'] = dataSite['released']
        data['samples'] = dataSite['samples']

        for value in data:
            if isinstance(data[value], str):
                data[value] = self.glv.clean_string(data[value])

        self.glv.log('Title: {}'.format(data['title']))
        self.glv.log('Romanji: {}'.format(data['romanji']))
        self.glv.log('Developer0: {}'.format(data['developer0']))
        self.glv.log('Developer1: {}'.format(data['developer1']))
        self.glv.log('Developer2: {}'.format(data['developer2']))
        self.glv.log('Webpage: {}'.format(data['webpage']))
        self.glv.log('Infopage: {}'.format(data['infopage']))
        self.glv.log('Cover1: {}'.format(data['cover1']))
        self.glv.log('Cover2: {}'.format(data['cover2']))
        self.glv.log('released: {}'.format(data['released']))

        done = []
        for site in dataSite['chars']:
            chars.append({})
            name = site['name'].replace(' ', '').replace('　', '')
            done.append(name)
            chars[-1]['name'] = site['name']
            chars[-1]['romanji'] = site['romanji'] or ''
            chars[-1]['gender'] = site['gender'] or ''
            chars[-1]['height'] = site['height'] or ''
            chars[-1]['weight'] = site['weight'] or ''
            chars[-1]['measurements'] = site['measurements'] or ''
            chars[-1]['age'] = site['age'] or ''
            chars[-1]['cup'] = site['cup'] or ''                              
            chars[-1]['img1'] = site['img1']
            chars[-1]['img2'] = site['img2']   
        
        for vndb in dataVndb['chars']:
            name = vndb['name'].replace(' ', '').replace('　', '')
            if name not in done:
                chars.append({})
                done.append(name)
                chars[-1]['name'] = vndb['name']
                chars[-1]['romanji'] = vndb['romanji']
                chars[-1]['gender'] = vndb['gender']
                chars[-1]['height'] = vndb['height']
                chars[-1]['weight'] = vndb['weight']
                chars[-1]['measurements'] = vndb['measurements']
                chars[-1]['age'] = vndb['age']
                chars[-1]['cup'] = vndb['cup']                              
                chars[-1]['img1'] = vndb['img1']
                chars[-1]['img2'] = ''
            else:
                index = done.index(name)
                
                chars[index]['name'] = vndb['name']
                chars[index]['romanji'] = vndb['romanji']
                chars[index]['gender'] = vndb['gender']
                chars[index]['height'] = vndb['height']
                chars[index]['weight'] = vndb['weight']
                chars[index]['measurements'] = vndb['measurements']
                chars[index]['age'] = vndb['age']
                chars[index]['cup'] = chars[index]['cup'] or vndb['cup']                                     
            
        for char in chars:
            for value in char:
                if isinstance(char[value], str):
                    char[value] = self.glv.clean_string(char[value])

            if char['img1'] == '':
                chars.remove(char)

        data['chars'] = chars

        self.glv.driver.quit()

        self.glv.log('Downloading images')

        self.glv.download_images(data, self.vndbId)
        time.sleep(2)
        import os
        from os.path import isfile, join

        root = '{}/{}'.format(self.glv.app_folder, self.vndbId)
        rootTemp = '{}/temp'.format(root)

        files = [f for f in os.listdir(rootTemp) if isfile(join(rootTemp, f))]

        sampleNr = 0
        moveTo = ''

        nrs = []
        for f in files:
            if 'chara' in f:
                nr = f.split('__img')[-1].split('.')[0]
                if nr.isdigit() and int(nr) not in nrs:
                    nrs.append(int(nr))

        nrs.sort()

        for f in files:
            if '.png' in f:
                continue

            name = f.replace('.jpg', '')
            old_file = '{}/{}.jpg'.format(rootTemp, name)

            if 'package' in f or '_cover_1' in f:
                moveTo = '{}/_cover_1.jpg'.format(root)

            elif '_cover_2' in f:
                old_file = '{}/{}'.format(rootTemp, name)
                moveTo = '{}/_cover_2.jpg'.format(root)

            elif 'sample' in f or 'table' in f:
                sampleNr += 1
                moveTo = '{}/samples/sample{}.jpg'.format(root, sampleNr)

            elif 'char' in f:
                number = re.sub("[^0-9]", "", f)
                nr = int(number)
                moveTo = '{}/chars/{}/char.jpg'.format(root, nr)

            elif '__img' in f:
                number = re.sub("[^0-9]", "", f)
                nr = int(number)
                moveTo = '{}/chars/{}/__img.jpg'.format(root, nr)

            command = 'mv {} {}'.format(old_file, moveTo)

            self.glv.log(command)

            try:
                if os.path.isfile(old_file):
                    os.system(command)
            except Exception as e:
                self.glv.log(e)
                continue

        root_samples = '{}/{}/samples'.format(self.glv.app_folder, self.vndbId)
        files = [f for f in os.listdir(root_samples) if isfile(join(root_samples, f))]

        samples = []
        for f in files:
            if '_cover' not in f:
                f_path = '{}/{}'.format(root_samples, f)

                samples.append(f_path)

        data['samples'] = samples

        ui = MainUI(self.glv)

        ui.fill_data(data, self.vndbId)
        
        ui.do_loop()


driver = None
main = None
main = Main(driver)
main.start()
exit()
# try:
#     main = Main(driver)
#     main.start()
# except Exception as e:
#     main.glv.log('')
#     main.glv.log(e)
#
#     resolution = main.glv.get_screen_resolution()
#     locX = int(resolution[0] / 2) - 250
#     locY = 100
#
#     error = ErrorHandler()
#     error.title('Action log')
#     error.geometry("827x522+{}+{}".format(locX, locY))
#
#     error.set_error_message(main.glv.errorMessage)
#     error.resizable(False, False)
#     error.mainloop()
