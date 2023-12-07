import time
import os
import os.path

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from selenium.common.exceptions import TimeoutException
from PIL import Image

glv = None


class Getchu:

    def __init__(self, globalvar):
        global glv
        glv = globalvar
        self.entryId = ''
        self.pageUrl = 'http://www.getchu.com'
        self.lines = []
        self.charNr = 0
        self.charNrs = []
        
    def find_str(self, full, sub):
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

    def getEntryData(self, driver, id, vndbId):
        glv.addMessage('')
        glv.addMessage('Getting site main data')

        data = {}
        data['released'] = '0000-00-00'
        data['cover'] = ''
        data['infopage'] = ''
        data['chars'] = []
        data['samples'] = []
        
        self.entryId = id

        driver.get('{}/soft.phtml?id={}'.format(self.pageUrl, self.entryId))
        
        source = driver.page_source
        
        if 'gc=gc">' in source:
            spans = glv.getElements(driver, 'tag', 'span')
        
        try: 
            for span in spans:
                if '[は い]' in span.text:
                    span.click()
                    break;
        except:
            pass
        
        time.sleep(2)
        
        url = '{}/soft.phtml?id={}'.format(self.pageUrl, self.entryId)
        
        delay = 5 # seconds
        try:
            myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'chara-name')))
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
         
        source = driver.page_source
        
        start = self.find_str(source, '<div class="tabletitle"> キャラクター</div>')
        subStr = source[start:]
        
        end = self.find_str(subStr, '</tbody></table>')
        subStr = subStr[:end]
        
        charTrs = subStr.split('<tr>')

        data['infopage'] = url;
        
        data['cover'] = '{}/brandnew/{}/c{}package.png'.format(self.pageUrl, self.entryId, self.entryId)
        
        a_s = glv.getElements(driver, 'tag', 'a')

        for a in a_s:
            href = a.get_attribute('href')
            if href is not None and 'start_date' in href:
                data['released'] = a.get_attribute('innerHTML')

        tables = glv.getElements(driver, 'tag', 'table')

        glv.addMessage('Getting getchu character data')

        data['chars'] = []
        for i, tr in enumerate(charTrs):
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
                img1 = self.pageUrl + img1[0] + '.png'
            
            img2 = ''
            if len(imgs) > 2:
                img2 = imgs[-1].split('.png"')
                img2 = self.pageUrl + img2[0] + '.png'
                img2 = img2.replace('_s', '')
            
            cup = ''
            if len(imgs) > 1:
                if ('カップ' in imgs[1]):
                    cup_split = imgs[1].split('カップ')[0]
                    cup = cup_split[-1]
                elif '<span>' in imgs[1]:
                    span_split = imgs[1].split('span')[1]
                    if ('（' in span_split):
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
                
            if (len(name) > 1):
                if '</charalist>' in tr:
                    name = tr.split('</charalist>')[0]
                    name = name.split('<charalist>')[-1]
                    name = self.splitNameOnParenthesis(name)
                else:    
                    if '</h2>' in name[1]:
                        name = name[1].split('</h2>')[0] 
                        name = self.splitNameOnParenthesis(name)
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
                name = name.strip(' ')
                
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


            glv.addMessage('-------------------------------------------------------------')
            glv.addMessage('Name: {}'.format(data['chars'][-1]['name']))
            glv.addMessage('Romanji: {}'.format(data['chars'][-1]['romanji']))
            glv.addMessage('Gender: {}'.format(data['chars'][-1]['gender']))
            glv.addMessage('Height: {}'.format(data['chars'][-1]['height']))
            glv.addMessage('Weight: {}'.format(data['chars'][-1]['weight']))
            glv.addMessage('Measurements: {}'.format(data['chars'][-1]['measurements']))
            glv.addMessage('Age: {}'.format(data['chars'][-1]['age']))
            glv.addMessage('Cup: {}'.format(data['chars'][-1]['cup']))
            glv.addMessage('Image 1: {}'.format(data['chars'][-1]['img1']))
            glv.addMessage('Image 2: {}'.format(data['chars'][-1]['img2']))


        data['samples'] = []

        glv.addMessage('Getting screenshot images')

        self.downloadImages(driver, vndbId)

        return data
    
    def splitNameOnParenthesis(self, name):
        name = name.split('（')[0]
        name = name.split('(')[0]
        name = name.split('「')[0]
        name = name.split('「')[0]
        name = name.split('「')[0]
        name = name.split('『')[0]
        
        return name

    def downloadImages(self, driver, id):
        script = "$('.highslide').attr('onclick', 'window.open(this)');$('.highslide').attr('onkeypress', '')"
        driver.execute_script(script)

        script = "$('.highslide').click()"
        driver.execute_script(script)

        highSlideImages = glv.getElements(driver, 'class', 'highslide')

        root = '{}/{}'.format(glv.ME_folder, id)
        rootTemp = '{}/temp'.format(root)

        glv.sleep(2)

        images = glv.getElements(driver, 'tag', 'img')
        charNr = 1
        for i, image in enumerate(images):
            src = image.get_attribute('src')
            imageName = src.split('/')[-1]

            if '_' not in imageName and 'charab' not in imageName and 'chara' in imageName:
                self.charNrs.append(charNr)
                imgName = '__img{}'.format(charNr)
                charNr += 1
                self.saveImageScreenshot(driver, rootTemp, image, imgName)

        length = len(highSlideImages)
        for i in range(0, length):
            tab = length - i
            driver.switch_to.window(driver.window_handles[tab])

            url = driver.current_url
            if '_' in url or not ('chara' in url or 'table' in url or 'package' in url or 'sample' in url):
                continue

            tabImg = glv.getElement(driver, 'tag', 'img')

            src = tabImg.get_attribute('src')

            try:
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'img')))
            except TimeoutException:
                print("Loading took too much time!")

            self.saveImageScreenshot(driver, rootTemp, tabImg)

        glv.addMessage('')

    def saveImageScreenshot(self, driver, saveLocation, image, name=''):

        if name == '':
            src = image.get_attribute('src')
            if 'charab' in src:
                imageName = 'char{}.png'.format(self.charNrs[self.charNr])
                self.charNr += 1
            else:
                imageName = src.split('/')[-1].split('.')[0] + '.png'
        else:
            imageName = name + '.png'

        location = image.location_once_scrolled_into_view

        glv.addMessage('Save: {} to: {}/'.format(imageName, saveLocation))

        size = image.size

        driver.save_screenshot(imageName)

        image = Image.open(imageName)
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        image = image.crop((left, top, right, bottom))  # defines crop points

        fullImageName = '{}/{}'.format(saveLocation, imageName)
        image.save(fullImageName, 'png')  # saves new cropped image

        count = 0
        while not os.path.isfile(fullImageName):
            time.sleep(1)
            count += 1

        if count == 5:
            input("Waiting for input.")

        newImage = fullImageName.replace('.png', '.jpg')

        count = 0
        while not os.path.isfile(fullImageName):
            time.sleep(1)
            count += 1

        if count == 5:
            input("Waiting for input.")

        command = 'convert {} {}'.format(fullImageName, newImage)
        os.system(command)

        while not os.path.isfile(newImage):
            time.sleep(1)
            count += 1

        if count == 5:
            input(newImage)

        command = 'rm {}'.format(imageName)

        os.system(command)



        # convert_img = Image.open(fullImageName)
        # bg = Image.new("RGB", convert_img.size, (255, 255, 255))
        # bg.paste(convert_img, convert_img)
        #
        # command = 'rm {}'.format(fullImageName)
        # os.system(command)
        #
        # command = 'rm {}/{}'.format(os.getcwd(), imageName)
        # os.system(command)

        # imageName = imageName.replace('.png', '.jpg')
        # command = 'convert {}/{} {}/{}'.format('/home/erik/', imageName, '/home/erik/', imageName)
        # os.system(command)
        #
        # new_image_path = fullImageName.replace('.png', '.jpg')
        # bg.save(new_image_path)
