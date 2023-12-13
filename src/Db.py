import pymysql
import base64
import os

from tkinter import Image

from sys import exit
from PIL import Image
import sys
from math import floor
from shutil import copyfile, rmtree


class DB:

    def __init__(self, globalvar):
        self.glv = globalvar

        self.glv.log('Making connection with the DB')
        self.password = base64.b64decode('ZmlyZWZseQ==')
        self.root = '/var/www/Hcapital/entry_images'

        self.connection = pymysql.Connection(
            host="localhost",
            user="yuuichi_sagara",
            password=self.password,
            database="hcapital"
        )

        if self.connection is not None:
            self.glv.log('Connection established')

        self.root_entries = ''
        self.root_chars = ''

    def check_duplicate(self, title, romanji, browser):
        if self.glv.get_test():
            return
        romanji = "3-5-4-6-7" if romanji == '' else romanji

        title = self.check_var_for_sql(title)
        romanji = self.check_var_for_sql(romanji)

        # table = 'entries' if self.glv.get_test() == False else 'entries_2'

        query = "SELECT id AS `rows` FROM {} WHERE type = 'game' AND (title = '{}' OR romanji = '{}')".format(
            self.glv.entries_table,
            title,
            romanji
        )

        entry_id = self.run_query(query)

        if entry_id != 0:
            message = 'Duplicate entry: {}'.format(entry_id)
            self.glv.log(message, 'error', browser)

            browser.quit()

    def delete_all_test_rows(self):
        queries = [
            "DELETE FROM entries_2 WHERE id > 999899", "DELETE FROM characters_2 WHERE id > 999899",
            "DELETE FROM developers_2 WHERE id > 999899",
            "DELETE FROM entry_characters_2 WHERE entry_id > 999899",
            "DELETE FROM characters_2 WHERE id > 999899",
            "DELETE FROM entry_developers_2 WHERE entry_id > 999899"
        ]

        for query in queries:
            self.run_query(query)

        return True

    def connect(self, data, vndb_id):
        entry_id = self.submit_entry_data(data)
        self.glv.entry_id = entry_id

        self.glv.log('Entry has been made: {}'.format(entry_id))

        for i in range(3):
            if 'developer{}'.format(i) not in data.keys() or data['developer{}'.format(i)] == '':
                break

            developer = data['developer{}'.format(i)]
            developer = self.check_var_for_sql(developer)

            self.submit_developers(developer, entry_id)

        self.glv.log('Developers have been made.')

        self.root_entries = '{}/entries/{}'.format(self.root, entry_id)
        self.root_chars = '{}/char'.format(self.root)

        self.make_dirs('info')
        self.glv.log('Directories have been created')

        self.move_cover(data['cover'])
        self.glv.log('Cover has been moved')

        self.move_samples(data)
        self.glv.log('Samples have been moved')

        self.submit_chars_data(data['chars'], entry_id)

        self.glv.log('All characters have been made')

        rmtree('{}/{}'.format(self.glv.app_folder, vndb_id), ignore_errors=True)

        self.glv.log('Temp folder has been removed')

        if self.glv.get_test():
            self.edit_sitemap(entry_id)
            print('Sitemap has been edited')
            self.glv.log('Sitemap has been edited')

        sys.exit()

    @staticmethod
    def check_var_for_sql(var):
        if "'" in var:
            var = var.replace("'", "\\'")
        if '"' in var:
            var = var.replace('"', '\\"')

        return var

    def submit_entry_data(self, data):
        data['title'] = self.check_var_for_sql(data['title'])
        data['romanji'] = self.check_var_for_sql(data['romanji'])
        data['developer0'] = self.check_var_for_sql(data['developer0'])
        if 'developer1' in data.keys():
            data['developer1'] = self.check_var_for_sql(data['developer1'])
        if 'developer2' in data.keys():
            data['developer2'] = self.check_var_for_sql(data['developer2'])
        data['webpage'] = self.check_var_for_sql(data['webpage'])
        data['infopage'] = self.check_var_for_sql(data['infopage'])

        query = "INSERT INTO {} (".format(self.glv.entries_table)
        query += "id, title, romanji, released, size, website, information, "
        query += "password, type, time_type, last_edited"
        query += ") VALUES (NULL,"
        query += "'" + data['title'] + "', "
        query += "'" + data['romanji'] + "', "
        query += "'" + data['released'] + "', "
        query += "'', "  # size
        query += "'" + data['webpage'] + "', "
        query += "'" + data['infopage'] + "', "
        query += "'', "  # password
        query += "'app', "
        query += "'upc', "
        query += "CURRENT_TIMESTAMP()) "

        self.glv.log('Inserting entry')

        return self.run_query(query)

    def submit_developers(self, developer, entry_id):
        # table = 'developers' if self.glv.get_test() == False else 'developers_2'

        query = "SELECT id FROM {} WHERE name = '{}' AND (type = 'game' OR type = 'app')".format(
            self.glv.developers_table,
            developer
        )

        developer_id = self.run_query(query)

        if developer_id == 0 or developer is None:
            # table = 'developers' if self.glv.get_test() == False else 'developers_2'

            query = "INSERT INTO {}".format(self.glv.developers_table)
            query += " (id, name, kanji, homepage, type)"
            query += " VALUES "
            query += "(NULL, '{}', '{}', '{}', '{}')".format(developer, '', '', 'game')

            developer_id = self.run_query(query)

        # entry_developers_table = 'entry_developers' if self.glv.get_test() == False else 'entry_developers_2'

        query = "INSERT INTO {} ".format(self.glv.entry_developers_table)
        query += "(entry_id, developer_id)"
        query += " VALUES "
        query += "({}, {})".format(entry_id, developer_id)

        self.run_query(query)

    def submit_chars_data(self, chars, entry_id):
        for i, char in enumerate(chars):
            char['name'] = self.check_var_for_sql(char['name'])
            char['romanji'] = self.check_var_for_sql(char['romanji'])

            # table = 'characters' if self.glv.get_test() == False else 'characters_2'
            id_column = '' if not self.glv.get_test() else 'id,'
            nr = 999920 + i

            query = "INSERT INTO {} ".format(self.glv.characters_table)
            query += "({} name, romanji,".format(id_column)
            query += " age, gender, height, weight, cup,"
            query += " bust, waist, hips"
            query += ") VALUES ("

            query += '' if not self.glv.get_test() else '{},'.format(nr)
            query += "'" + char['name'] + "', "
            query += "'" + char['romanji'] + "', "
            query += "'" + char['age'] + "', "
            query += "'" + char['gender'] + "', "

            height = ''
            weight = ''
            bust = ''
            waist = ''
            hip = ''

            if char['height'] != '':
                height = char['height'].strip('cm')
            if char['weight'] != '':
                weight = char['weight'].strip('kg')
            if char['measurements'] != '':
                sizes = char['measurements'].strip('cm').strip(' ')
                sizes_split = sizes.split('-')

                bust = sizes_split[0]
                waist = sizes_split[1]
                hip = sizes_split[2]

            query += "'" + height + "', "
            query += "'" + weight + "', "
            query += "'" + char['cup'] + "', "
            query += "'" + bust + "', "
            query += "'" + waist + "', "
            query += "'" + hip + "')"

            char_id = self.run_query(query, True)

            # table = 'entry_characters' if self.glv.get_test() == False else 'entry_characters_2'
            # characterTable = 'characters' if self.glv.get_test() == False else 'characters_2'

            query = "INSERT INTO {} (entry_id, character_id) VALUES ({}, {})".format(
                self.glv.entry_characters_table,
                entry_id,
                char_id
            )

            self.run_query(query)
            
            print('Character has been made: {}'.format(char_id))
            
            self.move_char(char, char_id)
            print('Character has been moved')

    def make_dirs(self, dir_type, path=''):
        if dir_type == 'info':
            if not os.path.isdir('{}'.format(self.root_entries)):
                path = '{}'.format(self.root_entries)
                os.makedirs(path)
                os.chmod(path, 0o7777)
            if not os.path.isdir('{}/cg'.format(self.root_entries)):
                path = '{}/cg'.format(self.root_entries)
                os.makedirs(path)
                os.chmod(path, 0o7777)
            if not os.path.isdir('{}/cover'.format(self.root_entries)):
                path = '{}/cover'.format(self.root_entries)
                os.makedirs(path)
                os.chmod(path, 0o7777)
        elif dir_type == 'char':
            if not os.path.isdir(path):
                path = path
                os.makedirs(path)
                os.chmod(path, 0o7777)
                
    def move_cover(self, cover):
        self.glv.log('Moving cover images')

        root_cover = '{}/cover'.format(self.root_entries)

        save_location = '{}/_cover_m.jpg'.format(root_cover)

        with open(cover, 'r+b') as f:
            with Image.open(f) as image:
                self.resize(image, 320, 320, save_location, cover)

        save_location = '{}/_cover_l.jpg'.format(root_cover)

        if cover != '':
            if os.path.exists(cover):
                copyfile(cover, save_location)

    def move_char(self, char, char_id):
        self.glv.log('Moving character data')
        root_char = '{}/{}'.format(self.root_chars, char_id)
        
        if not os.path.isdir(root_char):
            self.make_dirs('char', root_char)
                          
        save_location = '{}/__img.jpg'.format(root_char)

        if 'img1' in char.keys() and char['img1'] != '':
            try:
                with open(char['img1'], 'r+b') as f:
                    with Image.open(f) as image:
                        char_face = image.resize((256, 300), Image.LANCZOS)
                        char_face.save(save_location, image.format)
            except:
                pass
        
        try:
            if 'img2' in char.keys() and char['img2'] != '':                        
                save_location = '{}/char.jpg'.format(root_char)
                
                if os.path.exists(char['img2']):
                    copyfile(char['img2'], save_location)
        except:
            pass
            
    def move_samples(self, data):
        self.glv.log('Moving sample images')

        samples = data['samples']

        root_samples = '{}/cg'.format(self.root_entries)

        for i, sample in enumerate(samples):
            if i > len(samples) - 4:
                save_location = '{}/_sample{}.jpg'.format(root_samples, i)
            else:
                save_location = '{}/sample{}.jpg'.format(root_samples, i)

            with open(sample, 'r+b') as f:
                with Image.open(f) as image:
                    if data['split'][i] != '1' and data['split'][i] != '':
                        split = int(data['split'][i])

                        height = floor(image.height / split)

                        for j in range(split):
                            j_up = j+1
                            cropped = image.crop([0, height * j, image.width, height * j_up])

                            save_loc = '{}/sample{}_{}.jpg'.format(root_samples, i, j_up)

                            self.glv.log('Cropping sample{}.jpg'.format(i))
                            self.resize(cropped, 600, 600, save_loc, sample)
                    else:
                        self.resize(image, 600, 600, save_location, sample)

    @staticmethod
    def resize(image, max_x, max_y, save_location, file_path):
        factor = 1
        factor_x = max_x / image.width
        factor_y = max_y / image.height

        if factor_x <= factor_y:
            factor = factor_x
        elif factor_x > factor_y: 
            factor = factor_y
        if factor_x > 1 and factor_y > 1:
            factor = 1

        width = floor(image.width * factor)
        height = floor(image.height * factor)

        extension = save_location.split('.')[-1]

        if extension == 'jpg' or extension == 'jpeg':
            command = 'convert "{0}" -crop {1}x{2}+0+0 "{3}"'.format(file_path, width, height, save_location)

            os.system(command)

        resized = image.resize((width, height), Image.LANCZOS)
        resized.save(save_location, image.format)
        
    def edit_sitemap(self, entry_id):
        self.glv.log('Editing site map')

        file_path = '/var/www/Hcapital/sitemap.xml'
        
        os.system('sed -i "$ d" {0}'.format(file_path))
        
        txt = "<url>"
        txt += "<loc>http://www.hcapital.tk/?show=entry&amp;id={}</loc>".format(entry_id)
        txt += "<changefreq>daily</changefreq>"
        txt += "<priority>0.2</priority>"
        txt += "</url>\n</urlset>"
        
        with open(file_path, 'a+') as f:
            f.write(txt)

        self.glv.clean_folder()

    def run_query(self, query, error=False):
        self.glv.log('\n{}\n'.format(query))

        if self.glv.get_test():
            query = query.replace('NULL', '999999')

            print(query)

        query_type = query[0:6]

        if self.glv.get_test() and query_type == 'DELETE':
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()

            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)

                if query_type == 'INSERT':
                    self.connection.commit()

                    table = query.split(' ')[2]
                    id_query = 'SELECT id FROM {} ORDER BY id DESC LIMIT 1'.format(table)
                    result = self.run_query(id_query)
                    return result
                elif query_type == 'SELECT':
                    result = cursor.fetchone()

                    return 0 if result is None or len(result) < 1 else result[0]
        except Exception as e:
            self.glv.log(e)

            if error:
                return e
            elif 'SELECT' in query:
                return 0
            exit()
