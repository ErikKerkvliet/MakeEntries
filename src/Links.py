
import os
import re
from datetime import datetime
from pathlib import Path
from tkinter import *
import tkinter as tk
from tkinter import Tk

from HostResolver import HostResolver, MEXASHARE, RAPIDGATOR


class Links(Tk):
    def __init__(self, glv, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Initialize Tk

        self.glv = glv

        self.title('Update Links v1.0 | Made by: Erik Kerkvliet')
        self.folder_path = "/home/erik/Desktop/Upload"

        label_text = "Enter full links then press 'Update' to overwrite the local links"
        label = Label(self, text=label_text, width=98, height=20, anchor=NW)
        label.pack()

        self.text = Text(self, width=98)
        self.text.pack()
        self.text.place(x=5, y=20)
        self.text.bind("<Button-3>", self.create_entry_context_menu)

        button = Button(self, text='Update', command=self.update)
        button.place(x=355, y=440, width=100, height=50)

    def create_entry_context_menu(self, event):
        """Creates a context menu for the entry widget."""
        context_menu = Menu(self, tearoff=0)
        context_menu.add_command(label="Cut", command=lambda: event.widget.event_generate("<<Cut>>"))
        context_menu.add_command(label="Copy", command=lambda: event.widget.event_generate("<<Copy>>"))
        context_menu.add_command(label="Paste", command=lambda: event.widget.event_generate("<<Paste>>"))
        context_menu.tk_popup(event.x_root, event.y_root)

    def update(self):
        link_input = self.text.get("1.0", "end-1c")
        links = link_input.split('\n')

        entry_urls = {}
        entry_sizes = {}
        for link in links:
            if link == '':
                continue

            entry_id = link.replace('_', '').split('/')[-1].split('.')[0][1:].split('-')[0]

            if entry_id not in entry_urls.keys():
                entry_urls[entry_id] = []
            entry_urls[entry_id].append(link)

        for entry in entry_urls.keys():
            insert_queries = []
            delete_queries = []
            size_query = None
            last_edited_query = None
            if entry not in entry_sizes:
                entry_sizes[entry] = self.get_files_size(entry)
                if isinstance(entry_sizes[entry], str):
                    size_query = f'UPDATE entries SET size = "{entry_sizes[entry]}" WHERE id = {entry}'

            if last_edited_query is None:
                last_edited = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                last_edited_query = f'UPDATE entries SET last_edited = "{last_edited}", time_type = "old" WHERE id = {entry}'

            for url in entry_urls[entry]:
                part = 0
                comment = ''
                url = url.replace("_", "")
                if '.part' in url:
                    part = url.split('.part')[-1].split('.')[0]
                if '-' in url:
                    comment_split = url.replace('_', '').split('/')[-1].split('-')
                    entry = comment_split[0][1:]
                    comment = comment_split[-1].split('.')[0]
                    comment = f'{comment.capitalize()}:'

                delete_queries.append(f'{self.get_delete_query(url, entry)} AND part = {part}')

                query = f"INSERT INTO entry_links SET" \
                        f" entry_id = {entry}, link = '{url}', part = {part}, comment = '{comment}'"
                insert_queries.append(query)

            if size_query is not None:
                self.glv.db.run_query(size_query)

            if last_edited_query is not None:
                self.glv.db.run_query(last_edited_query)

            for delete_query in delete_queries:
                self.glv.db.run_query(delete_query)

            for insert_query in insert_queries:
                self.glv.db.run_query(insert_query)

        exit()

    @staticmethod
    def get_delete_query(url, entry):
        if MEXASHARE == HostResolver.by_url(url):
            return (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                    f"AND (link LIKE '%//mexa%' OR link LIKE '%www.mexa%')")
        elif RAPIDGATOR == HostResolver.by_url(url):
            return (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                    f"AND (link LIKE '%//{RAPIDGATOR}%' OR link LIKE '%rg.to%')")
        else:
            host = HostResolver.by_url(url)
            return (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                    f"AND link LIKE '%{host}.%'")

    @staticmethod
    def get_size_format(bytes):
        """
        Convert bytes to human-readable format
        GB: 2 decimal places (e.g., 1.34 GB)
        MB: rounded to whole number (e.g., 145 MB)
        """
        if bytes >= 1024 * 1024 * 1024:  # GB
            return f"{bytes / (1024 ** 3):.2f} GB"
        elif bytes >= 1024 * 1024:  # MB
            return f"{round(bytes / (1024 ** 2))} MB"
        elif bytes >= 1024:  # KB
            return f"{round(bytes / 1024)} KB"
        else:
            return f"{bytes} B"

    def get_files_size(self, entry_id):
        """Get the size of all files in a directory or files containing entry_id in name"""
        path = f'{self.folder_path}/{entry_id}'
        total = 0
        try:
            # First try the direct path
            directory = Path(path)
            if directory.exists():
                for entry in directory.iterdir():
                    if entry.is_file():
                        total += entry.stat().st_size
                        print(f"{entry.name}: {self.get_size_format(entry.stat().st_size)}")
            else:
                # If directory doesn't exist, look for files containing entry_id in name
                main_directory = Path(self.folder_path)
                for file in main_directory.iterdir():
                    if file.is_file() and entry_id in file.name:
                        total += file.stat().st_size
                        print(f"{file.name}: {self.get_size_format(file.stat().st_size)}")

            if total == 0:
                return False

            return self.get_size_format(total)

        except Exception as e:
            return False
