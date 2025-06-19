import tkinter as tk
from tkinter import ttk
import pathlib
import re
import math

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


class App(tk.Tk):
    def __init__(self):
        # ---- Settings ----
        self.start_geometry='1200x500'
        self.fontsize=10
        self.root_folder = '.'
        self.padding = 0.04

        super().__init__()
        self.title('Patview')
        self.geometry(self.start_geometry)


        # --- Browser ----
        self.browser = ttk.Treeview(self)
        self.browser.insert('', 'end', self.root_folder, text=pathlib.Path(self.root_folder).resolve())
        self.browser.bind('<<TreeviewOpen>>', self.get_subs)
        self.browser.bind("<<TreeviewSelect>>", self.get_files)


        # --- Table ---
        self.table = ttk.Treeview(self, selectmode="extended")
        # self.table.heading('filename', text='filename')
        self.table.bind("<<TreeviewSelect>>", self.draw_diagram)

        # --- Canvas ---
        self.canvas = tk.Canvas(self)
 
        # --- Layout ----
        self.browser.pack(side='left', expand=False, fill='both')
        self.table.pack(side='left', expand=False, fill='both', ipadx=50) # make it abit wider
        self.canvas.pack(side='left', expand=True, fill='both')

        # axis
        self.draw_axis()


    def get_subs(self, e):
        base = self.browser.focus()  

        for item in pathlib.Path(base).iterdir():
            if item.is_dir() and str(item) not in self.browser.get_children(base):
                self.browser.insert(base, 'end', str(item), text=item.name)



    def get_files(self, e):
        base = self.browser.focus()

        # deleta all entries
        for item in self.table.get_children():
            self.table.delete(item)

        # add files
        for item in pathlib.Path(base).iterdir():
            if item.is_file():
                self.table.insert('', 'end', str(item), text=item.name)

    def draw_diagram(self, e):
        self.canvas.delete("all")
        l = self.table.selection()
        colors = ['black', 'red', 'blue', 'green']
        
        self.draw_axis()
        w = self.canvas.winfo_width()

        # draw antenna names
        for i, msi_file in enumerate(l):
            color = colors[i % len(colors)]
            self.draw_pattern(msi_file, color)
            self.canvas.create_text(self.padding, w/2 + i * self.fontsize * 1.5, text=msi_file, fill=color, font=("Consolas", self.fontsize), anchor='nw')

    def draw_circle(self, center_x, center_y, radius, **kwargs):
        x0 = center_x - radius
        y0 = center_y - radius
        x1 = center_x + radius
        y1 = center_y + radius
        self.canvas.create_oval(x0, y0, x1, y1, **kwargs)

    def draw_axis(self):
        w = self.canvas.winfo_width()
        a = self.padding * w

        # helping rects
        self.canvas.create_rectangle(0, 0, w/2, w/2)
        self.canvas.create_rectangle(w/2, 0, w, w/2)

        # circles
        x0, y0 = w/4, w/4
        r = w/4 - a
        for n in range(1, 4):
            self.draw_circle(x0, y0, r/3 * n, outline="#aaa")

        x0, y0 = w*3/4, w/4
        r = w/4 - a
        for n in range(1, 4):
            self.draw_circle(x0, y0, r/3 * n, outline="#aaa")

        # axis
        self.canvas.create_line(a, w/4, w/2 -a, w/4, fill='#aaa')
        self.canvas.create_line(w/4, a, w/4, w/2-a, fill='#aaa')

    
        self.canvas.create_line(w/2+3/a, w/4, w/2+w/2 -a, w/4, fill='#aaa')
        self.canvas.create_line(w/2+w/4, a, w/2+w/4, w/2-a, fill='#aaa')
       
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
            print(x, y)
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
            print(x, y)
        self.canvas.create_polygon(*a, fill='', outline=color)

app = App()
app.mainloop()