import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import simpledialog
import pathlib
import re
import math
import sys
import os

def make_pattern_dic(msi_path):
    with open(msi_path, encoding='latin1') as fin:
        lines = fin.readlines()

    mode = ''
    hori = []
    vert = []
    dic = {}
    for line in lines:
        line = line.strip()

        if re.match('HORIZONTAL', line):
            # print('set horizontal mode')
            mode = 'horizontal'
            continue

        if re.match('VERTICAL', line):
            # print('set vertical mode')
            mode = 'vertical'
            continue

        r = re.match('^([A-Z]+)\s+(.*)', line)
        if r:
            flag = r.group(1)
            data = r.group(2)
            dic[flag] = data
            continue


        r = re.match('^([\d\.]+)\s([\d\.]+)', line)
        if r:
            pair = (float(r.group(1)), float(r.group(2)))
            if mode == 'horizontal':
                hori.append(pair)
            elif mode == 'vertical':
                vert.append(pair)
            else:
                assert 0, 'ERROR'

    dic['HORIZONTAL'] = hori
    dic['VERTICAL'] = vert
    return dic

def read_header(msi_path):
    l = []
    with open(msi_path) as fin:
        for i in range(50):
            line = fin.readline()
            l.append(line)
            if line.startswith('HORIZONTAL'):
                return l
    return l

class FolderBrowser(tk.Frame):
    def __init__(self, parent_window, file_list, flag):
        super().__init__(parent_window)
        self.mainwindow = parent_window
        self.tree = ttk.Treeview(self)
        self.tree.pack(ipadx=100, expand=True, fill='both')

        self.file_list = file_list
        self.flag = flag
        self.files = []

        self.tree.bind('<<TreeviewOpen>>', self.add_sub_folders)
        self.tree.bind("<<TreeviewSelect>>", self.get_and_add_files)
        self.tree.pack(ipadx=100, expand=True, fill='both')


    def set_folder(self, folder):
        path_parts = folder.parts
        item = ''
        for i in range(1, len(path_parts) + 1):
            full_path = pathlib.Path(*path_parts[0:i])
            if  full_path.name == '':
                entry_text = full_path
            else:
                entry_text = full_path.name
            
            item = self.tree.insert(item, 'end', str(full_path), text=entry_text)
            self.tree.item(item, open=True)

    def add_sub_folders(self, e):
        base = self.tree.focus()
        for item in pathlib.Path(base).iterdir():
            if item.is_dir() and str(item) not in self.tree.get_children(base):
                self.tree.insert(base, 'end', str(item), text=item.name)

    def get_and_add_files(self, e):
        folder = self.tree.focus()
        self.file_list.get_files(folder, flag=self.flag)


