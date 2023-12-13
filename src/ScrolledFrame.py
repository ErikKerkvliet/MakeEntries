import math

from tkinter import *
from PIL import Image, ImageTk
from math import floor, ceil
import subprocess

import os

glv = None

class ScrolledFrame(Frame):

    def __init__(self, parent, scroll, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        self.parent = parent
        self.developer1_entry = None
        self.developer2_label = None
        self.released_entry = None
        self.web_entry = None
        self.info_entry = None
        self.developer2_entry = None
        self.developer0_entry = None
        self.romanji_entry = None
        self.title_entry = None
        self.top = None
        self.vndb_id = None
        
        self.getchuCoverVar = None
        self.vndbCoverVar = None
        
        self.charCheck = []
        self.sampleCheck = []
        
        self.charCheckVar = []
        self.sampleCheckVar = []
        self.charImgCheckVar = []
        
        self.charNameEntry = []
        self.charromanji_entry = []
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

    @staticmethod
    def build_labels(parent):
        label = [
            Label(parent, text="Title: ", anchor=W),
            Label(parent, text="Romanji: ", anchor=W),
            Label(parent, text="Developer0: ", anchor=W),
            Label(parent, text="Developer1: ", anchor=W),
            Label(parent, text="Released: ", anchor=W),
            Label(parent, text="Webpage: ", anchor=W),
            Label(parent, text="Infopage: ", anchor=W),
        ]
        
        for i in range(0, 7):
            label[i].pack()
    
            label[i].place(x=20, y=(i * 30) + 10, width=100, height=20)
    
    def build_text_fields(self, parent):
        self.title_entry = Entry(parent)
        self.romanji_entry = Entry(parent)
        self.developer0_entry = Entry(parent)
        self.developer1_entry = Entry(parent)
        self.developer2_entry = Entry(parent)
        self.released_entry = Entry(parent)
        self.web_entry = Entry(parent)
        self.info_entry = Entry(parent)
        
        self.title_entry.place(x=115, y=8, width=900, height=25)
        self.romanji_entry.place(x=115, y=38, width=900, height=25)
        self.developer0_entry.place(x=115, y=68, width=450, height=25)
        self.developer1_entry.place(x=115, y=98, width=450, height=25)
        self.developer2_label = Label(parent, text="Developer2: ", anchor=W)
        self.released_entry.place(x=115, y=128, width=100, height=25)
        self.web_entry.place(x=115, y=158, width=450, height=25)
        self.info_entry.place(x=115, y=188, width=450, height=25)
        
        self.add_binds(self.title_entry)
        self.add_binds(self.romanji_entry)
        self.add_binds(self.developer0_entry)
        self.add_binds(self.developer1_entry)
        self.add_binds(self.developer2_entry)
        self.add_binds(self.released_entry)
        self.add_binds(self.web_entry)
        self.add_binds(self.info_entry)
    
    def add_binds(self, parent):
        parent.bind('<Button-3>', self.r_clicker, add='')
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
    
            rmenu.tk_popup(e.x_root+40, e.y_root+10,entry="0")
    
        except TclError:
            print(' - rClick menu, something wrong')
            pass
    
        return "break"
        
    def build_cover(self, parent, img1, img2):
        image1 = Image.open(img1)
        
        original = ImageTk.PhotoImage(image1)
        
        factor_x = 300 / original.width()
        factor_y = 170 / original.height() 
        factor = 0
        
        if factor_x <= factor_y:
            factor = factor_x
        elif factor_x > factor_y:
            factor = factor_y
        if factor_x > 1 and factor_y > 1:
            factor = 1
       
        he = floor(original.height() * factor)
        wi = floor(original.width() * factor)
        
        resized = image1.resize([wi, he])
        
        photo = ImageTk.PhotoImage(resized)
        
        button = Button(master=parent, image=photo, command=lambda: self.build_img_dialog(image1))
        button.image = photo
        button.pack()
        
        button.place(x=600, y=68, width=wi, height=he)
        
        self.getchuCoverVar = IntVar()
        
        getchu_cover_check = Checkbutton(button, variable=self.getchuCoverVar)
        getchu_cover_check.select()
        getchu_cover_check.pack()
        getchu_cover_check.place(x=5, y=5, width=10, height=10)
        
        self.vndbCoverVar = IntVar()
        if img2 != '':
            image2 = Image.open(img2)
            
            original = ImageTk.PhotoImage(image2)
            
            factor_x = 100 / original.width()
            factor_y = 70 / original.height() 
            factor = 0
            
            if factor_x <= factor_y:
                factor = factor_x
            elif factor_x > factor_y:
                factor = factor_y
            if factor_x > 1 and factor_y > 1:
                factor = 1
           
            he = floor(original.height() * factor)
            wi = floor(original.width() * factor)
            
            resized = image2.resize([wi, he])
            
            photo = ImageTk.PhotoImage(resized)
            
            button = Button(master=parent, image=photo, command=lambda: self.build_img_dialog(image2))
            button.image = photo
            button.pack()
            
            button.place(x=710, y=68, width=wi, height=he)
            
            vndb_cover_check = Checkbutton(button, variable=self.vndbCoverVar)
            vndb_cover_check.pack()
            vndb_cover_check.place(x=5, y=5, width=10, height=10)

    @staticmethod
    def destroy_window(window):
        window.destroy()
        
    def build_img_dialog(self, image):
        if self.top is not None:
            self.top.destroy()
        
        self.top = Toplevel()
        
        photo = ImageTk.PhotoImage(image)
        width = photo.width() + 4
        height = photo.height() + 4
        
        resolution = self.get_screen_resolution()
        loc_x = resolution[0] / 2 - width / 2
        loc_y = resolution[1] / 2 - height / 2
        
        loc_y = 0 if loc_y < 0 else math.floor(loc_y)
        loc_x = 0 if loc_x < 0 else math.floor(loc_x)

        self.top.title('')

        self.top.geometry("{}x{}+{}+{}".format(width, height, loc_x, loc_y)) 
        self.top.resizable(False, False)
        
        frame = Frame(master=self.top)
        frame.pack_propagate(False)
        frame.pack(fill=BOTH, expand=1)
        
        button = Button(master=frame, image=photo, command=lambda: self.destroy_window(self.top))
        button.image = photo
        button.pack()
        button.place(x=0, y=0, anchor=NW)
    
    def build_char_frame(self, parent, char):
        if char['img1'] == '' or not os.path.isfile(char['img1']):
            return 0
        
        image_face = Image.open(char['img1'])
        resized = image_face.resize([150, 170])
        
        char_frame = Frame(master=parent.interior, bd=1, relief=SUNKEN, bg='#ffffff')
        char_frame.place(width=454, height=186)
        
        photo = ImageTk.PhotoImage(resized)
        
        img_button = Button(master=char_frame, image=photo, command=lambda: self.build_img_dialog(image_face))
        img_button.image = photo
        img_button.pack()
        img_button.place(x=0, y=0, width=156, height=176)
        
        self.charCheckVar.append(IntVar())
        
        self.charCheck.append(Checkbutton(char_frame, variable=self.charCheckVar[-1]))
        self.charCheck[-1].select()
        self.charCheck[-1].pack()               
        self.charCheck[-1].place(x=5, y=5)
        
        label = [
            Label(char_frame, text="Name: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Romanji: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Gender: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Measurements: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Height: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Weight: ", bg='#ffffff', anchor=NW),
            Label(char_frame, text="Age: ", bg='#ffffff', anchor=NW),
        ]
        
        cup_label = Label(char_frame, text="Cup: ", bg='#ffffff', anchor=NW)
        cup_label.place(x=340, y=51, width=100, height=20)
        
        for i in range(0, 7):
            label[i].pack()
            label[i].place(x=160, y=(i * 25) + 1, width=100, height=20)   
            
        self.charNameEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charromanji_entry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charGenderEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charCupEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charMeasurementEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charHeightEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charAgeEntry.append(Entry(char_frame, font=("Calibri", 9)))
        self.charWeightEntry.append(Entry(char_frame, font=("Calibri", 9)))
        
        self.add_binds(self.charNameEntry[-1])
        self.add_binds(self.charromanji_entry[-1])
        self.add_binds(self.charGenderEntry[-1])
        self.add_binds(self.charCupEntry[-1])
        self.add_binds(self.charMeasurementEntry[-1])
        self.add_binds(self.charHeightEntry[-1])
        self.add_binds(self.charAgeEntry[-1])
        self.add_binds(self.charWeightEntry[-1])
        
        self.charNameEntry[-1].place(x=265, y=2, width=185, height=20)
        self.charromanji_entry[-1].place(x=265, y=27, width=185, height=20)
        self.charGenderEntry[-1].place(x=265, y=52, width=60, height=20)
        self.charCupEntry[-1].place(x=400, y=52, width=50, height=20)
        self.charWeightEntry[-1].place(x=265, y=127, width=55, height=20)
        
        self.charMeasurementEntry[-1].place(x=265, y=77, width=185, height=20)
        self.charHeightEntry[-1].place(x=265, y=102, width=55, height=20)
        
        self.charAgeEntry[-1].place(x=265, y=149, width=55, height=20) 
        
        if char['name'] != '':
            self.charNameEntry[-1].insert(0, char['name'])
          
        if char['romanji'] != '':
            self.charromanji_entry[-1].insert(0, char['romanji'])
          
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

        char['img2'] = char['img1'].replace('__img', 'char')
        if os.path.isfile(char['img2']):
            image = Image.open(char['img2'])
        
            resized = image.resize([64, 64])
            
            photo = ImageTk.PhotoImage(resized)
        
            button = Button(char_frame, image=photo, command=lambda: self.build_img_dialog(image))
            button.image = photo
            button.pack()
            button.place(x=340, y=102, width=68, height=68)
        
            self.charImgCheckVar.append(IntVar())
        
            char_img_check = Checkbutton(button, variable=self.charImgCheckVar[-1])
            char_img_check.select()
            char_img_check.pack()
            char_img_check.place(x=5, y=5, width=10, height=10)
        else:
            
            self.charImgCheckVar.append(IntVar())
        
        return char_frame
    
    def build_sample_frame(self, parent, img):
        sample = Frame(master=parent.interior, bd=1, bg='gray')
        sample.place(width=1014, height=176)
        
        image = Image.open(img)
        
        original = ImageTk.PhotoImage(image)
        
        factor_x = 150 / original.width()
        factor_y = 150 / original.height() 
        factor = 0
        
        if factor_x <= factor_y:
            factor = factor_x
        elif factor_x > factor_y:
            factor = factor_y
        if factor_x > 1 and factor_y > 1:
            factor = 1
       
        he = floor(original.height() * factor)
        wi = floor(original.width() * factor)
        
        resized = image.resize([wi, he])
        
        photo = ImageTk.PhotoImage(resized)
        
        button = Button(sample, image=photo, command=lambda: self.build_img_dialog(image))
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

    @staticmethod
    def get_screen_resolution():
        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4',
                                  shell=True,
                                  stdout=subprocess.PIPE
                                  ).communicate()[0]
        resolution = output.split()[0].split(b'x')
        return [int(resolution[0]), int(resolution[1])]


