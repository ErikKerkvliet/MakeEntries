import math

from tkinter import * 
from PIL import Image, ImageTk
from math import floor, ceil

import os


class ScrolledFrame(Frame):

    def __init__(self, parent, scroll, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)            

        self.top = None
        self.id = None
        
        self.getchuCoverVar = None
        self.vndbCoverVar = None
        
        self.charCheck = []
        self.sampleCheck = []
        
        self.charCheckVar = []
        self.sampleCheckVar = []
        self.charImgCheckVar = []
        
        self.charNameEntry = []
        self.charRomanjiEntry = []
        self.charGenderEntry = []
        self.charCupEntry = []
        self.charMeasurementEntry = []
        self.charHeightEntry = []
        self.charAgeEntry = []
        self.charWeightEntry = []
        self.splitEntry = []
        
        vscrollbar = Scrollbar(self, orient=VERTICAL, width=scroll)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)
        
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas, bg='gray')
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
    
    def buildLabels(self, parent):
        label = [0] * 7
        
        label[0] = Label(parent, text="Title: ", anchor=W)
        label[1] = Label(parent, text="Romanji: ", anchor=W)
        label[2] = Label(parent, text="Developer0: ", anchor=W)
        label[3] = Label(parent, text="Developer1: ", anchor=W)
        label[4] = Label(parent, text="Released: ", anchor=W)
        label[5] = Label(parent, text="Webpage: ", anchor=W)
        label[6] = Label(parent, text="Infopage: ", anchor=W)
        
        for i in range(0, 7):
            label[i].pack()
    
            label[i].place(x=20, y=(i * 30) + 10, width=100, height=20)
    
    def buildTextFields(self, parent):
        self.titleEntry = Entry(parent)
        self.romanjiEntry = Entry(parent)
        self.developer0Entry = Entry(parent)
        self.developer1Entry = Entry(parent)
        self.developer2Entry = Entry(parent)
        self.releasedEntry = Entry(parent)
        self.webEntry = Entry(parent)
        self.infoEntry = Entry(parent)
        
        self.titleEntry.place(x=115, y=8, width=900, height=25)
        self.romanjiEntry.place(x=115, y=38, width=900, height=25)
        self.developer0Entry.place(x=115, y=68, width=450, height=25)
        self.developer1Entry.place(x=115, y=98, width=450, height=25)
        self.developer2Label = Label(parent, text="Developer2: ", anchor=W)
        self.releasedEntry.place(x=115, y=128, width=100, height=25)
        self.webEntry.place(x=115, y=158, width=450, height=25)
        self.infoEntry.place(x=115, y=188, width=450, height=25)
        
        self.addBinds(self.titleEntry)
        self.addBinds(self.romanjiEntry)
        self.addBinds(self.developer0Entry)
        self.addBinds(self.developer1Entry)
        self.addBinds(self.developer2Entry)
        self.addBinds(self.releasedEntry)
        self.addBinds(self.webEntry)
        self.addBinds(self.infoEntry)
    
    def addBinds(self, parent):
        parent.bind('<Button-3>',self.rClicker, add='')
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
        
    def buildCover(self, parent, img1, img2):
        image1 = Image.open(img1)
        
        original = ImageTk.PhotoImage(image1)
        
        factorX = 300 / original.width()
        factorY = 170 / original.height() 
        factor = 0;
        
        if factorX <= factorY:
            factor = factorX;
        elif factorX > factorY:
            factor = factorY
        if factorX > 1 and factorY > 1:
            factor = 1
       
        he = floor(original.height() * factor)
        wi = floor(original.width() * factor)
        
        resized = image1.resize([wi, he])
        
        photo = ImageTk.PhotoImage(resized)
        
        button = Button(master=parent, image=photo, command=lambda: self.buildImgDialog(image1))
        button.image = photo
        button.pack()
        
        button.place(x=600, y=68, width=wi, height=he)
        
        self.getchuCoverVar = IntVar()
        
        getchuCoverCheck = Checkbutton(button, variable=self.getchuCoverVar)
        getchuCoverCheck.select()
        getchuCoverCheck.pack()               
        getchuCoverCheck.place(x=5, y=5, width=10, height=10)  
        
        self.vndbCoverVar = IntVar()
        if img2 != '':
            image2 = Image.open(img2)
            
            original = ImageTk.PhotoImage(image2)
            
            factorX = 100 / original.width()
            factorY = 70 / original.height() 
            factor = 0;
            
            if factorX <= factorY:
                factor = factorX
            elif factorX > factorY:
                factor = factorY
            if factorX > 1 and factorY > 1:
                factor = 1
           
            he = floor(original.height() * factor)
            wi = floor(original.width() * factor)
            
            resized = image2.resize([wi, he])
            
            photo = ImageTk.PhotoImage(resized)
            
            button = Button(master=parent, image=photo, command=lambda: self.buildImgDialog(image2))
            button.image = photo
            button.pack()
            
            button.place(x=710, y=68, width=wi, height=he)
            
            vndbCoverCheck = Checkbutton(button, variable=self.vndbCoverVar)
            vndbCoverCheck.pack()               
            vndbCoverCheck.place(x=5, y=5, width=10, height=10)  
        
    def destroyWindow(self, window):
        window.destroy()
        
    def buildImgDialog(self, image):
        if self.top != None:
            self.top.destroy()
        
        self.top = Toplevel()
        
        photo = ImageTk.PhotoImage(image)
        width = photo.width() + 4
        height = photo.height() + 4
        
        resolution = self.glv.get_screen_resolution()
        locX = resolution[0] / 2 - width / 2
        locY = resolution[1] / 2 - height / 2
        
        locY = 0 if locY < 0 else math.floor(locY)
        locX = 0 if locX < 0 else math.floor(locX)

        self.top.title('')

        self.top.geometry("{}x{}+{}+{}".format(width, height, locX, locY)) 
        self.top.resizable(0, 0)
        
        frame = Frame(master=self.top)
        frame.pack_propagate(0)
        frame.pack(fill=BOTH, expand=1)
        
        button = Button(master=frame, image=photo, command=lambda: self.destroyWindow(self.top))
        button.image = photo
        button.pack()
        button.place(x=0, y=0, anchor=NW)
    
    def buildCharFrame(self, parent, char):
        if char['img1'] == '' or not os.path.isfile(char['img1']):
            return 0
        
        imageFace = Image.open(char['img1'])
        resized = imageFace.resize([150, 170])
        
        charFrame = Frame(master=parent.interior, bd=1, relief=SUNKEN, bg='#ffffff')
        charFrame.place(width=454, height=186)
        
        photo = ImageTk.PhotoImage(resized)
        
        imgButton = Button(master=charFrame, image=photo, command=lambda: self.buildImgDialog(imageFace))
        imgButton.image = photo
        imgButton.pack()
        imgButton.place(x=0, y=0, width=156, height=176)
        
        self.charCheckVar.append(IntVar())
        
        self.charCheck.append(Checkbutton(charFrame, variable=self.charCheckVar[-1]))
        self.charCheck[-1].select()
        self.charCheck[-1].pack()               
        self.charCheck[-1].place(x=5, y=5)
        
        label = [0] * 7                    
        label[0] = Label(charFrame, text="Name: ", bg='#ffffff', anchor=NW)
        label[1] = Label(charFrame, text="Romanji: ", bg='#ffffff', anchor=NW)
        label[2] = Label(charFrame, text="Gender: ", bg='#ffffff', anchor=NW)
        label[3] = Label(charFrame, text="Measurements: ", bg='#ffffff', anchor=NW)
        label[4] = Label(charFrame, text="Height: ", bg='#ffffff', anchor=NW)
        label[5] = Label(charFrame, text="Weight: ", bg='#ffffff', anchor=NW)
        label[6] = Label(charFrame, text="Age: ", bg='#ffffff', anchor=NW)
        
        cupLabel = Label(charFrame, text="Cup: ", bg='#ffffff', anchor=NW)
        cupLabel.place(x=340, y=51, width=100, height=20) 
        
        for i in range(0, 7):
            label[i].pack()
            label[i].place(x=160, y=(i * 25) + 1, width=100, height=20)   
            
        self.charNameEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charRomanjiEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charGenderEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charCupEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charMeasurementEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charHeightEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charAgeEntry.append(Entry(charFrame, font=("Calibri", 9)))
        self.charWeightEntry.append(Entry(charFrame, font=("Calibri", 9)))
        
        self.addBinds(self.charNameEntry[-1])
        self.addBinds(self.charRomanjiEntry[-1])
        self.addBinds(self.charGenderEntry[-1])
        self.addBinds(self.charCupEntry[-1])
        self.addBinds(self.charMeasurementEntry[-1])
        self.addBinds(self.charHeightEntry[-1])
        self.addBinds(self.charAgeEntry[-1])
        self.addBinds(self.charWeightEntry[-1])
        
        self.charNameEntry[-1].place(x=265, y=2, width=185, height=20)
        self.charRomanjiEntry[-1].place(x=265, y=27, width=185, height=20)
        self.charGenderEntry[-1].place(x=265, y=52, width=60, height=20)
        self.charCupEntry[-1].place(x=400, y=52, width=50, height=20)
        self.charWeightEntry[-1].place(x=265, y=127, width=55, height=20)
        
        self.charMeasurementEntry[-1].place(x=265, y=77, width=185, height=20)
        self.charHeightEntry[-1].place(x=265, y=102, width=55, height=20)
        
        self.charAgeEntry[-1].place(x=265, y=149, width=55, height=20) 
        
        if char['name'] != '':
            self.charNameEntry[-1].insert(0, char['name'])
          
        if char['romanji'] != '':
            self.charRomanjiEntry[-1].insert(0, char['romanji'])
          
        if char['gender'] != '':
            self.charGenderEntry[-1].insert(0, char['gender'])
          
        if char['measurements'] != '':
            self.charMeasurementEntry[-1].insert(0, char['measurements'])
            
        if char['height'] != '':
            self.charHeightEntry[-1].insert(0, char['height'])
            
        if char['weight'] != '':
            self.charWeightEntry[-1].insert(0, char['weight'])
          
        if char['cup'] != '':
            self.charCupEntry[-1].insert(0, char['cup'])
        
        if char['age'] != '':
            self.charAgeEntry[-1].insert(0, char['age'])
            
        if char['img2'] != '' and os.path.isfile(char['img2']):
            image = Image.open(char['img2'])
        
            resized = image.resize([64, 64])
            
            photo = ImageTk.PhotoImage(resized)
        
            button = Button(charFrame, image=photo, command=lambda: self.buildImgDialog(image))
            button.image = photo
            button.pack()
            button.place(x=340, y=102, width=68, height=68)
        
            self.charImgCheckVar.append(IntVar())
        
            charImgCheck = Checkbutton(button, variable=self.charImgCheckVar[-1])
            charImgCheck.select()
            charImgCheck.pack()               
            charImgCheck.place(x=5, y=5, width=10, height=10)           
        else:
            
            self.charImgCheckVar.append(IntVar())
        
        return charFrame
    
    def buildSampleFrame(self, parent, img):
        sample = Frame(master=parent.interior, bd=1, bg='gray')
        sample.place(width=1014, height=176)
        
        image = Image.open(img)
        
        original = ImageTk.PhotoImage(image)
        
        factorX = 150 / original.width()
        factorY = 150 / original.height() 
        factor = 0
        
        if factorX <= factorY:
            factor = factorX
        elif factorX > factorY:
            factor = factorY
        if factorX > 1 and factorY > 1:
            factor = 1
       
        he = floor(original.height() * factor)
        wi = floor(original.width() * factor)
        
        resized = image.resize([wi, he])
        
        photo = ImageTk.PhotoImage(resized)
        
        button = Button(sample, image=photo, command=lambda: self.buildImgDialog(image))
        button.image = photo
        button.pack()
        button.place(x=0, y=0, width=154, height=154)
        
        self.sampleCheckVar.append(IntVar())
        
        self.sampleCheck.append(Checkbutton(sample, variable=self.sampleCheckVar[-1]))
        self.sampleCheck[-1].select()
        self.sampleCheck[-1].pack()               
        self.sampleCheck[-1].place(x=5, y=5)
        
        self.splitEntry.append(Entry(sample, font=("Calibri", 9)))
        
        if image.height > image.width:
            self.splitEntry[-1].place(x=25, y=9, width=15, height=15)
            self.splitEntry[-1].insert(0, 2)
        else:
            self.splitEntry[-1].insert(0, '1')
        
        return sample

