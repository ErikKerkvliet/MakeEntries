from tkinter import Image 
import sys

import ME_scrolledFrame

glv = None

class MainUI:
    
    def exit(self):
        print('close')
        glv.addMessage('close')
        sys.exit()

        raise ValueError('Finished.')

    def __init__(self, globalvar):
        global glv
        glv = globalvar

        glv.addMessage('Making GUI')

        self.app = ME_scrolledFrame.App(glv)
        self.app.title('Make Entries v1.6 | Made by: Erik Kerkvliet')
        
        img = Image("photo", file="icon.gif")
        self.app.call('wm','iconphoto', self.app, img)
        
        self.app.geometry("1024x1024+0+0") 
        self.app.resizable(0, 0)
        
        self.app.protocol("WM_DELETE_WINDOW", lambda:self.exit())
        
    def fillData(self, data, id):
        self.app.fillData(self.app, data, id)
        
    def doLoop(self):
        self.app.mainloop()
