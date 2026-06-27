import logging
import subprocess
import sys
import time
import re
import os
# pyrefly: ignore [missing-import]
import undetected_chromedriver as uc

# Import custom modules
from Getchu import Getchu
from Vndb import Vndb
from AniDB import AniDB
from dlsite import DlSite
from Globalvar import Globalvar
from AskEntry import AskEntry
from MainUI import MainUI

# from ErrorHandler import ErrorHandler
from CharacterHandler import CharacterHandler


def _chrome_major_version() -> int:
    """Read the major version of the system Chrome binary."""
    for binary in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
        try:
            out = subprocess.check_output([binary, "--version"], stderr=subprocess.DEVNULL).decode()
            return int(out.strip().split()[-1].split(".")[0])
        except (FileNotFoundError, ValueError, IndexError):
            continue
    return 0


class Main:
    def __init__(self):
        self.ask_entry = None
        self.glv = Globalvar()
        self.character_handler = CharacterHandler(self.glv)
        self.vndb_id = None
        self.getchu_id = None
        self.site_id = None
        self.db_label = None
        self.site_label = None
        self.glv.set_test(False)
        self.glv.set_tables()

    def exit(self):
        print('close')
        # Closing the entry-number window quits the browser too (in multiple mode
        # it is otherwise kept open on purpose).
        try:
            if self.glv.driver is not None:
                self.glv.driver.quit()
        except Exception:
            pass
        sys.exit()

    def _close_ask_entry(self):
        """Destroy the entry-number window so the review UI is the only Tk root."""
        if self.ask_entry is not None:
            try:
                self.ask_entry.destroy()
            except Exception:
                pass
            self.ask_entry = None

    def reset_run_state(self):
        """Reset every per-run variable to its default so each multiple-mode run
        starts from a clean slate. The browser session (glv.driver) and the
        multiple flag are deliberately preserved so the same session is reused."""
        self.vndb_id = None
        self.getchu_id = None
        self.site_id = None
        self.db_label = None
        self.site_label = None

        self.glv.errorMessage = 'Start\n'
        self.glv.downloadFolder = ''
        self.glv.entry_id = None
        self.glv.vndb_id = None
        self.glv.info_site = None
        self.glv.db_site = None
        self.glv.db_label = None
        self.glv.no_resize = False
        self.glv.video_file_path = None

    def setup_logging(self):
        """Set up logging configuration"""
        os.makedirs(self.glv.app_folder, exist_ok=True)
        logging.basicConfig(filename=f'{self.glv.app_folder}/log.txt', level=logging.ERROR)

    def initialize_webdriver(self):
        """Initialize and configure the Chrome WebDriver"""
        prefs = {
            "download.default_directory": f'{self.glv.app_folder}/{self.vndb_id}/temp',
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.popups": 1,
        }
        options = uc.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", prefs)

        version = _chrome_major_version()
        self.glv.driver = uc.Chrome(options=options, version_main=version or None)
        self.glv.driver.set_window_size(1024, 768)

    def get_entry_numbers(self):
        """Get entry numbers from user input"""
        screen_resolution = self.glv.get_screen_resolution()
        x_loc = screen_resolution[0] - 820
        y_loc = screen_resolution[1] - 220

        self.glv.log('Getting entry nrs.')

        self.ask_entry = AskEntry(self, self.glv)
        self.ask_entry.title('Entry nrs.')
        self.ask_entry.geometry(f"170x140+{x_loc}+{y_loc}")
        self.ask_entry.wm_attributes("-topmost", 1)
        self.ask_entry.protocol("WM_DELETE_WINDOW", lambda: self.exit())

        self.ask_entry.resizable(False, False)
        self.ask_entry.mainloop()

        self.glv.log(f'Url vndb: {self.vndb_id}')
        self.glv.log(f'Url getchu: {self.getchu_id}')

    def process_entry_data(self):
        """Process and combine data from different sources"""

        # Initialize vndb object based on db_label
        if self.db_label == 'anidb':
            vndb = AniDB(self.glv)
        else:
            vndb = Vndb(self.glv)

        # Initialize site object based on site_label
        if self.site_label == 'dlsite':
            site = DlSite(self.glv)
            pattern = r'(VJ|RJ)\d+?(?=\.)'
            match = re.search(pattern, self.getchu_id)
            self.site_id = match.group(0) if match else self.getchu_id
        else:
            site = Getchu(self.glv)
            self.site_id = re.sub(r"\D", "", self.getchu_id)
            # For the vndb-getchu combo we grab the character images by URL
            # (download) instead of Selenium screenshots, so tell Getchu to skip
            # the character screenshots. anidb-getchu keeps the screenshots.
            if self.is_vndb_getchu():
                site.skip_char_images = True

        # Clean vndb_id to only contain numbers
        self.vndb_id = re.sub(r"\D", "", self.vndb_id)
        self.glv.vndb_id = self.vndb_id

        self.glv.make_main_dirs(self.vndb_id)

        # Get data from database source (VNDB or AniDB)
        data_vndb = vndb.get_entry_data(self.glv.driver, self.vndb_id)

        # Fix title/romanji if needed
        if data_vndb['title'] == '' and data_vndb['romanji'] != '':
            data_vndb['title'] = data_vndb['romanji']
            data_vndb['romanji'] = ''

        # Check for duplicates (skip for volume series)
        if ' Vol. ' not in data_vndb['title']:
            self.glv.db.check_duplicate(data_vndb['title'], data_vndb['romanji'], self.glv.driver)

        # Get character data
        chars_vndb = vndb.get_char_data()

        # Get data from site source (Getchu or Dlsite)
        # Pass VNDB character data to site for character matching
        data_site = site.get_entry_data(self.glv.driver, self.site_id, self.vndb_id, chars_vndb)

        return self.combine_data(data_vndb, chars_vndb, data_site)

    def combine_data(self, data_vndb, chars_vndb, data_site):
        """Combine data from VNDB and other sources"""
        data = {
            'title': data_vndb['title'] or data_vndb['romanji'],
            'romanji': data_vndb['romanji'] if data_vndb['title'] else '',
            'developer1': data_vndb['developer1'],
            'developer2': data_vndb['developer2'],
            'webpage': data_vndb['webpage'],
            'infopage': data_site['infopage'],
            'cover1': data_site['cover'] if data_site['cover'] != '' else data_vndb['cover'],
            'cover2': data_vndb['cover'],
            'released': data_site['released'],
            'samples': data_site['samples']
        }

        chars = self.combine_character_data(data_site['chars'], chars_vndb['chars'])

        # vndb-getchu: use the Getchu image URLs as the character images (they get
        # downloaded directly), and keep the VNDB portrait for side-by-side display.
        if self.is_vndb_getchu():
            for char in chars:
                if char.get('getchu_img1'):
                    char['img1'] = char['getchu_img1']
                if char.get('getchu_img2'):
                    char['img2'] = char['getchu_img2']
            data['show_vndb'] = True

        data['chars'] = self.character_handler.characters(chars)

        return data

    def is_vndb_getchu(self):
        """The VNDB + Getchu combination (not anidb-getchu, not vndb-dlsite)."""
        return self.db_label == 'vndb' and self.site_label == 'getchu'

    def combine_character_data(self, site_chars, vndb_chars):
        """Combine character data from different sources, prioritized by VNDB order"""
        chars = []

        # Use VNDB list as the base to maintain order
        for i, v_char in enumerate(vndb_chars):
            v_entry = self.create_character_entry(v_char)
            v_entry['image_id'] = i + 1
            # Preserve the VNDB portrait URL before img1 is (possibly) overwritten
            # with the Getchu image, so it can be shown alongside for comparison.
            v_entry['vndb_img1'] = v_entry.get('img1', '')
            v_name_clean = v_entry['name'].replace(' ', '').replace('　', '')

            # Match a Getchu character to this VNDB character by (cleaned) kanji
            # name only. VNDB is leading, so we never pair by list position:
            # the two sites order their characters differently, and matching by
            # position grabbed the wrong Getchu image for the name.
            for s_char in site_chars:
                s_name_clean = s_char['name'].replace(' ', '').replace('　', '')
                if v_name_clean and v_name_clean == s_name_clean:
                    # Match found — only take images from Getchu, keep all VNDB metadata
                    if s_char.get('img1', ''):
                        v_entry['img1'] = s_char['img1']
                    if s_char.get('img2', ''):
                        v_entry['img2'] = s_char['img2']
                    if s_char.get('getchu_img1', ''):
                        v_entry['getchu_img1'] = s_char['getchu_img1']
                    if s_char.get('getchu_img2', ''):
                        v_entry['getchu_img2'] = s_char['getchu_img2']
                    break

            chars.append(v_entry)

        # Add site characters that didn't match any VNDB entry
        v_names = {c['name'].replace(' ', '').replace('　', '') for c in chars}
        for s_char in site_chars:
            s_name_clean = s_char['name'].replace(' ', '').replace('　', '')
            if s_name_clean not in v_names:
                new_entry = self.create_character_entry(s_char)
                if not new_entry.get('image_id'):
                    new_entry['image_id'] = len(chars) + 1
                chars.append(new_entry)

        return chars

            
    @staticmethod
    def create_character_entry(char_data):
        """Create a character entry from given data"""
        entry = {
            'name': char_data['name'],
            'romanji': char_data.get('romanji', ''),
            'gender': char_data.get('gender', ''),
            'height': char_data.get('height', ''),
            'weight': char_data.get('weight', ''),
            'measurements': char_data.get('measurements', ''),
            'age': char_data.get('age', ''),
            'cup': char_data.get('cup', ''),
            'img1': char_data.get('img1', ''),
            'img2': char_data.get('img2', '')
        }
        
        if 'image_id' in char_data and char_data['image_id'] is not None:
            entry['image_id'] = char_data['image_id']
            
        return entry

    def park_browser(self):
        """Navigate the (now idle) browser to a neutral page.

        Called once the browser is no longer needed for scraping. The only work
        left at this point is downloading the images (via requests/urllib, not
        the browser), so we park the session on google.nl instead of leaving it
        on the scraped page.
        """
        if self.glv.driver is None:
            return
        try:
            self.glv.driver.get('https://www.google.nl')
        except Exception as exc:
            self.glv.log(f'Failed to park browser on google.nl: {exc}')

    def download_and_organize_images(self, data):
        """Download and organize images"""
        self.glv.log('Downloading images')
        self.glv.download_images(data, self.vndb_id)
        time.sleep(2)

        root = f'{self.glv.app_folder}/{self.vndb_id}'
        root_temp = f'{root}/temp'
        files = [f for f in os.listdir(root_temp) if os.path.isfile(os.path.join(root_temp, f))]

        self.organize_images(root, root_temp, files)

    def organize_images(self, root, root_temp, files):
        """Organize downloaded images into appropriate directories using standardized naming"""
        for f in files:
            old_file = os.path.join(root_temp, f)
            if not os.path.isfile(old_file):
                continue

            move_to = None
            
            # Covers
            if 'cover1' in f:
                move_to = f'{root}/_cover_1.jpg'
            elif 'cover2' in f:
                move_to = f'{root}/_cover_2.jpg'
            
            # Samples (matches sample_#.jpg)
            elif 'sample_' in f:
                match = re.search(r'sample_(\d+)', f)
                if match:
                    nr = match.group(1)
                    move_to = f'{root}/samples/sample{nr}.jpg'
            
            # VNDB portrait for side-by-side display (matches char_#_vndb.jpg)
            elif 'char_' in f and '_vndb' in f:
                match = re.search(r'char_(\d+)_vndb', f)
                if match:
                    nr = int(match.group(1))
                    self.glv.make_char_dir(self.vndb_id, nr)
                    move_to = f'{root}/chars/{nr}/vndb.jpg'

            # Characters (matches char_#_img#.jpg)
            elif 'char_' in f:
                match = re.search(r'char_(\d+)_img(\d)', f)
                if match:
                    nr = int(match.group(1))
                    img_type = match.group(2)
                    self.glv.make_char_dir(self.vndb_id, nr)
                    
                    if img_type == '1':
                        move_to = f'{root}/chars/{nr}/__img.jpg'
                    else:
                        move_to = f'{root}/chars/{nr}/charb.jpg'

            if move_to:
                # Handle AniDB specific cover swapping if needed
                if self.glv.db_label == 'anidb' and 'cover' in f:
                    # Special logic for AniDB if needed, but for now just move
                    pass

                self.move_file(old_file, move_to)
            else:
                self.glv.log(f'Unknown file in temp: {f}')

    def move_file(self, old_file, new_file, command_type='mv'):
        """Move a file from one location to another"""
        command = f'{command_type} {old_file} {new_file}'
        self.glv.log(command)
        try:
            if os.path.isfile(old_file) and not os.path.isfile(new_file):
                os.system(command)
        except Exception as message:
            self.glv.log(message)

    def update_sample_list(self, data):
        """Update the list of sample images"""
        root_samples = f'{self.glv.app_folder}/{self.vndb_id}/samples'
        files = [f for f in os.listdir(root_samples) if os.path.isfile(os.path.join(root_samples, f))]

        samples = [f'{root_samples}/{f}' for f in files if '_cover' not in f]
        data['samples'] = samples

    def start(self, app_type='', file=''):
        """Main method to start the application"""
        self.glv.file = file
        self.setup_logging()

        if app_type == 'ova':
            self.glv.no_resize = True
            self.glv.video_file_path = file

            # We still need to get the entry numbers as usual
            self.get_entry_numbers()
            self.initialize_webdriver()

            # Process data from AniDB/Getchu as normal
            data = self.process_entry_data()

            # The browser is done scraping; park it on google.nl while the
            # montage/image downloads finish, then close it below.
            self.park_browser()

            if len(sys.argv) == 3:
                # Now process the video and add it to samples
                # from Capture import Capture
                # Capture(self.glv, file)
                from VideoMontage import VideoMontageGenerator
                vmg = VideoMontageGenerator(self.glv)
                vmg.create_montage(file)

                # Update the sample list to include the generated thumbnail
                video_filename = os.path.basename(file)[:-4]
                sample_path = f'{self.glv.app_folder}/{self.vndb_id}/samples/{video_filename}.jpg'
                if os.path.exists(sample_path):
                    if not isinstance(data['samples'], list):
                        data['samples'] = []
                    data['samples'].append(sample_path)

            self.download_and_organize_images(data)
            self.update_sample_list(data)

            # Downloads are done; the browser can now be closed.
            self.glv.driver.quit()

            self._close_ask_entry()
            ui = MainUI(self.glv)
            ui.fill_data(data, self.vndb_id)
            ui.do_loop()
            return

        # Normal flow. In "multiple" mode this loops: the browser session is kept
        # open and a fresh entry-number window is shown after each entry is saved.
        while True:
            # Start each run from defaults so nothing leaks from the previous one
            # (the browser session and multiple flag are preserved).
            self.reset_run_state()

            self.get_entry_numbers()

            # Reuse the existing browser session in multiple mode; otherwise the
            # driver is None on every run and a new browser is started.
            if self.glv.driver is None:
                self.initialize_webdriver()

            data = self.process_entry_data()

            # The browser is done scraping; only image downloading remains.
            # Park it on google.nl while the downloads run.
            self.park_browser()

            self.download_and_organize_images(data)

            # Only close the browser for single runs; multiple mode keeps it open.
            if not self.glv.multiple:
                self.glv.driver.quit()

            # Close the (now disabled) entry window so the review UI is the only
            # Tk root while the user submits.
            self._close_ask_entry()

            self.update_sample_list(data)

            ui = MainUI(self.glv)
            ui.fill_data(data, self.vndb_id)
            ui.do_loop()

            # In single-run mode submit() already quit the app; this guards the
            # case where the review window was closed without quitting.
            if not self.glv.multiple:
                break


if __name__ == "__main__":
    import traceback
    import ErrorHandler

    # Start capturing terminal output so it can be shown if the app crashes.
    ErrorHandler.install()

    main = Main()
    try:
        if len(sys.argv) == 2 or len(sys.argv) == 3 and sys.argv[2] == 'ova':
            main.start(sys.argv[1])
            sys.exit(1)
        if len(sys.argv) == 3:
            main.start(sys.argv[1], sys.argv[2])
            sys.exit()

        main.start()
    except SystemExit:
        # Normal exit (the user quit) — not a crash.
        raise
    except KeyboardInterrupt:
        raise
    except Exception:
        tb_text = traceback.format_exc()
        # Mirror the traceback to the terminal as Python normally would.
        sys.stderr.write(tb_text)

        # Make sure the browser is closed before we block on the dialog.
        try:
            if main.glv.driver is not None:
                main.glv.driver.quit()
        except Exception:
            pass

        ErrorHandler.show_error_dialog(ErrorHandler.get_terminal_output(), tb_text)
        sys.exit(1)