class App(Tk):
    def __init__(self, glv, *args, **kwargs):
        root = Tk.__init__(self, *args, **kwargs)

        self.glv = glv

        self.frame = ScrolledFrame(root, 98, relief='sunken')
        self.frame.pack()
        self.frame.place(x=5, y=258, width=1014, height=511)
        
        self.title_entry = None
        self.romanji_entry = None
        self.developerEntry = None
        self.released_entry = None
        self.coverEntry = None
        self.web_entry = None
        self.info_entry = None
                
        self.useCharCheckVar = IntVar()
        use_char_check = Checkbutton(root, text="Use characters", anchor=W, variable=self.useCharCheckVar)
        use_char_check.select()
        use_char_check.pack()
        use_char_check.place(x=10, y=224)
        
        self.useCupCheckVar = IntVar()
        use_cup_check = Checkbutton(root, text="Use cup sizes", anchor=W, variable=self.useCupCheckVar)
        use_cup_check.pack()
        use_cup_check.place(x=200, y=224)
        
        self.useImgVar = IntVar()
        use_img_check = Checkbutton(root, text="Use images", anchor=W, variable=self.useImgVar)
        use_img_check.select()
        use_img_check.pack()
        use_img_check.place(x=400, y=224)
             
        self.frame2 = ScrolledFrame(root, 60)
        self.frame2.pack()
        self.frame2.place(x=5, y=784, width=1014, height=180) 
        
        labell0 = Label(root, relief='raised')
        labell0.place(x=5, y=258, width=1013, height=2)
        
        labell1 = Label(root, relief='sunken')
        labell1.place(x=5, y=767, width=1014, height=18)
        
        labell2 = Label(root, relief='sunken')
        labell2.place(x=5, y=962, width=1013, height=2)             
        
    def submit(self, top_data):
        self.glv.log('Submit')

        data = {
            'cover': top_data['cover1']
        }

        if self.frame.vndbCoverVar and self.frame.vndbCoverVar.get() == 1:
            data['cover'] = top_data['cover2']
   
        data['title'] = self.frame.title_entry.get()
        data['romanji'] = self.frame.romanji_entry.get()
        data['developer0'] = self.frame.developer0_entry.get()
        if 'developer1' in top_data.keys() and top_data['developer1'] != '':
            data['developer1'] = self.frame.developer1_entry.get()
        if 'developer2' in top_data.keys() and top_data['developer2'] != '':
            data['developer2'] = self.frame.developer2_entry.get()
        data['released'] = self.frame.released_entry.get()
        data['webpage'] = self.frame.web_entry.get()
        data['infopage'] = self.frame.info_entry.get()
        
        data['chars'] = []
        data['charVars'] = []
        
        if self.useCharCheckVar.get() == 1:
            for i in range(len(self.frame.charCheckVar)):
                data['charVars'].append(self.frame.charCheckVar[i])
                if self.frame.charCheckVar[i].get() != 1:
                    continue
                
                data['chars'].append({})
                data['chars'][-1]['img1'] = top_data['chars'][i]['img1']
                data['chars'][-1]['name'] = self.frame.charNameEntry[i].get()
                data['chars'][-1]['romanji'] = self.frame.charromanji_entry[i].get()
                data['chars'][-1]['gender'] = self.frame.charGenderEntry[i].get()
                data['chars'][-1]['measurements'] = self.frame.charMeasurementEntry[i].get()
                data['chars'][-1]['height'] = self.frame.charHeightEntry[i].get()
                data['chars'][-1]['weight'] = self.frame.charWeightEntry[i].get()
                if self.useCupCheckVar.get() == 1:
                    data['chars'][-1]['cup'] = self.frame.charCupEntry[i].get()
                else:
                    data['chars'][-1]['cup'] = ''
                    
                data['chars'][-1]['age'] = self.frame.charAgeEntry[i].get()
                
                # if self.frame.charImgCheckVar[i].get() == 1:
                #     data['chars'][-1]['img2'] = top_data['chars'][i]['img2']
            
        data['samples'] = []
        data['sampleVars'] = []
        data['split'] = []
        if self.useImgVar.get() == 1:
            for i in range(len(self.frame2.sampleCheckVar)):
                if self.frame2.sampleCheckVar[i].get() != 1:
                    data['sampleVars'].append({})
                    continue
                
                data['sampleVars'].append(self.frame2.sampleCheckVar[i])
                data['samples'].append(top_data['samples'][i])
                
                data['split'].append(self.frame2.splitEntry[i].get())

        self.glv.db.connect(data, self.vndb_id)

    @staticmethod
    def build_char_scroll_frame(parent, chars):
        buttons = []     
        characters = []

        char_size = len(chars)
        for j in range(ceil(char_size / 2)):
            buttons.append(Button(
                    parent.interior,
                    width=0,
                    height=10,
                    bd=0,
                    bg='gray',
                    relief='solid',
                    highlightthickness=0,
                    activebackground='gray',
                    activeforeground='gray'
                )
            )
            buttons[-1].pack(anchor=W)
            
            for i in range(2):
                if j*2+i == char_size:
                    continue
                char_frame = parent.build_char_frame(parent, chars[j * 2 + i])
                if char_frame == 0:
                    continue
                characters.append(char_frame)
                characters[-1].place(x=i * 456+2, y=j * 178 + 2)                

    @staticmethod
    def build_sample_scroll_frame(parent, samples):
        buttons = []  
        imgs = []     
        
        samples_size = len(samples)
        for j in range(ceil(len(samples) / 6)):
            buttons.append(Button(parent.interior, width=0, height=9, bd=0, bg='gray',
                            relief='solid',highlightthickness=0, activebackground='gray',
                            activeforeground='gray'))
            buttons[-1].pack(anchor=W)
            
            for i in range(6):
                if (j*6+i) == samples_size:
                    break
                
                imgs.append(parent.build_sample_frame(parent, samples[(j * 6) + i]))
                imgs[-1].place(x=i * 158+2, y=j * 158 + 2)                    

    def fill_data(self, parent, data, vndb_id):
        self.vndb_id = vndb_id
        self.frame.build_labels(parent)
        self.frame.build_text_fields(parent)
        
        if data['cover1'] != '':
            self.frame.build_cover(parent, data['cover1'], data['cover2'])
          
        if data['title'] != '':
            self.frame.title_entry.insert(0, data['title'])
               
        if data['romanji'] != '':
            self.frame.romanji_entry.insert(0, data['romanji'])
                
        if data['developer0'] != '':
            self.frame.developer0_entry.insert(0, data['developer0'])

        if 'developer1' in data.keys() and data['developer1'] != '':
            self.frame.developer1_entry.insert(0, data['developer1'])
            
        if 'developer2' in data.keys() and data['developer2'] != '':
            self.frame.developer2_label.place(x=865, y=75)
            self.frame.developer2_entry.place(x=800, y=98, width=215, height=25)
            self.frame.developer2_entry.insert(0, data['developer2'])
               
        if data['released'] != '':
            self.frame.released_entry.insert(0, data['released'])
               
        if data['webpage'] != '':
            self.frame.web_entry.insert(0, data['webpage'])
               
        if data['infopage'] != '':
            self.frame.info_entry.insert(0, data['infopage'])

        if data['chars']:
            self.build_char_scroll_frame(self.frame, data['chars'])
        
        if data['samples']:
            self.build_sample_scroll_frame(self.frame2, data['samples'])
        
        submit_button = Button(parent, text='Submit', font=("Calibri", 12), command=lambda: self.submit(data))
        submit_button.pack()
        submit_button.place(x=920, y=210, height=30, width=100)
