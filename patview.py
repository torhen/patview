import tkinter as tk
from tkinter import ttk
from tkinter import font
import pathlib
import re
import math
import sys

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

class FolderBrowser(ttk.Treeview):
    def __init__(self, parent_window, file_list):
        super().__init__(parent_window)
        self.mainwindow = parent_window
        self.file_list = file_list
        self.files = []

        self.bind('<<TreeviewOpen>>', self.add_sub_folders)
        self.bind("<<TreeviewSelect>>", self.get_and_add_files)


    def set_folder(self, folder):
        path_parts = folder.parts
        item = ''
        for i in range(1, len(path_parts) + 1):
            full_path = pathlib.Path(*path_parts[0:i])
            if  full_path.name == '':
                entry_text = full_path
            else:
                entry_text = full_path.name
            
            item = self.insert(item, 'end', str(full_path), text=entry_text)
            self.item(item, open=True)

    def add_sub_folders(self, e):
        base = self.focus()
        for item in pathlib.Path(base).iterdir():
            if item.is_dir() and str(item) not in self.get_children(base):
                self.insert(base, 'end', str(item), text=item.name)

    def get_and_add_files(self, e):
        folder = self.focus()
        self.file_list.get_files(folder)


class FileList(ttk.Treeview):
    def __init__(self, parent_window, drawing):
        self.files = []
        self.parent_window = parent_window
        self.drawing = drawing
        super().__init__(parent_window)

        self['columns'] = ('freq', 'tilt')
        self.heading('freq', text='Frequency')
        self.heading('tilt', text='Tilt')
        self.config(selectmode='extended')
        self.heading('#0', text='filename')
        self.heading('freq', text='freq')
        self.heading('tilt', text='tilt')
        self.column('#0', width=300, anchor='w')
        self.column('tilt', width=10, anchor='w')
        self.column('freq', width=20, anchor='w')
        self.bind("<<TreeviewSelect>>", self.draw)
        # self.table.bind('<Button-1>', self.on_treeview_click)

    def get_files(self, folder):
        # delete all entries
        for item in self.get_children():
            self.delete(item)

        for item in pathlib.Path(folder).iterdir():
            if item.is_file():
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
                    'name' : item.name,
                    'freq' : freq,
                    'tilt' : tilt
                }

                self.insert('', 'end', row['path'], text=row['name'], values= [row['freq'], row['tilt'] ])

    # def sort_files(self, columns, ascending):
    #     self.files = sorted(self.files, key=lambda row: row[columns], reverse= not ascending)


    def draw(self, e):
        self.drawing.draw(self.selection())
 
 
class Drawing(tk.Canvas):
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.fontname = "Consolas"
        self.fontsize = 10
        self.padding = 0.02

        super().__init__(parent_window)


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
            self.delete("all")
            l = files
            colors = ['#000', '#f00', '#090', '#00f', '#990', '#099', '#f0f']
            
            self.draw_axis()
            w = self.winfo_width()
            a = self.padding * w

            for i, msi_file in enumerate(l):
                if pathlib.Path(msi_file).suffix.lower() == '.msi':
                    color = colors[i % len(colors)]
                    # draw pattern
                    self.draw_pattern(msi_file, color)


                    # draw antenna data
                    header = read_header(msi_file)
                    filename = pathlib.Path(msi_file).name
                    header.insert(0, filename)

                    # lines for one pattern
                    if len(l) <= 1: 
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

        self.ascending_0 = True
        self.ascending_1 = True
        self.ascending_2 = True

        # ---- start tkinter ----
        super().__init__()
        self.title('Patview')
        self.geometry(self.start_geometry)
        # self.bind("<Configure>", self.on_resize)

        # --- Drawing ---
        self.drawing = Drawing(self)

        # ---- frame for the left
        self.frame = ttk.Frame()

        # ----------- FileList ---------
        self.table = FileList(self, self.drawing)
        self.table.get_files(self.root_folder)

        # --------- Browser1 -------------------
        self.browser1 = FolderBrowser(self.frame, self.table)
        self.browser1.set_folder(self.root_folder)

        # ------------ Browser2 ---------
        self.browser2 = FolderBrowser(self.frame, self.table)
        self.browser2.set_folder(self.root_folder)
   
        # --- Layout ----
        self.browser1.pack(ipadx=100, expand=True, fill='both')
        self.browser2.pack(ipadx=100, expand=True, fill='both') 

        self.frame.pack(side='left', expand=False, fill='both')
        self.table.pack(side='left', expand=False, fill='both', ipadx=50)
        self.drawing.pack(side='left', expand=True, fill='both')

    def on_treeview_click(self, e):
        region = self.table.identify_region(e.x, e.y)
        if region == 'heading':
            column = self.table.identify_column(e.x)
            if column == '#0':
                if self.ascending_0 == True:
                    self.sort_files('name', ascending=False)
                    self.ascending_0 = False
                else:
                    self.sort_files('name', ascending=True)
                    self.ascending_0 = True

            if column == '#1':
                if self.ascending_1 == True:
                    self.sort_files('freq', ascending=False)
                    self.ascending_1 = False
                else:
                    self.sort_files('freq', ascending=True)
                    self.ascending_1 = True

            if column == '#2':
                if self.ascending_2 == True:
                    self.sort_files('tilt', ascending=False)
                    self.ascending_2 = False
                else:
                    self.sort_files('freq', ascending=True)
                    self.ascending_2 = True

            self.add_files()

  

    def add_sub_folders(self, e=None):
        base = self.browser1.focus()

        for item in pathlib.Path(base).iterdir():
            if item.is_dir() and str(item) not in self.browser1.get_children(base):
                self.browser1.insert(base, 'end', str(item), text=item.name)  

if __name__ == '__main__':
    if len(sys.argv) > 1:
        start_msi = sys.argv[1]
    else:
        start_msi = ''
    app = App(start_msi)
    app.mainloop()