class FileList(tk.Frame):
    def __init__(self, parent_window, drawing):
        self.files = []
        self.parent_window = parent_window
        self.drawing = drawing
        self.flag = 'A'
        self.filter = ".+"
        self.sort_order = {'#0': True, '#1': True, '#2': True, '#3': True}
        super().__init__(parent_window)

        # ---Filter
        self.filter_var = tk.StringVar(value='.+')
        self.filter_var.trace_add("write", self.on_filter_change)
        self.filter1 = tk.Entry(self, textvariable=self.filter_var)
        self.filter1.pack(fill='x')

        # ---- Tree---
        self.tree = ttk.Treeview(self)
        self.tree.config(selectmode='extended')


        self.tree['columns'] = ('flag', 'freq', 'tilt')
        self.tree.heading('flag', text='flag')
        self.tree.heading('freq', text='Frequency')
        self.tree.heading('tilt', text='Tilt')
        
        self.tree.heading('#0', text='filename')
        self.tree.heading('flag', text='flag')
        self.tree.heading('freq', text='freq')
        self.tree.heading('tilt', text='tilt')

        self.tree.column('#0', width=300, anchor='w')
        self.tree.column('flag', width=10, anchor='w')
        self.tree.column('tilt', width=10, anchor='w')
        self.tree.column('freq', width=20, anchor='w')

        self.tree.bind("<<TreeviewSelect>>", self.draw)
        self.tree.bind('<Button-1>', self.on_header_click)
        self.tree.bind("<Double-1>", self.on_double_click)

        self.tree.pack(side='left', expand=True, fill='both', ipadx=50)

    def get_files(self, folder, flag):
        self.read_files(folder, flag)
        self.add_files()

    def on_filter_change(self, *args):
        filter = self.filter_var.get()
        self.set_filter(filter)

    def read_files(self, folder, flag):

        # delete files only from source FileBrowser
        self.files = [row for row in self.files if row['flag'] != flag]


        for item in pathlib.Path(folder).iterdir():
            if item.is_file() and not item in self.tree.get_children(''):
                r = re.match(r'.*_(-\d|\d\d)T.*', item.name)
                if r:
                    tilt = r.group(1)
                else:
                    tilt = ''
                r = re.match(r'.*_(\d{3,4})_', item.name)
                if r:
                    freq = r.group(1)
                else:
                    freq = ''

                row = {
                    'path' :str(item),
                    'flag' : flag,
                    'name' : item.name,
                    'freq' : freq,
                    'tilt' : tilt
                }

                self.files.append(row)

    def add_files(self):
        # Apply filter
        filtered = [f for f in self.files if re.match(self.filter, f['name'])]

        # delete all entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        # add all entries
        for row in filtered:
            if row['path'] not in self.tree.get_children(''):
                self.tree.insert('', 'end', row['path'], text=row['name'], values= [row['flag'], row['freq'], row['tilt'] ])

    def sort_files(self, columns, ascending):
        self.files = sorted(self.files, key=lambda row: row[columns], reverse= not ascending)

    def on_header_click(self,e):               
        region = self.tree.identify_region(e.x, e.y)
        if region == 'heading':
            column = self.tree.identify_column(e.x)

            if column == '#0':
                self.sort_files('name', self.sort_order[column])
                self.sort_order[column] = not self.sort_order[column]

            if column == '#1':
                self.sort_files('flag', self.sort_order[column])
                self.sort_order[column] = not self.sort_order[column]

            if column == '#2':
                self.sort_files('freq', self.sort_order[column])
                self.sort_order[column] = not self.sort_order[column]

            if column == '#3':
                self.sort_files('tilt', self.sort_order[column])
                self.sort_order[column] = not self.sort_order[column]


            filtered = [f for f in self.files if re.match(self.filter, f['name'])]

            # delete all entries
            for item in self.tree.get_children():
                self.tree.delete(item)

            # add all entries
            for row in filtered:
                self.tree.insert('', 'end', row['path'], text=row['name'], values= [row['flag'], row['freq'], row['tilt'] ])

    def on_double_click(self, e):
        item_id = self.tree.identify_row(e.y)
        if not item_id.lower().endswith('.msi'):
            os.system('"' + item_id + '"')

    def select_file(self, filename):
        self.tree.selection_set(filename)  
        self.tree.focus(filename)        
        self.tree.see(filename) 

    def draw(self, e):
        self.drawing.draw(self.tree.selection())


    def set_filter(self, filter_str):
        self.filter = filter_str
        self.add_files()
  
