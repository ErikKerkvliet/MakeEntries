from Getchu import Getchu
from Vndb import Vndb
from Dlsite import DlSite
from Globalvar import Globalvar
from AskEntry import AskEntry
from MainUI import MainUI
from Links import Links
from ErrorHandler import ErrorHandler

import logging
from tkinter import Image 
import sys
import time
import re


from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Main:
    @staticmethod
    def exit():
        print('close')
        sys.exit()

    def __init__(self, app_type=''):
        self.ask_entry = None
        self.glv = Globalvar()
        self.vndb_id = None
        self.site_id = None
        logging.basicConfig(filename='{}/log.txt'.format(self.glv.app_folder), level=logging.ERROR)

        screen_resolution = self.glv.get_screen_resolution()

        if app_type == 'links':
            x_loc = screen_resolution[0] - 1300
            y_loc = screen_resolution[1] - 1200

            link = Links(self.glv)
            link.geometry(f'800x500+{x_loc}+{y_loc}')
            link.wm_attributes("-topmost", 1)
            link.protocol("WM_DELETE_WINDOW", lambda: self.exit())
            link.mainloop()

            self.exit()

        self.vndb_id = '0'
        self.site_id = '0'

        self.glv.set_test(False)
        self.glv.set_tables()
        if self.glv.get_test():
            self.glv.clean_folder('true')
            self.glv.db.delete_all_test_rows()

        vndb = Vndb(self.glv)

        x_loc = screen_resolution[0] - 820
        y_loc = screen_resolution[1] - 190

        self.glv.log('Getting entry nrs.')

        self.ask_entry = AskEntry(self, self.glv)
        self.ask_entry.title('Entry nrs.')

        self.ask_entry.geometry("170x109+{}+{}".format(x_loc, y_loc))
        self.ask_entry.wm_attributes("-topmost", 1)

        self.ask_entry.protocol("WM_DELETE_WINDOW", lambda: self.exit())

        try:
            img = Image("photo", file="icon.gif")
            self.ask_entry.call('wm', 'iconphoto', self.ask_entry, img)
        except Exception as msg:
            self.glv.log(msg)
            pass

        self.ask_entry.resizable(False, False)

        self.ask_entry.mainloop()

        self.glv.log('Url vndb: {}'.format(self.vndb_id))
        self.glv.log('Url getchu: {}'.format(self.site_id))

        if 'R' in self.site_id or 'V' in self.site_id:
            site = DlSite(self.glv)
        else:
            self.vndb_id = re.sub(r"\d+", "", self.vndb_id)
            self.site_id = re.sub(r"\d+", "", self.site_id)
            
            site = Getchu(self.glv)

        self.glv.make_main_dirs(self.vndb_id)

        prefs = {
            "download.default_directory": '{}/{}/temp'.format(self.glv.app_folder, self.vndb_id),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options = Options()
        # options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", prefs)

        self.glv.driver = webdriver.Chrome(options=options)
        # driver.set_window_size(1280, 100)

        self.glv.log('=============================================================')

        data_vndb = vndb.get_entry_data(self.glv.driver, self.vndb_id)

        if data_vndb['title'] == '' and data_vndb['romanji'] != '':
            data_vndb['title'] = data_vndb['romanji']
            data_vndb['romanji'] = ''

        self.glv.db.check_duplicate(data_vndb['title'], data_vndb['romanji'], self.glv.driver)

        chars_vndb = vndb.get_char_data()

        for char in chars_vndb['chars']:
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

        data_vndb = {**data_vndb, **chars_vndb}

        self.glv.log('')
        self.glv.log('=============================================================')

        self.glv.log('Getting site data')
        data_site = site.get_entry_data(self.glv.driver, self.site_id, self.vndb_id)

        chars = []
         
        data = {
            'title': data_vndb['title'],
            'romanji': data_vndb['romanji'],
            'developer0': data_vndb['developer0'],
            'developer1': data_vndb['developer1'],
            'developer2': data_vndb['developer2'],
            'webpage': data_vndb['webpage'],
            'infopage': data_site['infopage'],
            'cover1': data_site['cover'],
            'cover2': data_vndb['cover'],
            'released': data_site['released'],
            'samples': data_site['samples']
        }

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
        for site in data_site['chars']:
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
        
        for vndb in data_vndb['chars']:
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

        self.glv.download_images(data, self.vndb_id)
        time.sleep(2)
        import os
        from os.path import isfile, join

        root = '{}/{}'.format(self.glv.app_folder, self.vndb_id)
        root_temp = '{}/temp'.format(root)

        files = [f for f in os.listdir(root_temp) if isfile(join(root_temp, f))]

        sample_nr = 0
        move_to = ''

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
            old_file = '{}/{}.jpg'.format(root_temp, name)

            if 'package' in f or '_cover_1' in f:
                move_to = '{}/_cover_1.jpg'.format(root)

            elif '_cover_2' in f:
                old_file = '{}/{}'.format(root_temp, name)
                move_to = '{}/_cover_2.jpg'.format(root)

            elif 'sample' in f or 'table' in f:
                sample_nr += 1
                move_to = '{}/samples/sample{}.jpg'.format(root, sample_nr)

            elif 'char' in f:
                number = re.sub("[^0-9]", "", f)
                nr = int(number)
                move_to = '{}/chars/{}/char.jpg'.format(root, nr)
                self.glv.make_char_dir(self.vndb_id, nr)

            elif '__img' in f:
                number = re.sub("[^0-9]", "", f)
                nr = int(number)
                move_to = '{}/chars/{}/__img.jpg'.format(root, nr)
                self.glv.make_char_dir(self.vndb_id, nr)

            command = 'mv {} {}'.format(old_file, move_to)

            self.glv.log(command)

            try:
                if os.path.isfile(old_file):
                    os.system(command)
            except Exception as message:
                self.glv.log(message)
                continue

        root_samples = '{}/{}/samples'.format(self.glv.app_folder, self.vndb_id)
        files = [f for f in os.listdir(root_samples) if isfile(join(root_samples, f))]

        samples = []
        for f in files:
            if '_cover' not in f:
                f_path = '{}/{}'.format(root_samples, f)

                samples.append(f_path)

        data['samples'] = samples

        ui = MainUI(self.glv)

        ui.fill_data(data, self.vndb_id)
        
        ui.do_loop()


main = None
# main = Main()
# main.start()
# exit()
try:
    if len(sys.argv) == 2:
        Main(sys.argv[1])
        exit(1)
    main = Main()
except Exception as e:
    main.glv.log(e)

    resolution = main.glv.get_screen_resolution()
    loc_x = int(resolution[0] / 2) - 250
    loc_y = 100

    error = ErrorHandler()
    error.title('Action log')
    error.geometry("827x522+{}+{}".format(loc_x, loc_y))

    error.set_error_message(main.glv.errorMessage)
    error.resizable(False, False)
    error.mainloop()
