glv = None

class DlSite:

    def __init__(self, globalvar):
        global glv
        glv = globalvar
        self.pageUrl = 'https://www.dlsite.com/maniax/work/=/product_id'
        self.entryId = ''
        
    def getEntryData(self, driver, id):
        
        print('Get dlsite main data')
        
        self.entryId = id
        data = {}
        
        driver.get('{}/{}.html'.format(self.pageUrl, self.entryId))
        
        data['cover'] = ''
        data['romanji'] = ''
        data['title'] = ''
        data['infopage'] = ''
        data['developer0'] = ''
        data['developer1'] = ''
        data['developer2'] = ''
        data['released'] = ''
        data['chars'] = []
        data['samples'] = []
        
        glv.sleep(3)
        
        siteCheck = glv.getElement(driver, 'class', 'btn_yes')
        
        if siteCheck:
            a = glv.getElement(siteCheck, 'tag', 'a')
            a.click()
        
        glv.sleep(3)
        
        data['infopage'] = '{}/{}.html'.format(self.pageUrl, self.entryId)
        
        slider = glv.getElement(driver, 'class', 'slider_items')
        
        lis = glv.getElements(slider, 'tag', 'li')
        
        for li in lis:
            img = glv.getElement(li, 'tag', 'img')
            
            if img == 0:
                continue
            
            if '_main.jpg' in img.get_attribute('src'):
                data['cover'] = img.get_attribute('src')
            else:
                data['samples'].append(img.get_attribute('src'))
                
        table = glv.getElement(driver, 'id', 'work_outline')
        
        if table:
            td = glv.getElement(table, 'tag', 'td')
            if td:
                a = glv.getElement(td, 'tag', 'a')
                if a:
                    date = a.get_attribute('innerHTML')
                    
                    date_split1 = date.split('年')
                    date_split2 = date_split1[1].split('月')
                    
                    year = date_split1[0]
                    
                    month = date_split2[0]

                    day = date_split2[1]
                    
                    data['released'] = '{}-{}-{}'.format(year, month, '26')
        
        return data
