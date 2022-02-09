import ME_getchu
import ME_vndb
import ME_dlsite
import ME_globalvar
import ME_askEntry
import ME_mainUI
import ME_errorHandler

import logging
from tkinter import Image 
import sys
import time
import traceback
import re


from selenium import webdriver
from selenium.webdriver.chrome.options import Options

glv = ME_globalvar.Globalvar()

class Main:
    
    def exit(self):
        print('close')
        sys.exit()

    def __init__(self, driver):

        self.vndbId = '0'
        self.siteId = '0'

        glv.setTest(False)
        glv.setTables()
        if glv.getTest():
            glv.cleanFolder('true')
            glv.db.deleteAllTestRows()

        vndb = ME_vndb.Vndb(glv)


        resolution = glv.get_screen_resolution()
        locX = resolution[0] - 220
        locY = resolution[1] - 190

        glv.addMessage('Getting entry nrs.')

        self.askEntry = ME_askEntry.AskEntry(self, glv)
        self.askEntry.title('Entry nrs.')

        self.askEntry.geometry("170x109+{}+{}".format(locX, locY))
        self.askEntry.wm_attributes("-topmost", 1)

        self.askEntry.protocol("WM_DELETE_WINDOW", lambda:self.exit())

        try:
            img = Image("photo", file="icon.gif")
            self.askEntry.call('wm','iconphoto', self.askEntry, img)
        except:
            pass

        self.askEntry.resizable(0, 0)

        self.askEntry.mainloop()

        glv.addMessage('Url vndb: {}'.format(self.vndbId))
        glv.addMessage('Url getchu: {}'.format(self.siteId))

        if 'R' in self.siteId or 'V' in self.siteId:
            site = ME_dlsite.DlSite(glv)
        else:
            self.vndbId = re.sub("\D", "", self.vndbId)
            self.siteId = re.sub("\D", "", self.siteId)
            
            site = ME_getchu.Getchu(glv)

        glv.makeMainDirs(self.vndbId)

        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory": '{}/{}/temp'.format(glv.ME_folder, self.vndbId),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--ignore-certificate-errors')

        driver = webdriver.Chrome(executable_path=glv.home + '/bin/chromedriver', chrome_options=options)
        # driver.set_window_size(1280, 100)

        glv.addMessage('=============================================================')

        dataVndb = vndb.getEntryData(driver, self.vndbId)

        if dataVndb['title'] == '' and dataVndb['romanji'] != '':
            dataVndb['title'] = dataVndb['romanji']
            dataVndb['romanji'] = ''

        glv.db.checkDuplicate(dataVndb['title'], dataVndb['romanji'], driver)

        charsVndb = vndb.getCharData(driver)

        for char in charsVndb['chars']:
            glv.addMessage('-------------------------------------------------------------')
            glv.addMessage('Name: {}'.format(char['name']))
            glv.addMessage('Romanji: {}'.format(char['romanji']))
            glv.addMessage('Gender: {}'.format(char['gender']))
            glv.addMessage('Height: {}'.format(char['height']))
            glv.addMessage('Weight: {}'.format(char['weight']))
            glv.addMessage('Measurements: {}'.format(char['measurements']))
            glv.addMessage('Age: {}'.format(char['age']))
            glv.addMessage('Cup: {}'.format(char['cup']))
            glv.addMessage('Image 1: {}'.format(char['img1']))

        dataVndb = {**dataVndb, **charsVndb}

        glv.addMessage('')
        glv.addMessage('=============================================================')

        glv.addMessage('Getting site data')
        dataSite = site.getEntryData(driver, self.siteId, self.vndbId)

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
                data[value] = glv.cleanString(data[value])

        glv.addMessage('Title: {}'.format(data['title']))
        glv.addMessage('Romanji: {}'.format(data['romanji']))
        glv.addMessage('Developer0: {}'.format(data['developer0']))
        glv.addMessage('Developer1: {}'.format(data['developer1']))
        glv.addMessage('Developer2: {}'.format(data['developer2']))
        glv.addMessage('Webpage: {}'.format(data['webpage']))
        glv.addMessage('Infopage: {}'.format(data['infopage']))
        glv.addMessage('Cover1: {}'.format(data['cover1']))
        glv.addMessage('Cover2: {}'.format(data['cover2']))
        glv.addMessage('released: {}'.format(data['released']))

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
                    char[value] = glv.cleanString(char[value])

            if char['img1'] == '':
                chars.remove(char)

        data['chars'] = chars

        driver.quit()

        glv.addMessage('Downloading images')

        glv.downloadImages(data, self.vndbId)
        time.sleep(2)
        import os
        from os.path import isfile, join

        root = '{}/{}'.format(glv.ME_folder, self.vndbId)
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

            glv.addMessage(command)

            try:
                if os.path.isfile(old_file):
                    os.system(command)
            except Exception as e:
                glv.addMessage(e)
                continue


        root_samples = '{}/{}/samples'.format(glv.ME_folder, self.vndbId)
        files = [f for f in os.listdir(root_samples) if isfile(join(root_samples, f))]

        samples = []
        for f in files:
            if '_cover' not in f:
                f_path = '{}/{}'.format(root_samples, f)

                samples.append(f_path)

        data['samples'] = samples

        ui = ME_mainUI.MainUI(glv)

        ui.fillData(data, self.vndbId)
        
        ui.doLoop()


driver = None
logging.basicConfig(filename='{}/log.txt'.format(glv.ME_folder), level=logging.ERROR)

try:
    main = Main(driver)
except Exception as e:
    glv.addMessage('')
    glv.addMessage(e)

    resolution = glv.get_screen_resolution()
    locX = int(resolution[0] / 2) - 250
    locY = 100

    error = ME_errorHandler.ErrorHandler()
    error.title('Action log')
    error.geometry("827x522+{}+{}".format(locX, locY))

    error.setErrorMessage(glv.errorMessage)
    error.resizable(0, 0)
    error.mainloop()

