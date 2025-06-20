import tkinter as tk
from tkinter import ttk
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
    r = ''
    with open(msi_path) as fin:
        for i in range(50):
            line = fin.readline()
            line = line.strip('\n')
            line = line.replace(' ', ':', 1)
            r = r + line + '|'
            if line.startswith('HORIZONTAL'):
                break
    return r


class App(tk.Tk):
    def __init__(self, start_msi=''):
        super().__init__()

        
        # --- root folder
        if start_msi == '':
            self.root_folder = '.'
        else:
            self.root_folder = pathlib.Path(start_msi).parent

        # ---- Settings ----
        self.start_msi = start_msi
        self.start_geometry='1200x500'
        self.fontsize=10
        self.padding = 0.04
        self.ascending_0 = True
        self.ascending_1 = True
        self.ascending_2 = True


        self.title('Patview')
        self.geometry(self.start_geometry)
        self.bind("<Configure>", self.on_resize)

        # --- Canvas ---
        self.canvas = tk.Canvas(self, bg='white')

        # --- Browser ----
        self.browser = ttk.Treeview(self)
        first_item = pathlib.Path(self.root_folder).resolve()
        self.browser.insert('', 'end', first_item, text=first_item)
        self.browser.bind('<<TreeviewOpen>>', self.add_sub_folders)
        self.browser.bind("<<TreeviewSelect>>", self.get_and_add_files)

        # Set focus and selection on the first item
        self.browser.focus(first_item)              # Set keyboard focus
        self.browser.selection_set(first_item)      # Highlight it visually
        self.add_sub_folders()
        # Expand the first (root) item
        first_item = self.browser.get_children()[0]
        self.browser.item(first_item, open=True)

        # --- Table ---
        self.table = ttk.Treeview(self, columns=['freq', 'tilt'], selectmode="extended")
        self.table.heading('#0', text='filename')
        self.table.heading('freq', text='freq')
        self.table.heading('tilt', text='tilt')
        self.table.column('#0', width=300, anchor='w')
        self.table.column('tilt', width=10, anchor='w')
        self.table.column('freq', width=20, anchor='w')
        self.table.bind("<<TreeviewSelect>>", self.draw)
        self.table.bind('<Button-1>', self.on_treeview_click)
        self.get_and_add_files()

        # --- Layout ----
        self.browser.pack(side='left', expand=False, fill='both')
        self.table.pack(side='left', expand=False, fill='both', ipadx=50) # make it abit wider
        self.canvas.pack(side='left', expand=True, fill='both')

        # axis
        self.draw_axis()

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
                    self.sort_files('tilt', ascending=True)
                    self.ascending_2 = True

            self.add_files()

    def on_resize(self, e):
        self.draw(e)
    

    def add_sub_folders(self, e=None):
        base = self.browser.focus()

        for item in pathlib.Path(base).iterdir():
            if item.is_dir() and str(item) not in self.browser.get_children(base):
                self.browser.insert(base, 'end', str(item), text=item.name)


    def get_and_add_files(self, e=None):
        base = self.browser.focus()

         # add files
        self.files = []
        for item in pathlib.Path(base).iterdir():
            if item.is_file():
                item_str = str(item)

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

                self.files.append(row)

        self.sort_files('name', ascending=True)
        self.add_files()

    def sort_files(self, columns, ascending):
        self.files = sorted(self.files, key=lambda row: row[columns], reverse= not ascending)

    def add_files(self):

       # delete all entries
        for item in self.table.get_children():
            self.table.delete(item)
        # sort table
        for row in self.files:        
            self.table.insert('', 'end', row['path'], text=row['name'], values= [row['freq'], row['tilt'] ])

        # Select item at startup
        self.table.focus(self.start_msi)
        self.table.selection_set(self.start_msi)
        self.table.see(self.start_msi)
        

    def draw(self, e=None):
        self.canvas.delete("all")
        l = self.table.selection()
        colors = ['#000', '#f00', '#090', '#00f', '#990', '#099', '#f0f']
        
        self.draw_axis()
        w = self.canvas.winfo_width()
        a = self.padding * w

        # draw antenna names
        for i, msi_file in enumerate(l):
            if pathlib.Path(msi_file).suffix.lower() == '.msi':
                color = colors[i % len(colors)]
                self.draw_pattern(msi_file, color)
                text = pathlib.Path(msi_file).name + ': ' + read_header(msi_file)
                self.canvas.create_text(10, w/2 + i * self.fontsize * 1.5, text=text, fill=color, font=("Consolas", self.fontsize), anchor='nw')


    def draw_circle(self, center_x, center_y, radius, **kwargs):
        x0 = center_x - radius
        y0 = center_y - radius
        x1 = center_x + radius
        y1 = center_y + radius
        return self.canvas.create_oval(x0, y0, x1, y1, **kwargs)

    def draw_axis(self):
        w = self.canvas.winfo_width()
        a = self.padding * w

        # circles
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
        self.canvas.create_line(a, w/4, w/2 -a, w/4, fill='#aaa',dash=(1, 3))
        self.canvas.create_line(w/4, a, w/4, w/2-a, fill='#aaa',dash=(1, 3))

        self.canvas.create_line(w/2+a, w/4, w/2+w/2 -a, w/4, fill='#aaa',dash=(1, 3))
        self.canvas.create_line(w/2+w/4, a, w/2+w/4, w/2-a, fill='#aaa',dash=(1, 3))
       
    def draw_pattern(self, msi_file, color):

        w = self.canvas.winfo_width()
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
        self.canvas.create_polygon(*a, fill='', outline=color)

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
        self.canvas.create_polygon(*a, fill='', outline=color)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        start_msi = sys.argv[1]
    else:
        start_msi = ''
    print("start_msi:", start_msi)
    app = App(start_msi)
    app.mainloop()