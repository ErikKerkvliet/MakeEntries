import re
from tkinter import *
import pyperclip


class AskEntry(Tk):

    def __init__(self, parent, globalvar, *args, **kwargs):
        self.glv = globalvar

        root = Tk.__init__(self, *args, **kwargs)

        self.root = root
        self.parent = parent

        self.site_label = 'getchu'
        self.db_label = 'vndb'

        self.getchu_label = Label(root, text='Getchu:', width=40, height=20, anchor=NW)
        self.vndb_label = Label(root, text='VNDB:', width=40, height=20, anchor=NW)
         
        self.getchu_label.place(x=5, y=10, width=79)
        self.vndb_label.place(x=5, y=45, width=79)
         
        self.getchu_entry = Entry(root, font=("Calibri", 9))
        self.vndb_entry = Entry(root, font=("Calibri", 9))
         
        self.getchu_entry.place(x=80, y=5, width=85, height=30)
        self.vndb_entry.place(x=80, y=40, width=85, height=30)

        self.getchu_label.bind("<Button-1>", lambda event: self.paste_from_clipboard(self.getchu_entry))
        self.vndb_label.bind("<Button-1>", lambda event: self.paste_from_clipboard(self.vndb_entry))

        self.add_binds(self.getchu_entry)
        self.add_binds(self.vndb_entry)
         
        self.button = Button(root, text='Start', command=self.return_enry_nrs)
        self.button.place(x=5, y=75, width=160, height=30)
                 
    def return_enry_nrs(self):
        if self.getchu_entry.get() == '' or self.vndb_entry.get() == '':
            return

        self.parent.getchu_id = self.getchu_entry.get()
        self.parent.vndb_id = self.vndb_entry.get()

        self.parent.db_label = self.db_label
        self.glv.db_label = self.db_label
        self.parent.site_label = self.site_label

        self.glv.info_site = self.parent.getchu_id
        self.glv.db_site = self.parent.vndb_id

        self.parent.ask_entry.destroy()
        
    def add_binds(self, parent):
        parent.bind('<Button-3>', self.r_clicker, add='')
        parent.bind('<KP_Enter>', self.enter)
        parent.bind('<Return>', self.enter)
        parent.bind('<Control-a>', self.callback)
        
    def callback(self, event):
        event.widget.after(50, self.select_all, event.widget)

    @staticmethod
    def select_all(widget):
        widget.select_range(0, 'end')
        widget.icursor('end')

    @staticmethod
    def r_clicker(e):
        try:
            def r_click_copy(event):
                event.widget.event_generate('<Control-c>')
    
            def r_click_cut(event):
                event.widget.event_generate('<Control-x>')
    
            def r_click_paste(event):
                event.widget.event_generate('<Control-v>')
    
            e.widget.focus()
    
            nclst = [
                   (' Copy', lambda event=e: r_click_copy(e)),
                   (' Paste', lambda event=e: r_click_paste(e)),
                   (' Cut', lambda event=e: r_click_cut(e)),
                   ]
    
            rmenu = Menu(None, tearoff=0, takefocus=0)
    
            for (txt, cmd) in nclst:
                rmenu.add_command(label=txt, command=cmd)
    
            rmenu.tk_popup(e.x_root, e.y_root+10, entry="0")
    
        except TclError:
            print(' - rClick menu, something wrong')
            pass
    
        return "break"

    def enter(self, e):
        self.return_enry_nrs()

    def paste_from_clipboard(self, element):
        self.get_value_set_label(element)

    def get_value_set_label(self, element):
        site_id = ''
        entry = None
        if 'dlsite.com' in pyperclip.paste():
            self.getchu_label.config(text="Dlsite:")
            self.site_label = 'dlsite'
            site_id = pyperclip.paste().split('id/')[-1].split('/')[0].split('.')[0] + '.'
            entry = self.getchu_entry
        if 'getchu.com' in pyperclip.paste():
            self.getchu_label.config(text="Getchu:")
            self.site_label = 'getchu'
            site_id = re.sub(r"\D", "", pyperclip.paste().split('/')[-1])
            entry = self.getchu_entry
        if 'anidb.net' in pyperclip.paste():
            self.vndb_label.config(text="AniDb:")
            self.db_label = 'anidb'
            site_id = pyperclip.paste().split('/')[-1]
            entry = self.vndb_entry
        if 'vndb.org' in pyperclip.paste():
            self.vndb_label.config(text="VNDB:")
            self.db_label = 'vndb'
            site_id = re.search(r'vndb\.org/(v\d+)', pyperclip.paste()).group(1)
            entry = self.vndb_entry

        if entry is not None:
            entry.delete(0, END)
            entry.insert(END, site_id.strip())
        return site_id

