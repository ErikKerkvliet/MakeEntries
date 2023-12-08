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
        
        self.addBinds(self.siteEntry)
        self.addBinds(self.vndbEntry)
         
        self.button = Button(root, text='Start', command=self.returnEnryNrs)
        self.button.place(x=5, y=75, width=160, height=30)
                 
    def returnEnryNrs(self):
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
        
    def addBinds(self, parent):
        parent.bind('<Button-3>', self.rClicker, add='')
        parent.bind('<KP_Enter>', self.enter)
        parent.bind('<Return>', self.enter)
        parent.bind('<Control-a>', self.callback)
        
    def callback(self, event):
        event.widget.after(50, self.select_all, event.widget)
        
    def select_all(self, widget):
        widget.select_range(0, 'end')
        widget.icursor('end')
    
    def rClicker(self, e):
        try:
            def rClick_Copy(e, apnd=0):
                e.widget.event_generate('<Control-c>')
    
            def rClick_Cut(e):
                e.widget.event_generate('<Control-x>')
    
            def rClick_Paste(e):
                e.widget.event_generate('<Control-v>')
    
            e.widget.focus()
    
            nclst=[
                   (' Copy', lambda e=e: rClick_Copy(e)),
                   (' Paste', lambda e=e: rClick_Paste(e)),
                   (' Cut', lambda e=e: rClick_Cut(e)),
                   ]
    
            rmenu = Menu(None, tearoff=0, takefocus=0)
    
            for (txt, cmd) in nclst:
                rmenu.add_command(label=txt, command=cmd)
    
            rmenu.tk_popup(e.x_root+40, e.y_root+10,entry="0")
    
        except TclError:
            print(' - rClick menu, something wrong')
            pass
    
        return "break"

    def enter(self, e):
        self.returnEnryNrs()
