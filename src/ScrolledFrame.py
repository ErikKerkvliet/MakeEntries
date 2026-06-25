import math
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from math import floor, ceil
import subprocess
import pyperclip
import os


class ScrolledFrame(Frame):
    def __init__(self, parent, scroll, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        self.parent = parent
        self.entries = None
        self.labels = None

        self.top = None
        self.vndb_id = None
        # When True (vndb-getchu combo) character cards show the VNDB portrait
        # next to the Getchu image(s), one card per row.
        self.show_vndb = False

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
        self.char_dropdowns = []

        # Create vertical scrollbar
        vscrollbar = Scrollbar(self, orient=VERTICAL, width=scroll)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)

        # Create canvas
        self.canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=self.canvas.yview)

        # Reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it
        self.interior = Frame(self.canvas, bg='gray')
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=NW)

        # Track changes to the canvas and frame width and sync them
        self.interior.bind('<Configure>', self._configure_interior)
        self.canvas.bind('<Configure>', self._configure_canvas)

        # Bind mouse wheel to canvas for scrolling only when hovering over this frame
        self.canvas.bind('<Enter>', self._bind_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_mousewheel)
        self.interior.bind('<Enter>', self._bind_mousewheel)
        self.interior.bind('<Leave>', self._unbind_mousewheel)

    def _configure_interior(self, event):
        # Update the scrollbars to match the size of the inner frame
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # Update the canvas's width to fit the inner frame
            self.canvas.config(width=self.interior.winfo_reqwidth())

    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # Update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_info_ui(self, parent):
        # Create entry fields for various information
        entries = {
            'title': self.create_entry(parent, 115, 8, 845, 25, 'title'),
            'romanji': self.create_entry(parent, 115, 38, 845, 25, 'romanji'),
            'developer1': self.create_entry(parent, 115, 68, 450, 25, 'developer 1'),
            'developer2': self.create_entry(parent, 115, 98, 450, 25, 'developer 2'),
            'released': self.create_entry(parent, 115, 128, 100, 25, 'released'),
            'webpage': self.create_entry(parent, 115, 158, 450, 25, 'webpage'),
            'infopage': self.create_entry(parent, 115, 188, 450, 25, 'infopage'),
        }

        self.entries = entries

    def add_binds(self, parent):
        parent.bind('<Button-3>', self.r_clicker, add='')
        parent.bind('<Control-a>', self.callback)

    def callback(self, event):
        event.widget.after(50, self.select_all, event.widget)

    @staticmethod
    def select_all(widget):
        widget.select_range(0, 'end')
        widget.icursor('end')

    def r_clicker(self, e):
        try:
            def r_click_copy(event):
                event.widget.event_generate('<Control-c>')

            def r_click_cut(event):
                event.widget.event_generate('<Control-x>')

            def r_click_paste(event):
                event.widget.event_generate('<Control-v>')

            e.widget.focus()

            rmenu = Menu(None, tearoff=0, takefocus=0)

            for (txt, cmd) in [
                (' Copy', lambda e=e: r_click_copy(e)),
                (' Paste', lambda e=e: r_click_paste(e)),
                (' Cut', lambda e=e: r_click_cut(e)),
            ]:
                rmenu.add_command(label=txt, command=cmd)

            rmenu.tk_popup(e.x_root + 40, e.y_root + 10, entry="0")

            # Keep the menu visible until a click outside or menu option selected
            rmenu.bind('<FocusOut>', lambda event: rmenu.unpost())

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
        self.top.withdraw()  # Hide window while positioning

        photo = ImageTk.PhotoImage(image)
        width = photo.width() + 4
        height = photo.height() + 4

        # Center the pop-up relative to the main app window
        root = self.winfo_toplevel()
        root.update_idletasks()
        
        loc_x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
        loc_y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)

        self.top.title('')
        self.top.geometry("{}x{}+{}+{}".format(width, height, loc_x, loc_y))
        self.top.resizable(False, False)
        self.top.deiconify()  # Show window once positioned

        frame = Frame(master=self.top)
        frame.pack_propagate(False)
        frame.pack(fill=BOTH, expand=1)

        button = Button(master=frame, image=photo, command=lambda: self.destroy_window(self.top))
        button.image = photo
        button.pack()
        button.place(x=0, y=0, anchor=NW)

    def _build_char_frame_combo(self, parent, char):
        """vndb-getchu card: VNDB portrait + full character data + Getchu
        image(s), one wide card per row. Mirrors build_char_frame's parallel-list
        bookkeeping so the submit logic keeps working unchanged."""
        main_path = char.get('img1', '')          # Getchu face — the submitted image
        vndb_path = char.get('vndb_img1', '')      # VNDB portrait — for comparison
        has_main = bool(main_path) and os.path.isfile(main_path)
        has_vndb = bool(vndb_path) and os.path.isfile(vndb_path)
        if not has_main and not has_vndb:
            return 0

        # If Getchu has no usable image, fall back to the VNDB portrait as the
        # submitted image so the character still has one.
        if not has_main and has_vndb:
            main_path, has_main = vndb_path, True
            char['img1'] = vndb_path

        card = Frame(master=parent.interior, bd=1, relief=SUNKEN, bg='#ffffff')
        card.place(width=944, height=200)

        def image_button(path, x, y, w, h):
            image = Image.open(path)
            photo = ImageTk.PhotoImage(image.resize([w, h]))
            btn = Button(master=card, image=photo, command=lambda im=image: self.build_img_dialog(im))
            btn.image = photo
            btn.place(x=x, y=y, width=w, height=h)
            return btn

        def placeholder(text, x, y, w, h):
            Label(card, text=text, bg='#ffffff', fg='#b71c1c',
                  relief='groove').place(x=x, y=y, width=w, height=h)

        # captions
        Label(card, text='VNDB', bg='#ffffff', anchor=W, fg='#555').place(x=4, y=2, width=150, height=14)
        Label(card, text='Getchu (submitted)', bg='#ffffff', anchor=W, fg='#555').place(x=160, y=2, width=160, height=14)

        # VNDB portrait (display only) and Getchu / main image (submitted)
        if has_vndb:
            image_button(vndb_path, 2, 18, 150, 176)
        else:
            placeholder('(no VNDB image)', 2, 18, 150, 176)

        if has_main:
            image_button(main_path, 158, 18, 150, 176)
        else:
            placeholder('(no Getchu image)', 158, 18, 150, 176)

        # include-character checkbox (over the submitted image)
        self.charCheckVar.append(IntVar())
        self.charCheck.append(Checkbutton(card, variable=self.charCheckVar[-1], bg='#ffffff'))
        self.charCheck[-1].select()
        self.charCheck[-1].place(x=160, y=20)

        # data labels
        for text, y in (('Name', 20), ('Romanji', 48), ('Gender', 76),
                        ('Measurements', 104), ('Height', 132), ('Weight', 160)):
            Label(card, text=f'{text}: ', bg='#ffffff', anchor=NW).place(x=320, y=y, width=110, height=20)
        Label(card, text='Cup: ', bg='#ffffff', anchor=NW).place(x=540, y=76, width=40, height=20)
        Label(card, text='Age: ', bg='#ffffff', anchor=NW).place(x=540, y=132, width=40, height=20)

        # data entries (same lists/order as build_char_frame)
        self.charNameEntry.append(Entry(card, font=("Calibri", 9)))
        self.charromanji_entry.append(Entry(card, font=("Calibri", 9)))
        self.charGenderEntry.append(Entry(card, font=("Calibri", 9)))
        self.charCupEntry.append(Entry(card, font=("Calibri", 9)))
        self.charMeasurementEntry.append(Entry(card, font=("Calibri", 9)))
        self.charHeightEntry.append(Entry(card, font=("Calibri", 9)))
        self.charAgeEntry.append(Entry(card, font=("Calibri", 9)))
        self.charWeightEntry.append(Entry(card, font=("Calibri", 9)))

        for e in (self.charNameEntry[-1], self.charromanji_entry[-1], self.charGenderEntry[-1],
                  self.charCupEntry[-1], self.charMeasurementEntry[-1], self.charHeightEntry[-1],
                  self.charAgeEntry[-1], self.charWeightEntry[-1]):
            self.add_binds(e)

        self.charNameEntry[-1].place(x=435, y=20, width=300, height=22)
        self.charromanji_entry[-1].place(x=435, y=48, width=300, height=22)
        self.charGenderEntry[-1].place(x=435, y=76, width=80, height=22)
        self.charCupEntry[-1].place(x=585, y=76, width=50, height=22)
        self.charMeasurementEntry[-1].place(x=435, y=104, width=300, height=22)
        self.charHeightEntry[-1].place(x=435, y=132, width=70, height=22)
        self.charAgeEntry[-1].place(x=585, y=132, width=60, height=22)
        self.charWeightEntry[-1].place(x=435, y=160, width=70, height=22)

        for entry, key in ((self.charNameEntry[-1], 'name'), (self.charromanji_entry[-1], 'romanji'),
                           (self.charGenderEntry[-1], 'gender'), (self.charMeasurementEntry[-1], 'measurements'),
                           (self.charHeightEntry[-1], 'height'), (self.charWeightEntry[-1], 'weight'),
                           (self.charCupEntry[-1], 'cup'), (self.charAgeEntry[-1], 'age')):
            if char.get(key, '') != '':
                entry.insert(0, char[key])

        # Getchu body image (img2) + its include checkbox
        char['img2'] = main_path.replace('__img', 'charb') if has_main else ''
        if char['img2'] and os.path.isfile(char['img2']):
            Label(card, text='Getchu body', bg='#ffffff', anchor=W, fg='#555').place(x=760, y=2, width=120, height=14)
            image = Image.open(char['img2'])
            photo = ImageTk.PhotoImage(image.resize([120, 150]))
            btn = Button(card, image=photo, command=lambda im=image: self.build_img_dialog(im))
            btn.image = photo
            btn.place(x=760, y=18, width=120, height=150)
            self.charImgCheckVar.append(IntVar())
            cic = Checkbutton(card, variable=self.charImgCheckVar[-1], bg='#ffffff')
            cic.select()
            cic.place(x=762, y=20)
        else:
            self.charImgCheckVar.append(IntVar())

        # match-with-existing-character dropdown
        matches = char.get('matches', {})
        if len(matches) > 0:
            options = [f"c {cid:05d} | e {eid}" for cid, eid in matches.items()] + ['']
        else:
            options = ['']
        dropdown = ttk.Combobox(card, values=options, state="readonly", width=10)
        dropdown.set('')
        if len(matches) > 0:
            dropdown.place(x=700, y=160, width=200, height=22)
            dropdown.configure(postcommand=lambda: self.set_dropdown_width(dropdown, 1024))
        self.char_dropdowns.append(dropdown)

        return card

    def build_char_frame(self, parent, char):
        if self.show_vndb:
            return self._build_char_frame_combo(parent, char)

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

        char['img2'] = char['img1'].replace('__img', 'charb')
        if os.path.isfile(char['img2']):
            image = Image.open(char['img2'])

            resized = image.resize([64, 64])

            photo = ImageTk.PhotoImage(resized)

            button = Button(char_frame, image=photo, command=lambda: self.build_img_dialog(image))
            button.image = photo
            button.pack()
            button.place(x=330, y=102, width=68, height=68)

            self.charImgCheckVar.append(IntVar())

            char_img_check = Checkbutton(button, variable=self.charImgCheckVar[-1])
            char_img_check.select()
            char_img_check.pack()
            char_img_check.place(x=5, y=5, width=10, height=10)
        else:
            self.charImgCheckVar.append(IntVar())

        if len(char['matches']) > 0:
            options = []
            for character_tuple in list(char['matches'].items()):
                character_option = f"c {character_tuple[0]:05d} | e {character_tuple[1]}"
                options.append(character_option)
            options.append('')
        else:
            options = ['']

        dropdown = ttk.Combobox(char_frame, values=options, state="readonly", width=10)
        dropdown.set('')  # Set the default value
        if len(char['matches']) > 0:
            dropdown.place(x=405, y=148, width=700, height=20)
            dropdown.configure(postcommand=lambda: self.set_dropdown_width(dropdown, 1024))

        # Store the dropdown in a list if you need to access it later
        self.char_dropdowns.append(dropdown)

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
        output = subprocess.Popen('xrandr | grep "\\*" | cut -d" " -f4',
                                  shell=True,
                                  stdout=subprocess.PIPE
                                  ).communicate()[0]
        resolution = output.split()[0].split(b'x')
        return [int(resolution[0]), int(resolution[1])]

    def create_entry(self, parent, x, y, width, height, key):
        label = Label(parent, text=f"{key.capitalize()}: ", anchor=W)
        label.pack()
        label.place(x=20, y=y+2, width=100, height=20)

        entry = Entry(parent)
        entry.place(x=x, y=y, width=width, height=height)
        self.add_binds(entry)

        label.bind("<Button-1>", lambda event: self.paste_from_clipboard(entry))

        return entry

    @staticmethod
    def paste_from_clipboard(element):
        text_from_clipboard = pyperclip.paste()
        element.delete(0, END)
        element.insert(END, text_from_clipboard.strip())

    @staticmethod
    def set_dropdown_width(dropdown, width):
        dropdown_list = dropdown.winfo_toplevel()
        dropdown_list.update_idletasks()
        dropdown.configure(width=width)
        dropdown_list.geometry(f"{width}x{dropdown_list.winfo_height()}")