class App(Tk):
    def __init__(self, glovalvar, *args, **kwargs):
        root = Tk.__init__(self, *args, **kwargs)

        self.glv = glovalvar

        self.frame = ScrolledFrame(root, 98, relief='sunken')
        self.frame.pack()
        self.frame.place(x=5, y=258, width=1014, height=511)
        
        self.titleEntry = None
        self.romanjiEntry = None
        self.developerEntry = None
        self.releasedEntry = None
        self.coverEntry = None
        self.webEntry = None
        self.infoEntry = None
                
        self.useCharCheckVar = IntVar()
        useCharCheck = Checkbutton(root, text="Use characters", anchor=W, variable=self.useCharCheckVar)
        useCharCheck.select()
        useCharCheck.pack()               
        useCharCheck.place(x=10, y=224)
        
        self.useCupCheckVar = IntVar()
        useCupCheck = Checkbutton(root, text="Use cup sizes", anchor=W, variable=self.useCupCheckVar)
        useCupCheck.pack()               
        useCupCheck.place(x=200, y=224)
        
        self.useImgVar = IntVar()
        useImgCheck = Checkbutton(root, text="Use images", anchor=W, variable=self.useImgVar)
        useImgCheck.select()
        useImgCheck.pack()               
        useImgCheck.place(x=400, y=224)
             
        self.frame2 = ScrolledFrame(root, 60)
        self.frame2.pack()
        self.frame2.place(x=5, y=784, width=1014, height=180) 
        
        labell0 = Label(root, relief='raised')
        labell0.place(x=5, y=258, width=1013, height=2)
        
        labell1 = Label(root, relief='sunken')
        labell1.place(x=5, y=767, width=1014, height=18)
        
        labell2 = Label(root, relief='sunken')
        labell2.place(x=5, y=962, width=1013, height=2)             
        
    def submit(self, topData):
        self.glv.addMessage('Submit')

        data = {}
        
        data['cover'] = topData['cover1']
        if self.frame.vndbCoverVar and self.frame.vndbCoverVar.get() == 1:
            data['cover'] = topData['cover2']            
   
        data['title'] = self.frame.titleEntry.get()
        data['romanji'] = self.frame.romanjiEntry.get()
        data['developer0'] = self.frame.developer0Entry.get()
        if 'developer1' in topData.keys() and topData['developer1'] != '':
            data['developer1'] = self.frame.developer1Entry.get()
        if 'developer2' in topData.keys() and topData['developer2'] != '':
            data['developer2'] = self.frame.developer2Entry.get()
        data['released'] = self.frame.releasedEntry.get()
        data['webpage'] = self.frame.webEntry.get()
        data['infopage'] = self.frame.infoEntry.get()
        
        data['chars'] = []
        data['charVars'] = []
        
        if self.useCharCheckVar.get() == 1:
            for i in range(len(self.frame.charCheckVar)):
                data['charVars'].append(self.frame.charCheckVar[i])
                if self.frame.charCheckVar[i].get() != 1:
                    continue
                
                data['chars'].append({})
                data['chars'][-1]['img1'] = topData['chars'][i]['img1']
                data['chars'][-1]['name'] = self.frame.charNameEntry[i].get()
                data['chars'][-1]['romanji'] = self.frame.charRomanjiEntry[i].get()
                data['chars'][-1]['gender'] = self.frame.charGenderEntry[i].get()
                data['chars'][-1]['measurements'] = self.frame.charMeasurementEntry[i].get()
                data['chars'][-1]['height'] = self.frame.charHeightEntry[i].get()
                data['chars'][-1]['weight'] = self.frame.charWeightEntry[i].get()
                if self.useCupCheckVar.get() == 1:
                    data['chars'][-1]['cup'] = self.frame.charCupEntry[i].get()
                else:
                    data['chars'][-1]['cup'] = ''
                    
                data['chars'][-1]['age'] = self.frame.charAgeEntry[i].get()
                
                if self.frame.charImgCheckVar[i].get() == 1:
                    data['chars'][-1]['img2'] = topData['chars'][i]['img2']
            
        data['samples'] = []
        data['sampleVars'] = []
        data['split'] = []
        if self.useImgVar.get() == 1:
            for i in range(len(self.frame2.sampleCheckVar)):
                if self.frame2.sampleCheckVar[i].get() != 1:
                    data['sampleVars'].append({})
                    continue
                
                data['sampleVars'].append(self.frame2.sampleCheckVar[i])
                data['samples'].append(topData['samples'][i])
                
                data['split'].append(self.frame2.splitEntry[i].get())

        self.glv.db.connect(data, self.id)
       
    def buildCharScrollFrame(self, parent, chars):
        buttons = []     
        characters = []

        charSize = len(chars)
        for j in range(ceil(charSize / 2)):
            buttons.append(Button(parent.interior, width=0, height=10, bd=0, bg='gray',
                            relief='solid',highlightthickness=0, activebackground='gray',
                            activeforeground='gray'))
            buttons[-1].pack(anchor=W)
            
            for i in range(2):
                if j*2+i == charSize:
                    continue
                charFrame = parent.buildCharFrame(parent, chars[j*2+i])
                if charFrame == 0:
                    continue
                characters.append(charFrame)
                characters[-1].place(x=i * 456+2, y=j * 178 + 2)                
                
    def buildSampleScrollFrame(self, parent, samples): 
        buttons = []  
        imgs = []     
        
        samplesSize = len(samples) 
        for j in range(ceil(len(samples) / 6)):
            buttons.append(Button(parent.interior, width=0, height=9, bd=0, bg='gray',
                            relief='solid',highlightthickness=0, activebackground='gray',
                            activeforeground='gray'))
            buttons[-1].pack(anchor=W)
            
            for i in range(6):
                if (j*6+i) == samplesSize:
                    break
                
                imgs.append(parent.buildSampleFrame(parent, samples[(j*6)+i]))
                imgs[-1].place(x=i * 158+2, y=j * 158 + 2)                    
                
                    
    def fillData(self, parent, data, id):
        self.id = id
        self.frame.buildLabels(parent)
        self.frame.buildTextFields(parent)
        
        if data['cover1'] != '':
            self.frame.buildCover(parent, data['cover1'], data['cover2'])
          
        if data['title'] != '':
            self.frame.titleEntry.insert(0, data['title'])
               
        if data['romanji'] != '':
            self.frame.romanjiEntry.insert(0, data['romanji'])
                
        if data['developer0'] != '':
            self.frame.developer0Entry.insert(0, data['developer0'])

        if 'developer1' in data.keys() and data['developer1'] != '':
            self.frame.developer1Entry.insert(0, data['developer1'])
            
        if 'developer2' in data.keys() and data['developer2'] != '':
            self.frame.developer2Label.place(x=865, y=75)
            self.frame.developer2Entry.place(x=800, y=98, width=215, height=25)
            self.frame.developer2Entry.insert(0, data['developer2'])
               
        if data['released'] != '':
            self.frame.releasedEntry.insert(0, data['released'])
               
        if data['webpage'] != '':
            self.frame.webEntry.insert(0, data['webpage'])
               
        if data['infopage'] != '':
            self.frame.infoEntry.insert(0, data['infopage'])

        if data['chars'] != []:
            self.buildCharScrollFrame(self.frame, data['chars'])
        
        if data['samples'] != []:
            self.buildSampleScrollFrame(self.frame2, data['samples'])  
        
        submitButton = Button(parent, text='Submit', font=("Calibri", 12), command=lambda: self.submit(data))
        submitButton.pack()
        submitButton.place(x=920, y=210, height=30, width=100)
