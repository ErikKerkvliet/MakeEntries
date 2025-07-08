from datetime import datetime, timedelta

import pymysql
import os
from dotenv import load_dotenv

from tkinter import Image

from PIL import Image
from math import floor
from shutil import copyfile, rmtree

load_dotenv()


class DB:

    def __init__(self, globalvar):
        self.glv = globalvar

        self.glv.log('Making connection with the DB')
        self.root = '/var/www/Hcapital/entry_images'

        self.connection = pymysql.Connection(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            database=os.getenv('DATABASE_NAME')
        )

        if self.connection is not None:
            self.glv.log('Connection established')

        self.root_entries = ''
        self.root_chars = ''

    def check_duplicate(self, title, romanji='', driver=None, entry_type='game'):
        if self.glv.get_test():
            return
        romanji = title[0:-8] if romanji == '' else romanji

        title = self.check_var_for_sql(title)
        romanji = self.check_var_for_sql(romanji)

        # table = 'entries' if self.glv.get_test() == False else 'entries_2'

        query = "SELECT id AS `rows` FROM {} WHERE type = '{}' AND (title = '{}' OR romanji = '{}')".format(
            self.glv.entries_table,
            entry_type,
            title,
            romanji
        )

        entry_id = self.run_query(query)

        if entry_id != 0:
            if driver is not None:
                message = 'Duplicate entry: {}'.format(entry_id)
                self.glv.log(message, 'error', driver)
                self.glv.quit()
            else:
                entry_data = self.get_entry_by_id(entry_id)

                series = self.get_series_by_anidb_id(entry_data[0][7])
                for entry in series:
                    if title[-7:] in entry[1]:
                        return True
                return False

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

    def connect(self, data, vndb_id, entry_id):
        self.glv.entry_id = entry_id

        self.glv.log('Entry has been made: {}'.format(entry_id))

        if 'developer1' in data.keys() and data['developer1'] != '':
            developer = data['developer1']
            developer = self.check_var_for_sql(developer)
            self.submit_developers(developer, entry_id)

        if 'developer2' in data.keys() and data['developer2'] != '':
            developer = data['developer2']
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
        data['webpage'] = self.check_var_for_sql(data['webpage'])
        data['infopage'] = self.check_var_for_sql(data['infopage'])

        query = "INSERT INTO {} (".format(self.glv.entries_table)
        query += "id, title, romanji, released, size, website, information, "
        query += "vndb_id, password, type, time_type, last_edited"
        query += ") VALUES (NULL,"
        query += "'" + data['title'] + "', "
        query += "'" + data['romanji'] + "', "
        query += "'" + data['released'] + "', "
        query += "'', "  # size
        query += "'" + data['webpage'] + "', "
        query += "'" + data['infopage'] + "', "
        query += "" + self.glv.vndb_id + ", "
        query += "'', "  # password

        query += "'" + data['type'] + "', "
        if datetime.strptime(data['released'], '%Y-%m-%d') >= datetime.now() - timedelta(days=60):
            query += "'new', "
        else:
            query += "'old', "
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

            entry_type = 'ova' if self.glv.db_label == 'anidb' else 'game'

            query = "INSERT INTO {}".format(self.glv.developers_table)
            query += " (id, name, kanji, homepage, type)"
            query += " VALUES "
            query += "(NULL, '{}', '{}', '{}', '{}')".format(developer, '', '', entry_type)

            developer_id = self.run_query(query)

        # entry_developers_table = 'entry_developers' if self.glv.get_test() == False else 'entry_developers_2'

        query = "INSERT INTO {} ".format(self.glv.entry_developers_table)
        query += "(entry_id, developer_id)"
        query += " VALUES "
        query += "({}, {})".format(entry_id, developer_id)

        self.run_query(query)

    def submit_chars_data(self, chars, entry_id):
        for i, char in enumerate(chars):
            if 'checked' not in char:
                continue

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

    def insert_entry_character(self, entry_id, char_id):
        query = "INSERT INTO {} (entry_id, character_id) VALUES ({}, {})".format(
            self.glv.entry_characters_table,
            entry_id,
            char_id
        )

        self.run_query(query)

        print('Character relation has been made. entry_id:{} char_id: {}'.format(entry_id, char_id))

    def find_characters(self, character):
        query = 'SELECT c.id AS cid, e.id AS eid, e.romanji, e.title FROM `characters` as c '
        query += 'LEFT JOIN entry_characters as ec ON ec.character_id = c.id '
        query += 'LEFT JOIN entries as e ON ec.entry_id = e.id '

        query += ' WHERE '

        if character["name"] != '':
            query += f'c.name LIKE "{character["name"]}" '

        if character["romanji"] != '':
            query += f'or c.romanji LIKE "{character["romanji"]}"'

        if character["name"] == '' and character["romanji"] == '':
            return []

        return self.run_query(query, False, True)

    def insert_entry_relation(self, entry_id, relation_id, entry_type='series'):
        query = f'INSERT INTO entry_relations (entry_id, relation_id, type) VALUES({entry_id}, {relation_id}, "{entry_type}")'
        self.run_query(query)

    def find_relation_by_anidb_id(self, anidb_id):
        query = f"""
            SELECT e.id FROM entries e
            LEFT JOIN entry_relations er ON er.entry_id = e.id
            WHERE e.type='ova' AND e.vndb_id={anidb_id} AND er.entry_id=er.relation_id
        """
        return self.run_query(query)

    def find_developer_by_anidb_id(self, anidb_id):
        query = f"""
            SELECT d.name FROM entries e
            LEFT JOIN entry_relations er ON er.entry_id = e.id
            LEFT JOIN entry_developers ed ON ed.entry_id = e.id
            LEFT JOIN developers d ON d.id = ed.developer_id
            WHERE e.vndb_id = {anidb_id} AND e.type = 'ova' AND er.entry_id = er.relation_id
        """
        return self.run_query(query)

    def get_entry_by_id(self, entry_id):
        query = f"""
            SELECT * FROM entries e WHERE e.id = {entry_id}
        """
        return self.run_query(query, fetch_all=True)

    def get_series_by_anidb_id(self, anidb_id):
        query = f"""
            SELECT * FROM entries e WHERE e.vndb_id = {anidb_id}
        """
        return self.run_query(query, fetch_all=True)

    def make_dirs(self, dir_type, path=''):
        if dir_type == 'info':
            folders = ['', 'cg', 'cover']
            for folder in folders:
                path = f'{self.root_entries}/{folder}'
                if not os.path.isdir(path):
                    os.makedirs(path, mode=0o777)

        elif dir_type == 'char':
            if not os.path.isdir(path):
                os.makedirs(path, mode=0o777)

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
        if not os.path.isfile(save_location):
            if 'img1' in char.keys() and char['img1'] != '':
                try:
                    with open(char['img1'], 'r+b') as f:
                        with Image.open(f) as image:
                            char_face = image.resize((256, 300), Image.LANCZOS)
                            char_face.save(save_location, image.format)
                except Exception as e:
                    self.glv.log(f'Error moving character image: {e}', 'error')
                    pass
        
        try:
            if 'img2' in char.keys() and char['img2'] != '':                        
                save_location = '{}/char.jpg'.format(root_char)
                
                if os.path.exists(char['img2']):
                    copyfile(char['img2'], save_location)
        except Exception as e:
            self.glv.log(f'Error moving character image: {e}', 'error')
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

    def resize(self, image, max_x, max_y, save_location, file_path):
        # Check if we should skip resizing
        if self.glv.no_resize:
            # For video captures, just save without resizing
            if 'samples' in file_path and self.glv.video_file_path is not None:
                extension = save_location.split('.')[-1]
                if extension == 'jpg' or extension == 'jpeg':
                    image.save(save_location, image.format)
                return

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

    def run_query(self, query, error=False, fetch_all=False):
        query = query.strip()
        # Log the query string for debugging or monitoring purposes
        self.glv.log('\n{}\n'.format(query))

        # If running in test mode, replace 'NULL' values in the query with '999999'
        if self.glv.get_test():
            query = query.replace('NULL', '999999')
            print(query)

        # Determine the type of query by examining the first 6 characters (e.g., 'SELECT', 'INSERT')
        query_type = query[0:6]

        # If in test mode and the query type is 'DELETE', execute the query but do not return any result
        if self.glv.get_test() and query_type == 'DELETE':
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()  # Commit DELETE operations in test mode

            return  # Return None explicitly for DELETE in test mode

        try:
            # Execute the query in a new cursor context
            with self.connection.cursor() as cursor:
                cursor.execute(query)

                # Handle 'INSERT' queries by committing and returning the last inserted id
                if query_type == 'INSERT':
                    self.connection.commit()  # Commit INSERT operations

                    # Get the name of the table from the query and select the latest inserted ID
                    table = query.split(' ')[2]
                    id_query = 'SELECT id FROM {} ORDER BY id DESC LIMIT 1'.format(table)
                    result = self.run_query(id_query)
                    return result  # Returns the latest inserted ID (int) or None if no rows

                elif query_type == 'UPDATE' or query_type == 'DELETE':
                    self.connection.commit()   # Commit UPDATE or DELETE operations

                # Handle 'SELECT' queries
                elif query_type == 'SELECT':
                    # If fetch_all is True, return all rows as a list of tuples (list of tuples)
                    if fetch_all:
                        return cursor.fetchall()  # Returns a list of tuples

                    # Otherwise, fetch only the first row
                    result = cursor.fetchone()  # Returns a single tuple or None if no result

                    # If no result or the result is empty, return 0; otherwise, return the first item in the tuple
                    return 0 if result is None or len(result) < 1 else result[0]  # Returns int, str, or 0

        except Exception as e:
            # Log the exception for debugging
            self.glv.log(e)

            # If error flag is True, return the exception object
            if error:
                return e  # Returns an Exception object

            # If the query is a 'SELECT' and fails, return 0 to indicate failure
            elif 'SELECT' in query:
                return 0  # Returns int (0) as a default for failed SELECT queries

            exit()  # Exit the program if an unhandled exception occurs
