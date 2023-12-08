import re


class Vndb:
    
    def __init__(self, globalvar):
        self.glv = globalvar
        self.pageUrl = 'https://vndb.org'
        self.entryId = ''
        
    def get_entry_data(self, driver, id):
        self.glv.log('')
        self.glv.log('Getting vndb main data')

        self.entryId = id
        data = {}
        
        driver.get('{}/v{}'.format(self.pageUrl, self.entryId))
        
        data['cover'] = ''
        data['romanji'] = ''
        data['title'] = ''
        data['webpage'] = ''
        data['developer0'] = ''
        data['developer1'] = ''
        data['developer2'] = ''
        data['chars'] = []
        
        cover = self.glv.get_elements('class', 'vnimg')
        
        if cover != 0:
            cover = self.glv.getElement(cover[0], 'tag', 'img')

            data['cover'] = cover.get_attribute('src')

        self.glv.log('Cover vndb: {}'.format(data['cover']))

        details = self.glv.get_element('class', 'vndetails')

        romanjiTitle = self.glv.get_elements('tag', 'h1')
        
        data['romanji'] =  romanjiTitle[1].get_attribute('innerHTML')

        self.glv.log('Romanji title: {}'.format(data['romanji']))

        title = self.glv.get_element('class', 'alttitle')
        
        if title != 0:
            data['title'] = title.get_attribute('innerHTML')

        self.glv.log('Original title: {}'.format(data['title']))

        tds = self.glv.getElements(details, 'tag', 'td')
        
        next = False
        titleNext = False
        for td in tds:
            if next:
                dev_split = td.get_attribute('innerHTML').split(' & ')
                for i, dev in enumerate(dev_split):
                    developer = dev.split('>')
                    data['developer{}'.format(i)] = developer[1][:-3]

                    self.glv.log('Develover {}: {}'.format(i, data['developer{}'.format(i)]))

                break
            
            if titleNext:
                data['title'] = td.get_attribute('innerHTML')

            if 'Developer' == td.get_attribute('innerHTML'):
                next = True
                
            if title == 0 and 'Original title' == td.get_attribute('innerHTML'):
                titleNext = True
            

        self.options = ['download edition', 'package edition', 'regular edition', 'first press edition', 'premium edition']

        data['webpage'] = self.getOfficialWebsite(driver, self.options, data['title'], data['romanji'])

        if data['webpage'] == None:
            data['webpage'] = ''

        self.glv.log('Webpage: {}'.format(data['webpage']))
                
        return data
     
    def get_char_data(self, driver):
        self.glv.log('')
        self.glv.log('Getting character data')

        data = {}
        driver.get('{}/v{}/chars#chars'.format(self.pageUrl, self.entryId))  
       
        theads = self.glv.get_elements('tag', 'thead')
        tds = self.glv.get_elements('tag', 'td')
       
        data['chars'] = []
        count = 0
        
        if theads != 0:
            for thead in theads:

                data['chars'].append([])
                
                data['chars'][count] = {}
                
                data['chars'][count]['name'] = ''
                data['chars'][count]['romanji'] = ''
                data['chars'][count]['height'] = ''
                data['chars'][count]['weight'] = ''
                data['chars'][count]['measurements'] = ''
                data['chars'][count]['cup'] = ''
                data['chars'][count]['gender'] = ''
                data['chars'][count]['age'] = ''
                data['chars'][count]['img1'] = ''
                data['chars'][count]['img2'] = ''
                
                romanji = self.glv.getElement(thead, 'tag', 'a')
                
                data['chars'][count]['romanji'] = romanji.get_attribute('innerHTML')

                name = self.glv.getElement(thead, 'tag', 'small')
                if name != 0:
                    nameStr = name.get_attribute('innerHTML')
                    data['chars'][count]['name'] = nameStr.replace('　', ' ')
                elif data['chars'][count]['romanji'] != '':
                    data['chars'][count]['name'] = data['chars'][count]['romanji']
                    data['chars'][count]['romanji'] = ''

                gender = self.glv.getElement(thead, 'tag', 'abbr')
                
                if gender != 0:
                    genderType = gender.get_attribute('title')
                
                    if genderType == 'Female':
                        gender = 'female'
                    elif genderType == 'Male':
                        gender = 'male'
                    elif genderType == 'Both':
                        gender = 'both'
                    else:
                        gender = 'unknown'
                else:
                    gender = 'unknown'
                        
                data['chars'][count]['gender'] = gender
                
                count += 1
                
            measureNext = False
            bodyNext = False
            hasMeasurement = False
            count = 0
            if tds != 0:
                for td in tds:
                    if measureNext:
                        measure = td.get_attribute('innerHTML').lower()
                        
                        measurements = measure.split(',')
                        if 'height' in measure:
                            for measurement in measurements:
                                if 'height:' in measurement:
                                    splitted = measurement.split(':')
                                    height = splitted[1].strip(' ')
                                    
                                    data['chars'][count]['height'] = height

                                    measurements.remove(measurement)
                                    break
                                
                        if 'weight' in measure:
                            for measurement in measurements:
                                if 'weight:' in measurement:
                                    splitted = measurement.split(':')
                                    weight = splitted[1].strip(' ')
                                                               
                                    data['chars'][count]['weight'] = weight

                                    measurements.remove(measurement)
                                    break
                        
                        if 'bust' in measure:
                            for measurement in measurements:
                                if 'bust' in measurement:
                                    splitted = measurement.split(':')
                                    sizes = splitted[1].strip('bust-waist-hips').strip(' ')
                                    
                                    data['chars'][count]['measurements'] = sizes

                                    measurements.remove(measurement)
                                    break
                                 
                        count += 1
                        measureNext = False
                        hasMeasurement = True
                    if bodyNext:
                        body = td.get_attribute('innerHTML')
                        cup = ''
                        if 'Cup' in body:
                            body_split = body.split('Cup')[0]
                            cup_split = body_split.split('Cup')
                            cup = cup_split[0].split('>')[-1].strip(' ')
                        if hasMeasurement:
                            data['chars'][count-1]['cup'] = cup
                        else:
                            data['chars'][count]['cup'] = cup
                            hasMeasurement = False
                            count += 1

                        bodyNext = False
                        
                    if td.get_attribute('innerHTML') == 'Measurements':
                        measureNext = True
                    if '>Body<' in td.get_attribute('innerHTML'):
                        bodyNext = True
                        
            charimgs = self.glv.get_elements('class', 'charimg')
            count = 0
            for div in charimgs:
                data['chars'][count]['img1'] = ''
                
                img_img = self.glv.getElement(div, 'tag', 'img')
                if img_img != 0:
                    img = img_img.get_attribute('src')
                    data['chars'][count]['img1'] = img

                count += 1
                
            divs = self.glv.get_elements('class', 'chardesc')
            count = 0
    
            if divs != 0 and len(charimgs) == len(divs):
                for div in divs:
                    text = div.get_attribute('innerHTML')
                    
                    data['chars'][count]['age'] = ''
                    data['chars'][count]['cup'] = ''
                    cup_split = []
                    if 'Cup size: ' in text:
                        cup_split = text.split('Cup size: ')
                    elif 'Cup size:' in text:
                        cup_split = text.split('Cup size:')
                    elif 'Cup size' in text:
                        cup_split = text.split('Cup size')
                    elif 'Cup: ' in text:
                        cup_split = text.split('Cup:')
                    elif 'Cup ' in text:
                        cup_split = text.split('Cup ')
                        
                    age_split = []
                    if 'Age: ' in text:
                        age_split = text.split('Age: ')
                    elif 'Age:' in text:
                        age_split = text.split('Age:')
                    elif 'Age' in text:
                        age_split = text.split('Age')
                    elif 'years old' in text:
                        age = text.split('years old')[0].strip(' ')
                        
                    if len(cup_split) > 1:   
                        cup = cup_split[1].split('<')[0].strip(' ')
                        
                        data['chars'][count]['cup'] = cup

                    if len(age_split) > 1: 
                        age = age_split[1][0:5]
                        age = re.sub("\D", "", age)  
                        
                        data['chars'][count]['age'] = age

                    count +=1
                     
        return data
    
    def getOfficialWebsite(self, driver, options, title, romanji):
        releases = self.glv.get_element('class', 'releases')
        webpage = ''

        if releases == 0:
            return '' 
         
        trs = self.glv.getElements(releases, 'tag', 'tr')

        link = ''
        lang = False
        if trs == 0:
            return ''

        for tr in trs:
            if tr == trs[-1]:
                self.options = []

            abbrs = self.glv.getElements(tr, 'tag', 'abbr')

            icons = 0
            for abbr in abbrs:
                if "complete" == abbr.get_attribute('title') or "windows" == abbr.get_attribute('title').lower():
                    icons += 1
            
            if icons != 2: 
                continue

            tc4 = self.glv.getElement(tr, 'class', 'tc4')
            if tc4 != 0:  
                a = self.glv.getElement(tc4, 'tag', 'a')

                text = a.get_attribute('innerHTML').lower()
                for option in options:
                    if option in text:
                        options = options.remove(option)
                        link = a.get_attribute('href')     
                        break
                
                str = a.get_attribute('title')
                inner_html = a.get_attribute('innerHTML')
                if link == '' and ((str == title) or (inner_html == romanji)):
                    link = a.get_attribute('href')   
            
            if link == '':
                continue

            driver.get(link)

            links = self.glv.get_elements('tag', 'a')
                
            for link in links:
                if link.get_attribute('innerHTML') == 'Official website':
                    webpage = link.get_attribute('href')
                    break

            if webpage == '':
                if not options:
                    options = self.options
                    if not options:
                        return ''

                webpage = self.getOfficialWebsite(driver, options, title, romanji)

            return webpage
