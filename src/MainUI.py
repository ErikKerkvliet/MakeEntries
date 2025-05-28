import sys

import ScrolledFrame


class MainUI:
    
    def exit(self):
        print('close')
        self.glv.log('close')
        sys.exit()

    def __init__(self, globalvar):
        self.glv = globalvar

        self.glv.log('Making GUI')

        self.app = ScrolledFrame.App(self.glv)
        self.app.title('Make Entries v1.6 | Made by: Erik Kerkvliet')
        
        self.app.geometry("1024x1024+0+0") 
        self.app.resizable(False, False)
        
        self.app.protocol("WM_DELETE_WINDOW", lambda: self.exit())
        
    def fill_data(self, data, vndb_id):
        self.app.fill_data(self.app, data, vndb_id)
        
    def do_loop(self):
        self.app.mainloop()
