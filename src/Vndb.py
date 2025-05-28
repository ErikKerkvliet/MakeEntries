import re


class Vndb:

    def __init__(self, globalvar):
        self.glv = globalvar
        self.pageUrl = 'https://vndb.org'
        self.entry_id = ''
        self.options = []

    def get_entry_data(self, driver, entry_id):
        self.glv.log('')
        self.glv.log('Getting vndb main data')

        self.entry_id = entry_id
        data = {}

        driver.get('{}/v{}'.format(self.pageUrl, self.entry_id))

        data['cover'] = ''
        data['romanji'] = ''
        data['title'] = ''
        data['webpage'] = ''
        data['developer1'] = ''
        data['developer2'] = ''
        data['chars'] = []

        cover = self.glv.get_elements('class', 'vnimg')

        if cover != 0:
            cover = self.glv.get_element_old(cover[0], 'tag', 'img')

            data['cover'] = cover.get_attribute('src') if cover != 0 else ''

        self.glv.log('Cover vndb: {}'.format(data['cover']))

        details = self.glv.get_element('class', 'vndetails')

        romanji_title = self.glv.get_elements('tag', 'h1')

        data['romanji'] = romanji_title[1].get_attribute('innerHTML')

        self.glv.log('Romanji title: {}'.format(data['romanji']))

        title = self.glv.get_element('class', 'alttitle')

        if title != 0:
            data['title'] = title.get_attribute('innerHTML')

        self.glv.log('Original title: {}'.format(data['title']))

        tds = self.glv.get_elements_old(details, 'tag', 'td')

        next_td = False
        title_next = False
        for td in tds:
            if next_td:
                dev_split = td.get_attribute('innerHTML').split(' & ')
                for i in range(len(dev_split)):
                    j = i + 1
                    developer = dev_split[i].split('>')
                    data['developer{}'.format(j)] = developer[1][:-3]

                    self.glv.log('Developer {}: {}'.format(j, data['developer{}'.format(j)]))

                break

            if title_next:
                data['title'] = td.get_attribute('innerHTML')

            if 'Developer' == td.get_attribute('innerHTML'):
                next_td = True

            if title == 0 and 'Original title' == td.get_attribute('innerHTML'):
                title_next = True

        self.options = [
            'download edition',
            'package edition',
            'regular edition',
            'first press edition',
            'premium edition'
        ]

        data['webpage'] = self.get_official_website(driver, self.options, data['title'], data['romanji'])

        if data['webpage'] is None:
            data['webpage'] = ''

        self.glv.log('Webpage: {}'.format(data['webpage']))

        return data

    def get_char_data(self):
        self.glv.log('')
        self.glv.log('Getting character data')

        data = {}
        url = f'{self.pageUrl}/v{self.entry_id}/chars#chars'
        self.glv.driver.get(url)

        theads = self.glv.get_elements('tag', 'thead')
        char_details = self.glv.get_elements('class', 'chardetails')

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

                romanji = self.glv.get_element_old(thead, 'tag', 'a')

                data['chars'][count]['romanji'] = romanji.get_attribute('innerHTML')

                name = self.glv.get_element_old(thead, 'tag', 'small')
                if name != 0:
                    name_str = name.get_attribute('innerHTML')
                    name_text = name_str.replace('　', ' ')
                    data['chars'][count]['name'] = re.sub(r'<[^>]+>', '', name_text)
                elif data['chars'][count]['romanji'] != '':
                    name_text = data['chars'][count]['romanji']
                    data['chars'][count]['name'] = re.sub(r'<[^>]+>', '', name_text)
                    data['chars'][count]['romanji'] = ''

                gender = self.glv.get_element_old(thead, 'tag', 'abbr')

                if gender != 0:
                    gender_type = gender.get_attribute('title')

                    if 'Female' in gender_type:
                        gender = 'female'
                    elif 'Male' in gender_type:
                        gender = 'male'
                    elif 'Both' in gender_type:
                        gender = 'both'
                    else:
                        gender = 'unknown'
                else:
                    gender = 'unknown'

                data['chars'][count]['gender'] = gender

                count += 1

            measure_next = False
            body_next = False
            has_measurement = False
            count = 0
            if char_details != 0:
                for details in char_details:
                    tds = self.glv.get_element_in_element(details, 'tag', 'td')
                    for td in tds:
                        if measure_next:
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
                            measure_next = False
                            has_measurement = True
                        if body_next:
                            body = td.get_attribute('innerHTML')
                            cup = ''
                            if 'Cup' in body:
                                body_split = body.split('Cup')[0]
                                cup_split = body_split.split('Cup')
                                cup = cup_split[0].split('>')[-1].strip(' ')
                            if has_measurement:
                                data['chars'][count - 1]['cup'] = cup
                            else:
                                data['chars'][count]['cup'] = cup
                                has_measurement = False

                            body_next = False

                        if td.get_attribute('innerHTML') == 'Measurements':
                            measure_next = True
                        if '>Body<' in td.get_attribute('innerHTML'):
                            body_next = True
                    count += 1

            charimgs = self.glv.get_elements('class', 'charimg')
            count = 0
            for div in charimgs:
                data['chars'][count]['img1'] = ''

                img_img = self.glv.get_element_old(div, 'tag', 'img')
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

                    if len(cup_split) > 1:
                        cup = cup_split[1].split('<')[0].strip(' ')

                        data['chars'][count]['cup'] = cup

                    if len(age_split) > 1:
                        age = age_split[1][0:5]
                        age = re.sub(r"\D", "", age)

                        data['chars'][count]['age'] = age

                    count += 1

        return data

    def get_official_website(self, driver, options, title, romanji):
        releases = self.glv.get_element('class', 'releases')
        webpage = ''

        if releases == 0:
            return ''

        trs = self.glv.get_elements_old(releases, 'tag', 'tr')

        link = ''
        if trs == 0:
            return ''

        for tr in trs:
            if tr == trs[-1]:
                self.options = []

            abbrs = self.glv.get_elements_old(tr, 'tag', 'abbr')

            icons = 0
            for abbr in abbrs:
                if "complete" == abbr.get_attribute('title') or "windows" == abbr.get_attribute('title').lower():
                    icons += 1

            if icons != 2:
                continue

            tc4 = self.glv.get_element_old(tr, 'class', 'tc4')
            if tc4 != 0:
                a = self.glv.get_element_old(tc4, 'tag', 'a')

                text = a.get_attribute('innerHTML').lower()
                for option in options:
                    if option in text:
                        options = options.remove(option)
                        link = a.get_attribute('href')
                        break

                title_str = a.get_attribute('title')
                inner_html = a.get_attribute('innerHTML')
                if link == '' and ((title_str == title) or (inner_html == romanji)):
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

                webpage = self.get_official_website(driver, options, title, romanji)

            return webpage
