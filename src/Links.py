from tkinter import *
from HostResolver import HostResolver, MEXASHARE, RAPIDGATOR


class Links(Tk):

    def __init__(self, glv, *args, **kwargs):
        self.glv = glv

        root = Tk.__init__(self, *args, **kwargs)

        self.root = root

        label_text = "Enter full links then press 'Update' to overwrite the local links"
        label = Label(self.root, text=label_text, width=98, height=20, anchor=NW)
        label.pack()

        self.text = Text(self.root, width=98)
        self.text.pack()
        self.text.place(x=5, y=20)
        self.add_binds(self.text)

        button = Button(self.root, text='Update', command=self.update)
        button.place(x=355, y=440, width=100, height=50)

    def update(self):
        link_input = self.text.get("1.0", "end-1c")
        links = link_input.split('\n')

        entry_urls = {}
        for link in links:
            if link == '':
                continue

            entry_id = link.split('/')[-1].split('.')[0][1:]

            if entry_id not in entry_urls.keys():
                entry_urls[entry_id] = []
            entry_urls[entry_id].append(link)

        for entry in entry_urls.keys():
            insert_queries = []
            for url in entry_urls[entry]:
                part = 0
                if '.part' in url:
                    part = url.split('.part')[-1].split('.')[0]
                insert_queries.append(f"INSERT INTO entry_links SET entry_id = {entry}, link = '{url}', part = {part}")

            if MEXASHARE == HostResolver.by_url(entry_urls[entry][0]):
                delete_query = (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                                f"AND (link LIKE '%//mexa%' OR link LIKE '%www.mexa%') AND comment = ''")
            elif RAPIDGATOR == HostResolver.by_url(entry_urls[entry][0]):
                delete_query = (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                                f"AND (link LIKE '%//{RAPIDGATOR}%' OR link LIKE '%rg.to%') AND comment = ''")
            else:
                host = HostResolver.by_url(entry_urls[entry][0])
                delete_query = (f"DELETE FROM entry_links WHERE entry_id = {entry} "
                                f"AND link LIKE '%{host}.%' AND comment = ''")

            if delete_query:
                self.glv.db.run_query(delete_query)

            for insert_query in insert_queries:
                self.glv.db.run_query(insert_query)

        exit()

    def add_binds(self, parent):
        parent.bind('<Button-3>', self.r_clicker, add='')

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

            rmenu.tk_popup(e.x_root + 40, e.y_root + 10, entry="0")

        except TclError:
            print(' - rClick menu, something wrong')
            pass

        return "break"
