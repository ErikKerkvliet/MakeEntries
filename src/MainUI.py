from tkinter import Image 
import sys

import ScrolledFrame

self.glv = None

class MainUI:
    
    def exit(self):
        print('close')
        self.glv.addMessage('close')
        sys.exit()

        raise ValueError('Finished.')

    def __init__(self, globalvar):
        self.glv = globalvar

        self.glv.addMessage('Making GUI')

        self.app = ScrolledFrame.App(self.glv)
        self.app.title('Make Entries v1.6 | Made by: Erik Kerkvliet')
        
        img = Image("photo", file="icon.gif")
        self.app.call('wm','iconphoto', self.app, img)
        
        self.app.geometry("1024x1024+0+0") 
        self.app.resizable(False, False)
        
        self.app.protocol("WM_DELETE_WINDOW", lambda:self.exit())
        
    def fillData(self, data, id):
        self.app.fillData(self.app, data, id)
        
    def doLoop(self):
        self.app.mainloop()
