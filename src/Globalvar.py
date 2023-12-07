import os, shutil
import sys
from selenium.common.exceptions import NoSuchElementException
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
        self.home = os.path.expanduser('~')
        self.ME_folder = '{}/MakeEntries'.format(self.home)
        self.downloadFolder = ''
        self.id = 0
        self.test = False
        self.developer = 9999999
        self.character = 9999999

        self.entriesTable = None
        self.charactersTable = None
        self.developersTable = None
        self.entryCharactersTable = None
        self.entryDevelopersTable = None

    def setTest(self, state):
        self.test = state

    def getTest(self):
        return self.test

    def getDeveloper(self):
        return self.developer

    def getCharacter(self):
        return self.character

    def setTables(self):
        self.entriesTable = 'entries' if self.test == False else 'entries_2'
        self.charactersTable = 'characters' if self.test == False else 'characters_2'
        self.developersTable = 'developers' if self.test == False else 'developers_2'
        self.entryCharactersTable = 'entry_characters' if self.test == False else 'entry_characters_2'
        self.entryDevelopersTable = 'entry_developers' if self.test == False else 'entry_developers_2'

    def addMessage(self, message, type='message', browser=None):
        message = str(message)
        self.errorMessage += message
        self.errorMessage += '\n'
        print(message)
        if type == 'error':
            browser.quit()

    def get_screen_resolution(self):
        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',shell=True, stdout=subprocess.PIPE).communicate()[0]
        resolution = output.split()[0].split(b'x')
        return [int(resolution[0]), int(resolution[1])]
    
    def setDownloadDir(self, id):
        self.downloadFolder = '{}/{}/temp'.format(self.ME_folder, id)

    def getDownloadDir(self):
        return self.downloadFolder

    def setDriver(self, driver):
        self.driver = driver

    def getDriver(self):
        return self.driver

    def getSource(self, url):
        with open('/home/erik/test.txt', 'r+') as f:
            #f.write(source)
            line = '<html>'
            nr = 1
            lines = []
            while line != '</html>':
                line = f.readline().strip('\n')
                lines.append(line)
            
            return lines
    
    def sleep(self, start, to=0):
        if to != 0:
            sleep = uniform(start, to)
        else:
            sleep = start
    
        time.sleep(sleep)
          
    def getElement(self, driver, by, value, time=0, depth=0):
        #if the element is not found after 5 iterations return 0
        if depth >= 2:
            #self.log("Can't find element '{0}', even after searching a long time".format(value))
            
            return 0
        
        element = None
        
        if by == 'id':
            #try to find the element by its id
            try:
                element = driver.find_element_by_id(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                    
        elif by == 'css':
            #try to find the element by its css
            try:
                element = driver.find_element_by_css_selector(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'xpath':
            #try to find the element by its xpath
            try:
                element = driver.find_element_by_xpath(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'tag':
            #try to find the element by its tag
            try:
                element = driver.find_element_by_tag_name(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'name':
            #try to find the element by its name
            try:
                element = driver.find_element_by_name(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'text':
            #try to find the element by link text
            try:
                element = driver.find_element_by_link_text(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'partial_text':
            #try to find the element by its partial link text
            try:
                element = driver.find_element_by_partial_link_text(value)
            
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
                
        elif by == 'class':
            #try to find the element by its value
            try:
                element = driver.find_element_by_class_name(value)
                
            except NoSuchElementException:
                #the element is not found. So set it to None
                element = None
        
        #If the element is not found. Wait a while and try again  
        if element == None: 
            
            self.sleep(time)
            
            element = self.getElement(driver, by, value, 1, depth+1)
        
        return element
    
    def getElements(self, driver, by, value, time=0, depth=0):
        #if the elements are not found after 5 iterations return 0
        if depth >= 2:
            #self.log("Can't find elements '{0}', even after searching a long time".format(value))
            
            return 0
        
        if by == 'css':
            #try to find the elements by their css
            elements = driver.find_elements_by_css_selector(value)
            
                
        elif by == 'xpath':
            #try to find the elements by their xpath
            elements = driver.find_elements_by_xpath(value)

                
        elif by == 'tag':
            #try to find the elements by their tag
            elements = driver.find_elements_by_tag_name(value)

        elif by == 'name':
            #try to find the elements by their name
            elements = driver.find_elements_by_name(value)
                
        elif by == 'text':
            #try to find the elements by their text
            elements = driver.find_elements_by_link_text(value)
            
        elif by == 'partial_text':
            #try to find the elements by their partial link text
            elements = driver.find_element_by_partial_link_text(value)
      
        elif by == 'class':
            #try to find the elements by their value
            elements = driver.find_elements_by_class_name(value)
        
        #If the elements are not found. Wait a while and try again  
        if elements == []: 
            
            self.sleep(time)
            
            elements = self.getElements(driver, by, value, 1, depth+1)
            
        #return the found elements
        return elements
    
    def makeMainDirs(self, id):
        if not os.path.isdir(self.ME_folder):
            os.makedirs(self.ME_folder, mode=0o777)
            
        if not os.path.isdir("{}/{}/temp".format(self.ME_folder, id)):
            os.makedirs("{}/{}/temp".format(self.ME_folder, id), mode=0o777)
            
        if not os.path.isdir("{}/{}".format(self.ME_folder, id)):
            os.makedirs("{}/{}".format(self.ME_folder, id), mode=0o777)
        
        if not os.path.isdir("{}/{}/samples".format(self.ME_folder, id)):
            os.makedirs("{}/{}/samples".format(self.ME_folder, id), mode=0o777)
              
        if not os.path.isdir("{}/{}/chars".format(self.ME_folder, id)):
            os.makedirs("{}/{}/chars".format(self.ME_folder, id), mode=0o777)
            
    def makeCharDir(self, id, charId):
        if not os.path.isdir("{}/{}/chars/{}".format(self.ME_folder, id, charId)):
            os.makedirs("{}/{}/chars/{}".format(self.ME_folder, id, charId), mode=0o777)

    def downloadImages(self, data, id):
        self.setDownloadDir(id)

        chars = data['chars']
        samples = data['samples']

        root = '{}/{}'.format(self.ME_folder, id)
        rootTemp = '{}/temp'.format(root)

        if data['cover1'] != '':
            self.downloadUrl(data['cover1'], '_cover_1')
            data['cover1'] = '{}/_cover_1.jpg'.format(root)
        if data['cover2'] != '':
            self.downloadUrl(data['cover2'], '_cover_2')
            data['cover2'] = '{}/_cover_2.jpg'.format(root)

        for j, char in enumerate(chars):
            img1 = ''
            img2 = ''
            jUp = j + 1

            rootChar = '{}/chars/{}'.format(root, jUp)

            self.makeCharDir(id, jUp)

            self.downloadUrl(char['img1'], '__img{}.jpg'.format(jUp))

            img1 = '{}/__img.jpg'.format(rootChar)
            if char['img2'] != '' and char['img2'].split('"')[0] != '':
                self.downloadUrl(char['img2'], 'char{}'.format(jUp))

                img2 = '{}/char.jpg'.format(rootChar)

            data['chars'][j]['img1'] = img1
            data['chars'][j]['img2'] = img2

        rootSamples = '{}/samples'.format(root)
        newSamples = []
        for i, sample in enumerate(samples):
            iUp = i + 1
            self.downloadUrl(sample, 'sample{}'.format(iUp))

            newSamples.append('{}/sample{}.jpg'.format(rootSamples, iUp))

        data['samples'] = newSamples

            
    def downloadUrl(self, url, filename):
        url = url.split('"')[0]

        if 'vndb.org' in url:
            self.addMessage('Download url: {} to: {}'.format(url, filename))

            self.sleep(0.5)

            try:
                urllib.request.urlretrieve(url, '{}/{}'.format(self.downloadFolder, filename))
                self.addMessage('Downloaded')
            except Exception as exc:
                self.addMessage(exc)

                print(type(exc))
                print(exc.args)
                print(exc)
                print(url)
                return

            return

    def convertToJpg(self, filePath, savePath):
        image = Image.open(filePath)
        image.save(savePath)

    def cleanString(self, string):
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

    def cleanFolder(self, start = 'false'):
        folder = self.ME_folder

        if start == 'true':
            path = '/var/www/html/entry_images/entries/999999'

            if os.path.isdir(path):
                self.cleanFolder(path)
                shutil.rmtree(path)

            for i in range(100):
                try:
                    path = '/var/www/html/entry_images/char/{}'.format(999901 + i)

                    if os.path.isdir(path):
                        self.cleanFolder(path)
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