class Drawing(tk.Canvas):
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.fontname = "Consolas"
        self.fontsize = 10
        self.padding = 0.02
        self.files = []

        super().__init__(parent_window)
        self.bind("<Configure>", self.on_resize)

        self.config(relief="sunken", bd=1)

    def on_resize(self, e):
        self.delete("all")
        self.draw_axis()
        self.draw_diagrams()


    def draw_circle(self, center_x, center_y, radius, **kwargs):
        x0 = center_x - radius
        y0 = center_y - radius
        x1 = center_x + radius
        y1 = center_y + radius
        return self.create_oval(x0, y0, x1, y1, **kwargs)

    def draw_axis(self):
        w = self.winfo_width()
        a = self.padding * w

        x0, y0 = w/4, w/4
        r = w/4 - a
        for n in range(1, 4):
            self.draw_circle(x0, y0, r/3 * n, outline="#aaa",dash=(1, 3))
        self.draw_circle(x0, y0, 0.9 * r, outline="#aaa",dash=(1,1)) # 3dB

        x0, y0 = w*3/4, w/4
        r = w/4 - a
        for n in range(1, 4):
            self.draw_circle(x0, y0, r/3 * n, outline="#aaa",dash=(1, 3))
        self.draw_circle(x0, y0, 0.9 * r, outline="#aaa",dash=(1,1)) # 3dB

        # axis
        self.create_line(a, w/4, w/2 -a, w/4, fill='#aaa',dash=(1, 3))
        self.create_line(w/4, a, w/4, w/2-a, fill='#aaa',dash=(1, 3))

        self.create_line(w/2+a, w/4, w/2+w/2 -a, w/4, fill='#aaa',dash=(1, 3))
        self.create_line(w/2+w/4, a, w/2+w/4, w/2-a, fill='#aaa',dash=(1, 3))

    def draw(self, files):
            self.set_files(files)
            self.delete("all")
            self.draw_axis()
            self.draw_diagrams()

    def draw_diagrams(self):
            colors = ['#000', '#f00', '#090', '#00f', '#990', '#099', '#f0f']
           
            w = self.winfo_width()
            a = self.padding * w

            for i, msi_file in enumerate(self.files):
                if pathlib.Path(msi_file).suffix.lower() == '.msi':
                    color = colors[i % len(colors)]
                    # draw pattern
                    self.draw_pattern(msi_file, color)


                    # draw antenna data
                    header = read_header(msi_file)
                    filename = pathlib.Path(msi_file).name
                    header.insert(0, filename)

                    # lines for one pattern
                    if len(self.files) <= 1: 
                        for k, line in enumerate(header):
                            line = line.strip()
                            if k==0:
                                my_font = font.Font(family=self.fontname, size=self.fontsize, weight="bold")
                            else:
                                my_font = (self.fontname, self.fontsize)
                            self.create_text(10, w/2 + k * self.fontsize * 1.5, text=line, fill=color, font=my_font, anchor='nw')

                    # show 1 line for one paattern
                    else:
                        text = pathlib.Path(msi_file).name
                        for k, line in enumerate(header):
                            line = line.strip('\n').strip()
                            if len(line) > 0:
                                text = text + '|' + line.strip()
                        self.create_text(10, w/2 + i * self.fontsize * 1.5, text=text, fill=color, font=(self.fontname, self.fontsize), anchor='nw')

    def set_files(self, files):
        self.files = files

    def draw_pattern(self, msi_file, color):

        w = self.winfo_width()
        a = self.padding * w
        r0 = w/4 - a

        dic = make_pattern_dic(msi_file)
        points = dic['HORIZONTAL']
        a = []
        for point in points:
            grd = point[0]
            gain = point[1]
            rad = grd / 360 * 2 * math.pi

            r = r0 * (max(30 - gain, 0) / 30)
            x = r * math.cos(rad) + w/4
            y = r * math.sin(rad) + w/4
            a.append(x)
            a.append(y)
        self.create_polygon(*a, fill='', outline=color)

        points = dic['VERTICAL']
        a = []
        for point in points:
            grd = point[0]
            gain = point[1]
            rad = grd / 360 * 2 * math.pi

            r = r0 * (max(30 - gain, 0) / 30)
            x = r * math.cos(rad) + w*3/4
            y = r * math.sin(rad) + w/4
            a.append(x)
            a.append(y)
        self.create_polygon(*a, fill='', outline=color)

# ------------------- APP -------------------------------
class App(tk.Tk):
    def __init__(self, start_msi):

        # ------ start argument ------
        self.start_msi = start_msi

        if start_msi != '':
            self.root_folder = pathlib.Path(start_msi).parent
        else:
            self.root_folder = pathlib.Path('.').resolve()

        # ---- Settings ----
        self.start_geometry='1200x500'

        # ---- start tkinter ----
        super().__init__()
        self.title('Patview')
        self.geometry(self.start_geometry)

        # ------ Main Paned Window ------
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill='both' )

        # ------ Sub Paned Winows ------
        self.subpane = ttk.PanedWindow(self.paned_window)
        self.subpane.pack()

        # --- Drawing ---
        self.drawing = Drawing(self)

        # ----------- Filter and FileList ---------
        self.file_table = FileList(self, self.drawing)

        # # --------- Double Browser -------------------
        self.browser1 = FolderBrowser(self.subpane, self.file_table, flag='A')
        self.browser1.set_folder(self.root_folder)

        self.browser2 = FolderBrowser(self.subpane, self.file_table, flag='B')
        self.browser2.set_folder(self.root_folder)

        self.subpane.add(self.browser1)
        self.subpane.add(self.browser2)
        self.paned_window.add(self.subpane)
        self.paned_window.add(self.file_table)
        self.paned_window.add(self.drawing)

        # -------- initial drawing --------
        self.file_table.get_files(self.root_folder, 'A')
        self.file_table.select_file(self.start_msi)



if __name__ == '__main__':
    if len(sys.argv) > 1:
        start_msi = sys.argv[1]
    else:
        start_msi = ''
    app = App(start_msi)
    app.mainloop()