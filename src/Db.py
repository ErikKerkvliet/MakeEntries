import pymysql
import base64
import os

import logging
from tkinter import Image
import sys
import time
import traceback
import re

from sys import exit
from PIL import Image
from resizeimage import resizeimage
import sys
import time
from math import floor
from shutil import copyfile, rmtree
import subprocess

glv = None

class DB:

    def __init__(self, globalvar):
        global glv
        glv = globalvar

        glv.addMessage('Making connection with the DB')
        self.password = base64.b64decode('ZmlyZWZseQ==')
        self.root = '/var/www/html/entry_images'

        self.connection = pymysql.Connection(host="localhost", user="yuuichi_sagara", password=self.password, database="hcapital")

        if self.connection is not None:
            glv.addMessage('Connection established')

        self.rootEntries = ''
        self.rootChars = ''

    def checkDuplicate(self, title, romanji, browser):
        if glv.getTest():
            return
        romanji = "3-5-4-6-7" if romanji == '' else romanji

        title = self.checkVarForSql(title)
        romanji = self.checkVarForSql(romanji)

        # table = 'entries' if glv.getTest() == False else 'entries_2'

        query = "SELECT id as rows FROM {} WHERE type = 'game' AND (title = '{}' OR romanji = '{}')".format(glv.entriesTable, title, romanji)

        entryId = self.runQuery(query)

        if entryId != 0:
            message = 'Duplicate entry: {}'.format(entryId)
            glv.addMessage(message, 'error', browser)

            browser.quit()

    def deleteAllTestRows(self):
        queries = []
        queries.append("DELETE FROM entries_2 WHERE id > 999899")
        queries.append("DELETE FROM characters_2 WHERE id > 999899")
        queries.append("DELETE FROM developers_2 WHERE id > 999899")
        queries.append("DELETE FROM entry_characters_2 WHERE entry_id > 999899")
        queries.append("DELETE FROM characters_2 WHERE id > 999899")
        queries.append("DELETE FROM entry_developers_2 WHERE entry_id > 999899")

        for query in queries:
            self.runQuery(query)

        return True

    def connect(self, data, id):
        entryId = self.submitEntryData(data)

        print('Entry has been made: {}'.format(entryId))
        glv.addMessage('Entry has been made: {}'.format(entryId))

        for i in range(3):
            if 'developer{}'.format(i) not in data.keys() or data['developer{}'.format(i)] == '':
                break

            developer = data['developer{}'.format(i)]
            developer = self.checkVarForSql(developer)

            self.submitDevelopers(developer, entryId)

        glv.addMessage('Developers have been made.')

        self.rootEntries = '{}/entries/{}'.format(self.root, entryId)
        self.rootChars = '{}/char'.format(self.root)

        self.makeDirs('info')
        print('Directories have been created')
        glv.addMessage('Directories have been created')

        self.moveCover(data['cover'])
        print('Cover has been moved')
        glv.addMessage('Cover has been moved')

        self.moveSamples(data)
        print('Samples have been moved')
        glv.addMessage('Samples have been moved')

        self.submitCharsData(data['chars'], entryId)

        print('All characters have been made')
        glv.addMessage('All characters have been made')

        rmtree('{}/{}'.format(glv.ME_folder, id), ignore_errors=True)

        print('Temp folder has been removed')
        glv.addMessage('Temp folder has been removed')

        if glv.getTest():
            self.editSitemap(entryId)
            print('Sitemap has been edited')
            glv.addMessage('Sitemap has been edited')

        sys.exit()

    def checkVarForSql(self, var):
        if "'" in var:
            var = var.replace("'", "\\'")
        if '"' in var:
            var = var.replace('"', '\\"')

        return var

    def submitEntryData(self, data):
        data['title'] = self.checkVarForSql(data['title'])
        data['romanji'] = self.checkVarForSql(data['romanji'])
        data['developer0'] = self.checkVarForSql(data['developer0'])
        if 'developer1' in data.keys():
            data['developer1'] = self.checkVarForSql(data['developer1'])
        if 'developer2' in data.keys():
            data['developer2'] = self.checkVarForSql(data['developer2'])
        data['webpage'] = self.checkVarForSql(data['webpage'])
        data['infopage'] = self.checkVarForSql(data['infopage'])

        table = 'entries' if glv.getTest() == False else 'entries_2'

        query = "INSERT INTO {} (".format(glv.entriesTable)
        query += "id, title, romanji, released, size, website, information, "
        query += "password, type, time_type, last_edited"
        query += ") VALUES (NULL,"
        query += "'" + data['title'] + "', "
        query += "'" + data['romanji'] + "', "
        query += "'" + data['released'] + "', "
        query += "'', " #size
        query += "'" + data['webpage'] + "', "
        query += "'" + data['infopage'] + "', "
        query += "'', " #password
        query += "'app', "
        query += "'upc', "
        query += "CURRENT_TIMESTAMP()) "

        glv.addMessage('Inserting entry')

        return self.runQuery(query)

    def submitDevelopers(self, developer, entryId):
        # table = 'developers' if glv.getTest() == False else 'developers_2'

        query = "SELECT id FROM {} WHERE name = '{}' AND (type = 'game' OR type = 'app')".format(glv.developersTable, developer)

        developerId = self.runQuery(query)

        if developerId == 0 or developer == None:
            # table = 'developers' if glv.getTest() == False else 'developers_2'

            query = "INSERT INTO {}".format(glv.developersTable)
            query += " (id, name, kanji, homepage, type)"
            query += " VALUES "
            query += "(NULL, '{}', '{}', '{}', '{}')".format(developer, '', '', 'game')

            developerId = self.runQuery(query)

        # entryDevelopersTable = 'entry_developers' if glv.getTest() == False else 'entry_developers_2'

        query = "INSERT INTO {} ".format(glv.entryDevelopersTable)
        query += "(entry_id, developer_id)"
        query += " VALUES "
        query += "({}, {})".format(entryId, developerId)

        self.runQuery(query)

    def submitCharsData(self, chars, entryId):
        for i, char in enumerate(chars):
            char['name'] = self.checkVarForSql(char['name'])
            char['romanji'] = self.checkVarForSql(char['romanji'])

            # table = 'characters' if glv.getTest() == False else 'characters_2'
            idColumn = '' if glv.getTest() == False else 'id,'
            nr = 999920 + i

            query = "INSERT INTO {} ".format(glv.charactersTable)
            query += "({} name, romanji,".format(idColumn)
            query += " age, gender, height, weight, cup,"
            query += " bust, waist, hips"
            query += ") VALUES ("

            query += '' if glv.getTest() == False else '{},'.format(nr)
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

            characterEntries = False

            charId = self.runQuery(query, True)

            # table = 'entry_characters' if glv.getTest() == False else 'entry_characters_2'
            # characterTable = 'characters' if glv.getTest() == False else 'characters_2'

            query = "INSERT INTO {} (entry_id, character_id) VALUES ({}, {})".format(glv.entryCharactersTable, entryId, charId)

            result = self.runQuery(query)
            
            print('Character has been made: {}'.format(charId))
            
            self.moveChar(char, charId)
            print('Character has been moved')

    def makeDirs(self, type, path=''):
        if type == 'info':       
            if not os.path.isdir('{}'.format(self.rootEntries)):
                path = '{}'.format(self.rootEntries)
                os.makedirs(path)
                os.chmod(path, 0o777)
            if not os.path.isdir('{}/cg'.format(self.rootEntries)):
                path = '{}/cg'.format(self.rootEntries)
                os.makedirs(path)
                os.chmod(path, 0o777)
            if not os.path.isdir('{}/cover'.format(self.rootEntries)):
                path = '{}/cover'.format(self.rootEntries)
                os.makedirs(path)
                os.chmod(path, 0o777)
        elif type == 'char':
            if not os.path.isdir(path):
                path = path
                os.makedirs(path)
                os.chmod(path, 0o777)
                
    def moveCover(self, cover):
        glv.addMessage('Moving cover images')

        rootCover = '{}/cover'.format(self.rootEntries)

        saveLocation = '{}/_cover_m.jpg'.format(rootCover)

        with open(cover, 'r+b') as f:
            with Image.open(f) as image:
                self.resize(image, 320, 320, saveLocation, f)

        saveLocation = '{}/_cover_l.jpg'.format(rootCover)

        if cover != '':
            if os.path.exists(cover):
                copyfile(cover, saveLocation)

    def moveChar(self, char, charId):
        glv.addMessage('Moving character data')
        rootChar = '{}/{}'.format(self.rootChars, charId)
        
        if not os.path.isdir(rootChar):
            self.makeDirs('char', rootChar)
                          
        saveLocation = '{}/__img.jpg'.format(rootChar)

        if 'img1' in char.keys() and char['img1'] != '':
            try:
                with open(char['img1'], 'r+b') as f:
                    with Image.open(f) as image:
                        charFace = image.resize((256, 300), Image.LANCZOS)
                        charFace.save(saveLocation, image.format)
            except:
                pass
        
        try:
            if 'img2' in char.keys() and char['img2'] != '':                        
                saveLocation = '{}/char.jpg'.format(rootChar)
                
                if os.path.exists(char['img2']):
                    copyfile(char['img2'], saveLocation)
        except:
            pass
            
    def moveSamples(self, data):
        glv.addMessage('Moving sample images')

        samples = data['samples']

        rootSamples = '{}/cg'.format(self.rootEntries)

        for i, sample in enumerate(samples):
            if i > len(samples) - 4:
                saveLocation = '{}/_sample{}.jpg'.format(rootSamples, i)
            else:
                saveLocation = '{}/sample{}.jpg'.format(rootSamples, i)

            with open(sample, 'r+b') as f:
                with Image.open(f) as image:
                    if data['split'][i] != '1' and data['split'][i] != '':
                        split = int(data['split'][i])

                        height = floor(image.height / split)

                        for j in range(split):
                            jUp = j+1
                            cropped = image.crop([0, height*j, image.width, height*(jUp)])

                            saveLoc = '{}/sample{}_{}.jpg'.format(rootSamples, i, jUp)

                            glv.addMessage('Cropping sample{}.jpg'.format(i))
                            self.resize(cropped, 600, 600, saveLoc, f)
                    else:
                        self.resize(image, 600, 600, saveLocation, f)
                        
    def resize(self, image, maxX, maxY, saveLocation, filePath):
        factor = 1
        factorX = maxX / image.width
        factorY = maxY / image.height

        if factorX <= factorY:
            factor = factorX
        elif factorX > factorY: 
            factor = factorY
        if factorX > 1 and factorY > 1:
            factor = 1

        width = floor(image.width * factor)
        height = floor(image.height * factor)

        extension = saveLocation.split('.')[-1]

        if extension == 'jpg' or extension == 'jpeg':
            command = 'convert "{0}" -crop {1}x{2}+0+0 "{3}"'.format(filePath, width, height, saveLocation)

            os.system(command)

        resized = image.resize((width, height), Image.LANCZOS)
        resized.save(saveLocation, image.format)
        
    def editSitemap(self, id):
        glv.addMessage('Editing site map')

        filePath = '/var/www/html/sitemap.xml'
        
        os.system('sed -i "$ d" {0}'.format(filePath))
        
        txt = "<url>"
        txt += "<loc>http://www.hcapital.tk/?show=entry&amp;id={}</loc>".format(id)
        txt += "<changefreq>daily</changefreq>"
        txt += "<priority>0.2</priority>"
        txt += "</url>\n</urlset>"
        
        with open(filePath, 'a+') as f:
            f.write(txt)

        glv.cleanFolder()



    def runQuery(self, query, error = False):
        glv.addMessage('\n{}\n'.format(query))

        if glv.getTest():
            query = query.replace('NULL', '999999')

            print(query)

        queryType = query[0:6]

        if glv.getTest() and queryType == 'DELETE':
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()

            return

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)

                if queryType == 'INSERT':
                    self.connection.commit()

                    table = query.split(' ')[2]
                    idQuery = 'SELECT id FROM {} ORDER BY id DESC LIMIT 1'.format(table)
                    result = self.runQuery(idQuery)
                    return result
                elif queryType == 'SELECT':
                    result = cursor.fetchone()

                    return result[0]
        except Exception as e:
            glv.addMessage(e)

            if error:
                return e
            elif 'SELECT' in query:
                return 0
            exit()
