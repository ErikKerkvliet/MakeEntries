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
        self.getchu_to_vndb_index = {}  # Maps Getchu char index to VNDB char index

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

    def get_entry_data(self, web_driver, getchu_id, vndb_id, chars_vndb=None):
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
                    url = span.get_attribute('href')
                    web_driver.get(url)
                    element = web_driver.find_element(By.XPATH, f"//a[contains(@href, '{url}')]")
                    web_driver.execute_script("arguments[0].click();", element)
                    break
        except Exception as e:
            print("Error clicking on 'はい' span:", e)
            pass

        time.sleep(3)

        js = 'var el = document.getElementById("buyee-bcSection"); if (el) el.remove();'
        web_driver.execute_script(js)

        url = '{}/soft.phtml?id={}'.format(self.page_url, self.getchu_id)

        delay = 5  # seconds
        try:
            WebDriverWait(web_driver, delay).until(ec.presence_of_element_located((By.CLASS_NAME, 'chara-name')))
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
         
        source = web_driver.page_source

        start = self.find_str(source, '<table border="0" style="width: 100%;padding: 5px;">')
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

        self.get_character_data(char_trs, data, chars_vndb)

        data['samples'] = []
        self.data = data

        # if 'anidb' in self.glv.db_label:
        #     return data

        self.glv.log('Getting screenshot images')

        self.download_images(web_driver, vndb_id)

        return data

    def get_character_data(self, char_trs, data, chars_vndb=None):
        self.glv.log('Getting getchu character data')
        
        # Build VNDB character name lookup (kanji names) with indices
        vndb_name_map = {}  # Maps clean name -> (vndb_char, vndb_index)
        if chars_vndb and 'chars' in chars_vndb:
            for vndb_index, vndb_char in enumerate(chars_vndb['chars']):
                index = vndb_index
                if vndb_char.get('img', '') == '':
                    index -= 1
                    continue

                # Store both the original name and a cleaned version for matching
                kanji_name = vndb_char.get('name', '')
                if kanji_name:
                    # Clean version: remove all spaces and special characters for matching
                    clean_name = kanji_name.replace(' ', '').replace('　', '')
                    vndb_name_map[clean_name] = (vndb_char, index)
                    self.glv.log(f'VNDB character {index + 1} for matching: {kanji_name} (clean: {clean_name})')
        
        getchu_char_index = 0
        for i, tr in enumerate(char_trs):
            if i == 0:
                continue

            # Extract all src attributes from this row using regex
            all_srcs = re.findall(r'src="([^"]+)"', tr)

            # Find the main character portrait: chara{N}.jpg (no 'b', no '_s')
            img1_src = None
            getchu_img_id = None
            for src in all_srcs:
                m = re.search(r'chara(\d+)\.(jpg|png)$', src)
                if m and 'charab' not in src:
                    img1_src = src
                    getchu_img_id = m.group(1)
                    break

            # Find the alternate/body image: charab{N}.jpg (without _s thumbnail suffix)
            img2_src = None
            for src in all_srcs:
                if 'charab' in src and '_s' not in src:
                    img2_src = src
                    break
            # If only the thumbnail _s version exists, strip the suffix
            if img2_src is None:
                for src in all_srcs:
                    if 'charab' in src:
                        img2_src = src.replace('_s', '')
                        break

            img1 = (self.page_url + img1_src) if img1_src else ''
            img2 = (self.page_url + img2_src) if img2_src else ''

            # Skip rows that have no character image and no character name
            has_chara_name = 'class="chara-name"' in tr
            if not img1_src and not has_chara_name:
                continue

            data['chars'].append([])
            data['chars'][-1] = {}

            # Remove query params
            if img1:
                img1 = img1.split('?')[0]
            if img2:
                img2 = img2.split('?')[0]

            cup = ''
            if 'カップ' in tr:
                cup_split = tr.split('カップ')[0]
                cup = cup_split[-1]
            elif '<span>' in tr:
                span_split = tr.split('span')[1]
                if '（' in span_split:
                    cup_split = span_split.split('（')[-1]
                    cup = cup_split[0]
            elif '<b>' in tr and 'font' not in tr:
                b_split = tr.split('<b>')[1]
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

            # Extract name from <h4 class="chara-name">...</h4> using regex
            name = ''
            name_match = re.search(r'class="chara-name">(.*?)</h4>', tr, re.DOTALL)
            if name_match:
                raw = name_match.group(1)
                # Strip all HTML tags (e.g. <span class="bootstrap">)
                name = re.sub(r'<[^>]+>', '', raw)
                # Normalise whitespace and full-width spaces
                name = name.replace('\u3000', ' ').replace('\n', '').strip()
                # Remove CV info: "CV：..." or "CV:..."
                name = re.split(r'CV\s*[:：]', name, flags=re.IGNORECASE)[0].strip()
                # Remove reading in parentheses: （よみ） or (yomi)
                name = re.sub(r'[(\uff08].*?[)\uff09]', '', name).strip()
                # Remove trailing punctuation/dashes
                name = name.rstrip('－-― \n\t')

            name = name.replace('<strong>', '').replace('</strong>', '')
            
            # Try to match with VNDB character
            clean_name_for_match = name.replace(' ', '').replace('　', '')
            matched_vndb_data = vndb_name_map.get(clean_name_for_match)
            
            if matched_vndb_data:
                matched_vndb_char, vndb_index = matched_vndb_data
                # Map Getchu character index to VNDB character index (1-based)
                vndb_char_nr = vndb_index + 1
                self.getchu_to_vndb_index[getchu_char_index + 1] = vndb_char_nr
                if getchu_img_id:
                    self.nrs[getchu_img_id] = vndb_char_nr
                self.glv.log(f'✓ Matched Getchu character {getchu_char_index + 1} (ID: {getchu_img_id}) "{name}" with VNDB #{vndb_char_nr} "{matched_vndb_char.get("name", "")}"')
            else:
                # No match found, use sequential numbering
                vndb_char_nr = getchu_char_index + 1
                self.getchu_to_vndb_index[getchu_char_index + 1] = vndb_char_nr
                if getchu_img_id:
                    self.nrs[getchu_img_id] = vndb_char_nr
                self.glv.log(f'✗ No VNDB match found for Getchu character {getchu_char_index + 1} (ID: {getchu_img_id}) "{name}" - falling back to #{vndb_char_nr}')
            
            getchu_char_index += 1
            
            root = '{}/{}'.format(self.glv.app_folder, self.glv.vndb_id)
            img1_local = '{}/chars/{}/__img.jpg'.format(root, vndb_char_nr)
            
            data['chars'][-1]['name'] = name
            data['chars'][-1]['image_id'] = vndb_char_nr
            data['chars'][-1]['romanji'] = ''
            data['chars'][-1]['age'] = ''
            data['chars'][-1]['cup'] = cup
            data['chars'][-1]['measurements'] = ''
            data['chars'][-1]['height'] = ''
            data['chars'][-1]['weight'] = ''
            data['chars'][-1]['gender'] = 'female'
            data['chars'][-1]['img1'] = img1_local # Use local path
            data['chars'][-1]['img2'] = '' # Will be reconstructed as char.jpg
            data['chars'][-1]['getchu_img1'] = img1.split('"')[0] # Store original URL just in case
            data['chars'][-1]['getchu_img2'] = img2.split('"')[0]

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
        script = "document.querySelectorAll('.highslide').forEach(el => { el.setAttribute('onclick', 'window.open(this); return false;'); el.removeAttribute('onkeypress'); });"
        driver.execute_script(script)
        if 'anidb' in self.glv.db_label:
            script = "var el = document.querySelector('.highslide'); if (el) el.click();"
            driver.execute_script(script)
            high_slide_indices = [0]
        else:
            script = "document.querySelectorAll('.highslide').forEach(el => el.click());"
            driver.execute_script(script)
            # Find all elements with class highslide
            high_slide_elements = self.glv.get_elements('class', 'highslide')
            high_slide_indices = list(range(len(high_slide_elements)))

        root = '{}/{}'.format(self.glv.app_folder, vndb_id)
        root_temp = '{}/temp'.format(root)

        self.glv.sleep(2)

        # Handle character screenshots from the main page
        images = self.glv.get_elements('tag', 'img')
        for image in images:
            src = image.get_attribute('src')
            if not src:
                continue
            image_name = src.split('/')[-1]

            if '_' not in image_name and 'charab' not in image_name and 'chara' in image_name:
                nr_match = re.search(r'chara(\d+)', image_name)
                if nr_match:
                    nr = nr_match.group(1)
                    vndb_char_nr = self.nrs.get(nr)
                    if vndb_char_nr:
                        img_name = 'char_{}_img1'.format(vndb_char_nr)
                        self.glv.log(f'Saving character screenshot: Getchu ID {nr} -> VNDB nr {vndb_char_nr}')
                        self.save_image_screenshot(driver, root_temp, image, img_name)

        # Handle highslide images (samples and covers)
        window_handles = driver.window_handles
        # The first handle is the main window, others are opened highslide images
        sample_nr = 1
        for i, handle in enumerate(window_handles[1:], 1):
            driver.switch_to.window(handle)
            url = driver.current_url
            
            # Identify what kind of image this is
            if 'anidb.net' in self.glv.db_label and 'package' not in url:
                continue

            name = ''
            if 'package' in url:
                name = 'cover1'
            elif 'sample' in url or 'table' in url:
                name = 'sample_{}'.format(sample_nr)
                sample_nr += 1
            elif 'chara' in url:
                nr_match = re.search(r'chara[b]?(\d+)', url)
                if nr_match:
                    nr = nr_match.group(1)
                    vndb_char_nr = self.nrs.get(nr)
                    if vndb_char_nr:
                        name = 'char_{}_img2'.format(vndb_char_nr)

            if name:
                try:
                    WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.TAG_NAME, 'img')))
                    tab_img = self.glv.get_element('tag', 'img')
                    if tab_img != 0:
                        self.save_image_screenshot(driver, root_temp, tab_img, name)
                except TimeoutException:
                    self.glv.log(f"Timeout waiting for image in {url}")
            
            # Close the current highslide window after processing
            driver.close()
        
        # Switch back to the main window
        driver.switch_to.window(window_handles[0])

        self.glv.log('')

    def save_image_screenshot(self, driver, save_location, image, name=''):
        if name == '':
            src = image.get_attribute('src')
            if not src:
                return
            name = src.split('/')[-1].split('.')[0]
        
        image_name = f"{name}.png"
        full_png_path = os.path.join(save_location, image_name)
        full_jpg_path = full_png_path.replace('.png', '.jpg')

        self.glv.log(f'Save: {image_name} to: {save_location}/')

        # Wait for image to be fully loaded
        try:
            WebDriverWait(driver, 10).until(
                lambda d: image.get_attribute('complete') == 'true' and 
                          image.size['width'] > 0 and 
                          image.size['height'] > 0
            )
        except Exception as e:
            self.glv.log(f'Warning: Image may not be fully loaded: {e}')

        location = image.location_once_scrolled_into_view
        size = image.size

        # Take screenshot of the whole page first
        # Note: In Headless mode or some setups, this might be tricky, but we assume it works here
        driver.save_screenshot(full_png_path)

        # Crop the screenshot to the image
        img = Image.open(full_png_path)
        img_width, img_height = img.size
        
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        
        # Clamp coordinates
        left = max(0, min(left, img_width))
        top = max(0, min(top, img_height))
        right = max(0, min(right, img_width))
        bottom = max(0, min(bottom, img_height))
        
        if right <= left or bottom <= top:
            self.glv.log(f'Warning: Invalid crop region for {image_name}, skipping')
            if os.path.exists(full_png_path): os.remove(full_png_path)
            return
        
        img = img.crop((left, top, right, bottom))
        img.save(full_png_path, 'png')

        # Convert to JPG using PIL instead of system 'convert' for portability and speed
        try:
            rgb_img = img.convert('RGB')
            rgb_img.save(full_jpg_path, 'JPEG', quality=95)
            self.glv.log(f'Saved: {full_jpg_path}')
        except Exception as e:
            self.glv.log(f'Error converting {image_name} to jpg: {e}')
        finally:
            if os.path.exists(full_png_path):
                os.remove(full_png_path)



