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
            data['cover'] = data['cover'].replace('.t', '')

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

        url = f'{self.pageUrl}/v{self.entry_id}/chars#chars'
        self.glv.driver.get(url)
        data = self.parse_char_data()

        # VNDB sometimes serves an anti-bot / "enable cookies" interstitial when a
        # deep link is opened as the first request from a fresh session; that page
        # has no character markup. If we got nothing, warm up the session by
        # visiting the main entry page first, then retry the chars page once.
        if not data['chars']:
            self.glv.log('No characters found — warming up session and retrying')
            self.glv.driver.get(f'{self.pageUrl}/v{self.entry_id}')
            self.glv.sleep(2)
            self.glv.driver.get(url)
            self.glv.sleep(1)
            data = self.parse_char_data()

        if not data['chars']:
            self.glv.log(f'WARNING: VNDB returned 0 characters for v{self.entry_id}. '
                         f'The entry may genuinely have no characters, or VNDB blocked '
                         f'the request. Check {self.pageUrl}/v{self.entry_id}/chars')

        return data

    def parse_char_data(self):
        """Parse character data from whatever page is currently loaded in the
        driver. Split out from get_char_data so the same parsing can run on a
        saved chars-page HTML (loaded via file://) without hitting the network."""
        data = {}

        char_details = self.glv.get_elements('class', 'chardetails')

        data['chars'] = []

        if char_details == 0:
            return data

        for details in char_details:

            char = {
                'name': '',
                'romanji': '',
                'height': '',
                'weight': '',
                'measurements': '',
                'cup': '',
                'gender': '',
                'age': '',
                'img1': '',
                'img2': '',
            }

            # --- Name, romanji, gender from thead ---
            thead = self.glv.get_element_old(details, 'tag', 'thead')
            if thead != 0:
                romanji_el = self.glv.get_element_old(thead, 'tag', 'a')
                if romanji_el != 0:
                    char['romanji'] = romanji_el.get_attribute('innerHTML')

                name_el = self.glv.get_element_old(thead, 'tag', 'small')
                if name_el != 0:
                    name_str = name_el.get_attribute('innerHTML')
                    name_text = name_str.replace('\u3000', ' ')
                    char['name'] = re.sub(r'<[^>]+>', '', name_text).strip()
                elif char['romanji'] != '':
                    char['name'] = re.sub(r'<[^>]+>', '', char['romanji']).strip()
                    char['romanji'] = ''

                gender_el = self.glv.get_element_old(thead, 'tag', 'abbr')
                if gender_el != 0:
                    gender_type = gender_el.get_attribute('title')
                    if 'Female' in gender_type:
                        char['gender'] = 'female'
                    elif 'Male' in gender_type:
                        char['gender'] = 'male'
                    elif 'Both' in gender_type:
                        char['gender'] = 'both'
                    else:
                        char['gender'] = 'unknown'
                else:
                    char['gender'] = 'unknown'

            # --- Image from charimg div ---
            charimg_div = self.glv.get_element_old(details, 'class', 'charimg')
            if charimg_div != 0:
                img_el = self.glv.get_element_old(charimg_div, 'tag', 'img')
                if img_el != 0:
                    img_src = img_el.get_attribute('src')
                    # Convert thumbnail URL (t.vndb.org/ch.t/...) to full URL (t.vndb.org/ch/...)
                    img_src = img_src.replace('/ch.t/', '/ch/')
                    char['img1'] = img_src

            # --- Measurements, age, cup from table rows ---
            tds = self.glv.get_element_in_element(details, 'tag', 'td')
            measure_next = False
            age_next = False
            for td in tds:
                inner = td.get_attribute('innerHTML')

                if measure_next:
                    measure_lower = inner.lower()

                    # Extract height (e.g. "Height: 165cm")
                    h_match = re.search(r'height:\s*(\d+\s*cm)', measure_lower)
                    if h_match:
                        char['height'] = h_match.group(1).strip()

                    # Extract weight (e.g. "Weight: 52kg")
                    w_match = re.search(r'weight:\s*(\d+\s*kg)', measure_lower)
                    if w_match:
                        char['weight'] = w_match.group(1).strip()

                    # Extract BWH measurements (e.g. "Bust-Waist-Hips: 103-69-93cm")
                    bwh_match = re.search(r'bust-waist-hips:\s*(\d+-\d+-\d+\s*cm)', measure_lower)
                    if bwh_match:
                        char['measurements'] = bwh_match.group(1).strip()

                    # Extract cup size from Measurements cell (e.g. "J cup")
                    cup_match = re.search(r'\b([A-Za-z]{1,3})\s+cup\b', inner, re.IGNORECASE)
                    if cup_match:
                        char['cup'] = cup_match.group(1).upper()

                    measure_next = False

                if age_next:
                    age_text = re.sub(r'\D', '', inner[:10])
                    if age_text:
                        char['age'] = age_text
                    age_next = False

                if inner == 'Measurements':
                    measure_next = True
                if inner == 'Age':
                    age_next = True

            data['chars'].append(char)

            self.glv.log('-------------------------------------------------------------')
            self.glv.log('Name: {}'.format(char['name']))
            self.glv.log('Romanji: {}'.format(char['romanji']))
            self.glv.log('Gender: {}'.format(char['gender']))
            self.glv.log('Height: {}'.format(char['height']))
            self.glv.log('Weight: {}'.format(char['weight']))
            self.glv.log('Measurements: {}'.format(char['measurements']))
            self.glv.log('Age: {}'.format(char['age']))
            self.glv.log('Cup: {}'.format(char['cup']))
            self.glv.log('Image: {}'.format(char['img1']))

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
