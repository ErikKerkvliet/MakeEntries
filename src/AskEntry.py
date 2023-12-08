from tkinter import *


class AskEntry(Tk):

    def __init__(self, parent, globalvar, *args, **kwargs):
        self.glv = globalvar

        root = Tk.__init__(self, *args, **kwargs)

        self.root = root
        self.parent = parent
         
        self.siteLabel = Label(root, text='Site nr: ', width=40, height=20, anchor=NW)
        self.siteLabel.pack()
        self.vndbLabel = Label(root, text='VNDB nr: ', width=40, height=20, anchor=NW)
         
        self.siteLabel.place(x=5, y=10)
        self.vndbLabel.place(x=5, y=45)
         
        self.siteEntry = Entry(root, font=("Calibri", 9))
        self.vndbEntry = Entry(root, font=("Calibri", 9))
         
        self.siteEntry.place(x=80, y=5, width=85, height=30)
        self.vndbEntry.place(x=80, y=40, width=85, height=30)
        
        self.add_binds(self.siteEntry)
        self.add_binds(self.vndbEntry)
         
        self.button = Button(root, text='Start', command=self.return_enry_nrs)
        self.button.place(x=5, y=75, width=160, height=30)
                 
    def return_enry_nrs(self):
        if self.siteEntry.get() == '' or self.vndbEntry.get() == '':
            return

        self.parent.siteId = self.siteEntry.get()
        self.parent.vndbId = self.vndbEntry.get()
          
        self.siteLabel.destroy()
        self.vndbLabel.destroy()
         
        self.siteEntry.destroy()
        self.vndbEntry.destroy()
         
        self.button.destroy()
   
        self.parent.askEntry.destroy()
        
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
                   (' Copy', lambda e=e: r_click_copy(e)),
                   (' Paste', lambda e=e: r_click_paste(e)),
                   (' Cut', lambda e=e: r_click_cut(e)),
                   ]
    
            rmenu = Menu(None, tearoff=0, takefocus=0)
    
            for (txt, cmd) in nclst:
                rmenu.add_command(label=txt, command=cmd)
    
            rmenu.tk_popup(e.x_root+40, e.y_root+10, entry="0")
    
        except TclError:
            print(' - rClick menu, something wrong')
            pass
    
        return "break"

    def enter(self, e):
        self.return_enry_nrs()
