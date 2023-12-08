
class DlSite:

    def __init__(self, globalvar):
        self.glv = globalvar
        self.pageUrl = 'https://www.dlsite.com/maniax/work/=/product_id'
        self.entryId = ''
        
    def get_entry_data(self, driver, entry_id):
        
        print('Get dlsite main data')
        
        self.entryId = entry_id
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
        
        self.glv.sleep(3)
        
        site_check = self.glv.get_element('class', 'btn_yes')
        
        if site_check:
            a = self.glv.get_element_old(site_check, 'tag', 'a')
            a.click()
        
        self.glv.sleep(3)
        
        data['infopage'] = '{}/{}.html'.format(self.pageUrl, self.entryId)
        
        slider = self.glv.get_element('class', 'slider_items')
        
        lis = self.glv.get_elements_old(slider, 'tag', 'li')
        
        for li in lis:
            img = self.glv.get_element_old(li, 'tag', 'img')
            
            if img == 0:
                continue
            
            if '_main.jpg' in img.get_attribute('src'):
                data['cover'] = img.get_attribute('src')
            else:
                data['samples'].append(img.get_attribute('src'))
                
        table = self.glv.get_element('id', 'work_outline')
        
        if table:
            td = self.glv.get_element_old(table, 'tag', 'td')
            if td:
                a = self.glv.get_element_old(td, 'tag', 'a')
                if a:
                    date = a.get_attribute('innerHTML')
                    
                    date_split1 = date.split('年')
                    date_split2 = date_split1[1].split('月')
                    
                    year = date_split1[0]
                    
                    month = date_split2[0]
                    
                    data['released'] = '{}-{}-{}'.format(year, month, '26')
        
        return data