class App(Tk):
    def __init__(self, glv, *args, **kwargs):
        root = Tk.__init__(self, *args, **kwargs)

        self.glv = glv

        # Create main scrolled frame
        self.frame = ScrolledFrame(root, 45, relief='sunken')
        self.frame.pack()
        self.frame.place(x=5, y=240, width=960, height=380)

        # Create checkboxes for various options
        self.useCharCheckVar = IntVar()
        use_char_check = Checkbutton(root, text="Use characters", anchor=W, variable=self.useCharCheckVar)
        use_char_check.select()
        use_char_check.pack()
        use_char_check.place(x=10, y=216)

        self.useCupCheckVar = IntVar()
        use_cup_check = Checkbutton(root, text="Use cup sizes", anchor=W, variable=self.useCupCheckVar)
        use_cup_check.pack()
        use_cup_check.place(x=200, y=216)

        self.useImgVar = IntVar()
        use_img_check = Checkbutton(root, text="Use images", anchor=W, variable=self.useImgVar)
        use_img_check.select()
        use_img_check.pack()
        use_img_check.place(x=400, y=216)

        # Create secondary scrolled frame
        self.frame2 = ScrolledFrame(root, 12)
        self.frame2.pack()
        self.frame2.place(x=5, y=639, width=960, height=180)

        # Create decorative labels
        Label(root, relief='raised').place(x=5, y=240, width=1013, height=2)
        Label(root, relief='sunken').place(x=5, y=622, width=1014, height=18)
        Label(root, relief='sunken').place(x=5, y=817, width=1013, height=2)

    def submit(self, top_data):
        self.glv.log('Submit')

        data = {
            'cover': top_data['cover1']
        }

        if self.frame.vndbCoverVar and self.frame.vndbCoverVar.get() == 1:
            data['cover'] = top_data['cover2']

        data['title'] = self.frame.entries['title'].get()
        data['romanji'] = self.frame.entries['romanji'].get()
        if 'developer1' in top_data.keys() and top_data['developer1'] != '':
            data['developer1'] = self.frame.entries['developer1'].get()
        if 'developer2' in top_data.keys() and top_data['developer2'] != '':
            data['developer2'] = self.frame.entries['developer2'].get()
        data['released'] = self.frame.entries['released'].get()
        data['webpage'] = self.frame.entries['webpage'].get()
        data['infopage'] = self.frame.entries['infopage'].get()
        data['type'] = 'ova' if 'anidb' in self.glv.db_label else 'game'
        data['chars'] = []
        data['charVars'] = []

        entry_characters = []
        if self.useCharCheckVar.get() == 1:
            for i in range(len(self.frame.charCheckVar)):
                data['charVars'].append(self.frame.charCheckVar[i])
                if self.frame.charCheckVar[i].get() != 1:
                    continue

                drop_value = self.frame.char_dropdowns[i].get()
                if drop_value != '':
                    char_id = drop_value.split('|')[0]
                    char_id = ''.join([char for char in char_id if char.isdigit()])
                    entry_characters.append(char_id)
                    continue

                data['chars'].append({})
                data['chars'][-1]['checked'] = True
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

                if self.frame.charImgCheckVar[i].get() == 1:
                    data['chars'][-1]['img2'] = top_data['chars'][i]['img2']

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

        entry_id = self.glv.db.submit_entry_data(data)

        self.glv.db.connect(data, self.vndb_id, entry_id)
        for character_id in entry_characters:
            self.glv.db.insert_entry_character(entry_id, character_id)

        if 'anidb' in self.glv.db_label:
            anidb_id = self.glv.db_site.split('/')[-1]
            relation_id = self.glv.db.find_relation_by_anidb_id(anidb_id)

            relation_id = entry_id if relation_id == 0 else relation_id
            self.glv.db.insert_entry_relation(entry_id, relation_id)

            # from ArchiveManager import ArchiveManager
            # archive_manager = ArchiveManager(self.glv)
            # archive_path = archive_manager.create_rar_archive(self.glv.file)
            # self.glv.log(f'Created compressed RAR archive for video file: {archive_path}')

        if self.glv.sudo_pass:
            import subprocess
            subprocess.run(
                f'echo {self.glv.sudo_pass} | sudo -S chmod -R 777 /var/www/Hcapital/entry_images/entries/{entry_id}',
                shell=True, check=False
            )

        if getattr(self.glv, 'multiple', False):
            # Multiple mode: the entry is saved, so hand control back to Main
            # (which re-enables the entry-number window for the next run) while
            # keeping the browser session open. Closing only this review window
            # ends its event loop without quitting the browser or the process.
            self.destroy()
        else:
            self.glv.quit()

    @staticmethod
    def build_char_scroll_frame(parent, chars):
        buttons = []
        characters = []

        # vndb-getchu: one wide card per row (VNDB portrait + Getchu image(s)).
        if getattr(parent, 'show_vndb', False):
            for j, char in enumerate(chars):
                spacer = Button(parent.interior, width=0, height=12, bd=0, bg='gray',
                                relief='solid', highlightthickness=0,
                                activebackground='gray', activeforeground='gray')
                spacer.pack(anchor=W)
                char_frame = parent.build_char_frame(parent, char)
                if char_frame == 0:
                    spacer.destroy()
                    continue
                characters.append(char_frame)
                characters[-1].place(x=2, y=j * 204 + 2)
            return

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
        # vndb-getchu: show the VNDB portrait beside the Getchu image(s).
        self.frame.show_vndb = data.get('show_vndb', False)
        self.frame.create_info_ui(parent)

        if not os.path.isfile(data['cover1']):
            if os.path.isfile(data['cover2']):
                data['cover1'] = data['cover2']
            else:
                data['cover1'] = ''

        if data['cover1'] != '':
            self.frame.build_cover(parent, data['cover1'], data['cover2'])

        if data['title'] != '':
            self.frame.entries['title'].insert(0, self.check_var_for_sql(data['title']))

        if data['romanji'] != '':
            self.frame.entries['romanji'].insert(0, self.check_var_for_sql(data['romanji']))

        if 'developer1' in data.keys() and data['developer1'] != '':
            self.frame.entries['developer1'].insert(0, data['developer1'])

        if 'developer2' in data.keys() and data['developer2'] != '':
            self.frame.entries['developer2'].insert(0, data['developer2'])

        if data['released'] != '':
            self.frame.entries['released'].insert(0, data['released'])

        if data['webpage'] != '':
            self.frame.entries['webpage'].insert(0, data['webpage'])

        if data['infopage'] != '':
            self.frame.entries['infopage'].insert(0, data['infopage'])

        if data['chars']:
            if self.frame.show_vndb:
                # vndb-getchu: keep a character if it has an image on either side.
                valid_chars = [
                    char for char in data['chars']
                    if (char.get('img1') and os.path.isfile(char['img1']))
                    or (char.get('vndb_img1') and os.path.isfile(char['vndb_img1']))
                ]
            else:
                valid_chars = [char for char in data['chars']
                               if char.get('img1', '') != '' and os.path.isfile(char['img1'])]
            data['chars'] = valid_chars
            self.build_char_scroll_frame(self.frame, data['chars'])

        if data['samples']:
            self.build_sample_scroll_frame(self.frame2, data['samples'])

        submit_button = Button(parent, text='Submit', font=("Calibri", 12), command=lambda: self.submit(data))
        submit_button.pack()
        submit_button.place(x=860, y=205, height=30, width=100)

    @staticmethod
    def check_var_for_sql(var):
        if "'" in var:
            var = var.replace("'", "\'")
        if '"' in var:
            var = var.replace('"', '\"')

        return var
