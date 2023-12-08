from tkinter import *
import tkinter.ttk as ttk


class ErrorHandler(Tk):

    def __init__(self, *args, **kwargs):
        root = Tk.__init__(self, *args, **kwargs)

        self.text_box = Text(root, height=30, width=100)
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        scrollb = ttk.Scrollbar(self, command=self.text_box.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.text_box['yscrollcommand'] = scrollb.set

        # self.text_box.pack()

    def set_error_message(self, message):
        self.text_box.insert(END, message)
