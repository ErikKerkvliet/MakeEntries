import sys
from pathlib import Path
from tkinter import PhotoImage

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
        self.app.title('Make Entries v1.7 | Made by: Erik Kerkvliet')

        icon_path = Path(__file__).parent.parent / 'images' / 'MakeEntries.png'
        if icon_path.exists():
            icon = PhotoImage(file=str(icon_path))
            self.app.wm_iconphoto(True, icon)
        
        self.app.geometry("965x822+0+0") 
        # self.app.resizable(False, False)
        
        self.app.protocol("WM_DELETE_WINDOW", lambda: self.exit())
        
    def fill_data(self, data, vndb_id):
        self.app.fill_data(self.app, data, vndb_id)
        
    def do_loop(self):
        self.app.mainloop()
