import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter import simpledialog
from tkinter import messagebox
import pathlib
import re
import math
import sys
import os

# ----------- Globals ----------------------
class Settings:

    # bandname, letter, fmin_sr, fmax_sr, fmin_all, fmax_all, hsl
    bands = [
        ['0700', 'S', 743,    773,     738,  788, (  0, 100, 40)],
        ['0800', 'L', 791,    801,     791,  821, ( 30, 100, 40)],
        ['0900', 'G', 930.1,  945.1,   925,  960, ( 60, 100, 40)],
        ['1400', 'V', 1452,   1467,   1428, 1511, ( 90, 100, 40)],
        ['1800', 'D', 1860.1, 1879.9, 1805, 1880, (120, 100, 40)],
        ['2100', 'U', 2110.5, 2120.3, 2110, 2170, (150, 100, 40)],
        ['2600', 'E', 2620,   2645,   2594, 2690, (180, 100, 40)],
        ['3500', 'W', 3540,   3585,   3400, 3600, (210, 100, 40)],
        ['3600', 'Z', 3700,   3800,   3600, 3800, (240, 100, 40)]
    ]

    std_freqs = [
        738, 746, 757, 768, 777, 788,
        791, 798, 803, 807, 814, 821,
        925, 943, 960,
        1428, 1450, 1463, 1475, 1496, 1511,
        1805, 1830, 1845, 1859, 1880,
        2110, 2140, 2170,
        2594, 2622, 2658, 2665, 2690,
        3400, 3433, 3467, 3500, 3533, 3567, 3600,
        3600, 3633, 3667, 3700, 3733, 3767, 3800
    ]



    pattern_colors = ['#000', '#f00', '#090', '#00f', '#990', '#099', '#f0f']

    extract_freq_from_filename_re = r'.*_(\d{3,4})(_|\.|MHz)'
    extract_tilt_from_filename_re = r'.*_(\d\d)FD'
    atoll_passive_import_file = r'C:\test\atoll_import.txt'
    band_tolerance = 100 # Gives a band letter if not exact inside

# ------- Utility functions -------
class Helper:
    def hsl(h, s=100, l=50):
        """
        Convert HSL color to RGB hex format (#ffffff).
        h: Hue [0, 360)
        s: Saturation [0, 100]
        l: Lightness [0, 100]
        Returns: Hex color string
        """
        s /= 100
        l /= 100

        c = (1 - abs(2 * l - 1)) * s  # Chroma
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c/2

        if 0 <= h < 60:
            r_, g_, b_ = c, x, 0
        elif 60 <= h < 120:
            r_, g_, b_ = x, c, 0
        elif 120 <= h < 180:
            r_, g_, b_ = 0, c, x
        elif 180 <= h < 240:
            r_, g_, b_ = 0, x, c
        elif 240 <= h < 300:
            r_, g_, b_ = x, 0, c
        elif 300 <= h < 360:
            r_, g_, b_ = c, 0, x
        else:
            r_, g_, b_ = 0, 0, 0

        r = round((r_ + m) * 255)
        g = round((g_ + m) * 255)
        b = round((b_ + m) * 255)

        return f'#{r:02x}{g:02x}{b:02x}'
    

    def calc_band(f):
        f = float(f)
        for band in Settings.bands:
            fmin = band[2] - Settings.band_tolerance # +- MHz tolerance
            fmax = band[3] + Settings.band_tolerance
            if fmin <= f <= fmax:
                return band
        return []

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
                mode = 'horizontal'
                continue

            if re.match('VERTICAL', line):
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

    def pairs2atoll(pairs_hori, pairs_vert):
        """convert to list of string pairs to atoll importable string"""
        res = '2 0 0 360'
        digits = 2
        for p in pairs_hori:
            deg = int(float(p[0]))
            gain = round(float(p[1]), digits )
            part = str(deg) + ' ' + str(gain)
            res = res + ' ' + part

        res = res + ' 1 0 360'
        for p in pairs_vert:
            deg = int(float(p[0]))
            gain = round(float(p[1]), digits )
            part = str(deg) + ' ' + str(gain)
            res = res + ' ' + part

        return res

    def calc_gain(s):
        try:
            l = s.split()
            value = l[0]
            unit = l[1]

            if unit == 'dBd':
                add = 2.15
            elif unit == 'dBi':
                add = 0
            else:
                assert 'cant calc gain'

            return round(float(value) + add, 2)
        except:
            return ''

    def calc_tilt(s):
        s = s.strip()
        if s == '':
            return 0
        return int(s)


    def is_valid_regex(sreg):
        try:
            re.compile(sreg)
            return True
        except re.error:
            return False
    
    def make_passive_atoll(files):
        columns = "Name\tGain\tManufacturer\tComments\tELECTRICAL_TILT\tPhysical Antenna\tMin Frequency (MHz)\tMax Frequency (MHz)\tSR_ANTENNA_NAME\tFREQUENCY\tTILT\tSR_BAND\tSR_POLARIZATION\tPattern\n"
        values = []
        for file_dic in files:
            header_info = Helper.inspect_msis([file_dic])[0]
            # print(file_dic)
            antenna_dic = Helper.make_pattern_dic(file_dic['path'])
            atoll_str = Helper.pairs2atoll(antenna_dic['HORIZONTAL'], antenna_dic['VERTICAL'])

            freq = float(header_info['freq'])

            band = Helper.calc_band(freq)
            letter = band[1]
            tilt_str = str(Helper.calc_tilt(file_dic['tilt'])).zfill(2)

            Name = antenna_dic['NAME'].split('_')[0] + letter +  '_X' + '_T' + tilt_str
            print(Name)
            Gain = header_info['gain']
            Manufacturer = header_info['vendor']
            Comments = pathlib.Path(file_dic['file'])
            ELECTRICAL_TILT = file_dic['tilt']
            Physical_Antenna = antenna_dic['NAME']
            Min_Frequency = band[2]
            Max_Frequency = band[3]
            SR_ANTENNA_NAME = antenna_dic['NAME']
            FREQUENCY = header_info['bandname']
            TILT = header_info['tilt']
            SR_BAND = header_info['letter']
            SR_POLARIZATION = 'X'
            Pattern = atoll_str
            line = f'{Name}\t{Gain}\t{Manufacturer}\t{Comments}\t{ELECTRICAL_TILT}\t{Physical_Antenna}\t{Min_Frequency}\t{Max_Frequency}\t{SR_ANTENNA_NAME}\t{FREQUENCY}\t{TILT}\t{SR_BAND}\t{SR_POLARIZATION}\t{Pattern}\n'
            values.append(line)

        with open(Settings.atoll_passive_import_file, 'w') as fout:
            fout.write(columns)
            for value in values:
                fout.write(value)

        messagebox.showinfo('Make Atoll Pattern', f'{Settings.atoll_passive_import_file} created')


    def make_active_atoll(files):
        columns = "Name,Polarisation,Comments,PHYSICAL_ANTENNA,FREQUENCY,ELECTRICAL_TILT,SR_ANTENNA_NAME\n"

        print('make active atoll')

    def inspect_msi(full_path, deep):
        if not full_path.lower().endswith('.msi'):
            return
        name = pathlib.Path(full_path).name
        dic = {
            'path' : full_path,
            'file' : name,
            'freq' : Helper.extract_freq_from_filename(name),
            'tilt' : Helper.extract_tilt_from_filename(name)
        }

        if deep:
            vendor = ""
            header = Helper.read_header(full_path)
            for entry in header:
                if "huawei" in entry.lower():
                    vendor = "Huawei"
                elif "broadradio" in entry.lower():
                    vendor = "Broadradio"

                if entry.startswith('GAIN'):
                    gain_str = entry.strip()
                    gain_str = gain_str.strip('GAIN').strip()
                    gain_float = Helper.calc_gain(gain_str)

            dic['vendor'] = vendor
            dic['gain'] = gain_float

            band = Helper.calc_band(dic['freq'])
            if len(band) > 0:
                bandname, letter, fmin_sr, fmax_sr, fmin_all, fmax_all, hsl = band
            else:
                bandname, letter, fmin_sr, fmax_sr, fmin_all, fmax_all, hsl = ['','','','','','','']

            dic['bandname'] = bandname
            dic['letter'] = letter

        return dic

    def inspect_msis(files, deep):
        res = []
        for full_path in files:
            file_info = Helper.inspect_msi(full_path, deep=deep)
            if not file_info:
                continue
            res.append(file_info)
        return res    
    
    def extract_tilt_from_filename(filename):
        r = re.match(Settings.extract_tilt_from_filename_re, filename)
        if r:
            return r.group(1)
        else:
            return '-'
        
    def extract_freq_from_filename(filename):
        r = re.match(Settings.extract_freq_from_filename_re, filename)
        if r:
            return r.group(1)
        else:
            return '-'
    
# ----------------------- App ---------------------------------------------
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
    def __init__(self, parent_window, drawing, app):
        self.file_dics = []
        # self.file_dics_filtered = []
        self.parent_window = parent_window
        self.drawing = drawing
        self.app = app
        self.flag = 'A'
        self.filter = ".*"
        self.sort_order = {'#0': True, '#1': True, '#2': True, '#3': True}
        super().__init__(parent_window)

        # ---Filter
        self.filter_var = tk.StringVar(value=self.filter)
        self.filter_var.trace_add("write", self.on_filter_change)
        self.filter1 = tk.Entry(self, textvariable=self.filter_var)
        self.filter1.pack(fill='x')

        # ---- sort order
        self.sort_by = 'file'
        self.sort_asc = True

        # ---- Tree---
        self.tree = ttk.Treeview(self,  show="headings")
        # self.tree.config(selectmode='extended')


        self.tree.config(columns=("file", 'flag','freq', 'tilt'))
        self.tree.heading('file', text='file')
        self.tree.heading('flag', text='flag')
        self.tree.heading('freq', text='freq')
        self.tree.heading('tilt', text='tilt')
        
        self.tree.column('file', width=300, anchor='w')
        self.tree.column('flag', width=10, anchor='w')
        self.tree.column('tilt', width=10, anchor='w')
        self.tree.column('freq', width=20, anchor='w')

        self.tree.bind("<<TreeviewSelect>>", self.draw)
        self.tree.bind('<Button-1>', self.on_header_click)
        self.tree.bind("<Double-1>", self.on_double_click)

        self.tree.pack(side='left', expand=True, fill='both', ipadx=50)

        self.tree.bind("<Control-c>", self.copy_to_clipboard)
        self.tree.bind("<Control-C>", self.copy_to_clipboard)
        self.tree.bind("<Control-a>", self.select_all)
        self.tree.bind("<Control-A>", self.select_all)

    def copy_to_clipboard(self,*args):
        selected_items = self.tree.selection()  # Get selected item ID
        if selected_items:
            text = '\n'.join(selected_items)  # Combine values with tabs
            self.clipboard_clear()
            self.clipboard_append(text)

    def select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"  # Prevent default behavior (e.g. text selection)
    
    def get_files(self, folder, flag):
        self.read_files(folder, flag)
        self.add_files()

    def on_filter_change(self, *args):
        filter = self.filter_var.get()
        self.set_filter(filter)

    def read_files(self, folder, flag):

        # delete files only from source FileBrowser
        self.file_dics = [row for row in self.file_dics if row['flag'] != flag]

        # read file
        for item in pathlib.Path(folder).iterdir():
            if item.is_file() and not item in self.tree.get_children(''):
                full_path = str(item)
                file_info = Helper.inspect_msi(full_path, deep=False)
                if file_info:
                    file_info['flag'] = flag
                    self.file_dics.append(file_info)

    def add_files(self):
        # Apply filter
        if not Helper.is_valid_regex(self.filter):
            return
        
        filtered = [f for f in self.file_dics if re.match(self.filter, f['file'])]
        self.count_filtered = len(filtered)

        filtered_sorted = sorted(filtered, key=lambda x: x[self.sort_by], reverse = not self.sort_asc)

        # delete all entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        for dic in filtered_sorted:
            if dic['path'] not in self.tree.get_children(''):
                self.tree.insert('', 'end', iid=dic['path'], values= (dic['file'], dic['flag'], dic['freq'], dic['tilt'] ))

        self.set_statusbar()

    def set_statusbar(self):

        files_all = len(self.file_dics)
        files_selected = len(self.tree.selection())

        s = f'files found:{files_all} filtered:{self.count_filtered} selected:{files_selected}'
        self.app.set_statusbar(s)


    def on_header_click(self,e):               
        region = self.tree.identify_region(e.x, e.y)
        if region == 'heading':
            column = self.tree.identify_column(e.x)
            new_sort_by = self.tree.heading(column)['text']
            if new_sort_by != self.sort_by:
                self.sort_by = new_sort_by
            else:
                self.sort_asc = not self.sort_asc
            self.add_files()

    def on_double_click(self, e):
        item_id = self.tree.identify_row(e.y)
        if not item_id.lower().endswith('.msi'):
            os.system('"' + item_id + '"')

    def select_file(self, filename):
        self.tree.selection_set(filename)  
        self.tree.focus(filename)        
        self.tree.see(filename)


    def draw(self, e):
        full_paths = self.tree.selection()
        self.drawing.draw(full_paths)

        self.set_statusbar()

    def set_filter(self, filter_str):
        self.filter = filter_str
        self.add_files()
  
class Drawing(tk.Frame):
    def __init__(self, parent_window, app):
        self.parent_window = parent_window
        self.app = app
        self.fontname = "Consolas"
        self.fontsize = 10
        self.padding = 0.02
        self.files = []

        super().__init__(parent_window)

        # ------- Radiobuttons -----
        self.radio_content = tk.IntVar()
        self.radio_content.set(1) 
        self.radio_frame = tk.Frame(self)
        self.radio1 = tk.Radiobutton(self.radio_frame, text='patterns', variable=self.radio_content, value=1, command=self.on_radio_change)
        self.radio1.pack(side='left')
        self.radio2 = tk.Radiobutton(self.radio_frame, text='frequencies', variable=self.radio_content, value=2, command=self.on_radio_change)
        self.radio2.pack(side='left')
        self.radio2 = tk.Radiobutton(self.radio_frame, text='table', variable=self.radio_content, value=3, command=self.on_radio_change)
        self.radio2.pack(side='left')
        self.radio_frame.pack(anchor='w')

        self.subframe = tk.Frame(self)
        self.subframe.pack(expand=True, fill='both')

        # ----- Canvas ---
        self.canvas = tk.Canvas(self.subframe, relief="sunken", bd=1)
        # self.canvas.pack(expand=True, fill='both')
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Motion>", self.on_mouse_move)


        # ---- Treeview for table on top of canvas ----
        self.tree = ttk.Treeview(self.subframe, show="headings")

        self.tree.config(columns=("file", 'vendor','freq', 'bandname', 'letter', 'tilt', 'gain'))
        self.tree.heading("file", text="file")
        self.tree.heading("vendor", text="vendor")
        self.tree.heading("freq", text="freq")
        self.tree.heading("bandname", text="bandname")
        self.tree.heading("letter", text="letter")
        self.tree.heading("tilt", text="tilt")
        self.tree.heading("gain", text="gain")

        self.tree.column('file', width=200, anchor='w')
        self.tree.column('vendor', width=50, anchor='w')
        self.tree.column('freq', width=10, anchor='w')
        self.tree.column('bandname', width=10, anchor='w')
        self.tree.column('letter', width=10, anchor='w')
        self.tree.column('tilt', width=10, anchor='w')
        self.tree.column('gain', width=10, anchor='w')

        self.tree.place(x=0, y=0, relwidth=1, relheight=1)
        self.tree.bind('<Button-1>', self.on_header_click)
        self.sort_by = 'file'
        self.sort_ascending = True


    def on_radio_change(self, *args):
        self.draw()
      

    def on_resize(self, e):
        self.draw()

    def on_mouse_move(self, e):
        radio_selected = self.radio_content.get()
        if radio_selected == 2:
            f = int(self.unscale(e.x))
            self.app.set_statusbar(f'{f} MHz')

    def on_header_click(self,e):               
        region = self.tree.identify_region(e.x, e.y)
        if region == 'heading':
            column = self.tree.identify_column(e.x)
            new_sort_by = self.tree.heading(column)['text']
            if new_sort_by != self.sort_by:
                self.sort_by = new_sort_by
            else:
                self.sort_ascending = not self.sort_ascending
            self.draw3()


    def draw_circle(self, center_x, center_y, radius, **kwargs):
        x0 = center_x - radius
        y0 = center_y - radius
        x1 = center_x + radius
        y1 = center_y + radius
        return self.canvas.create_oval(x0, y0, x1, y1, **kwargs)

    def draw_axis(self):
        w = self.winfo_width()
        a = self.padding * w

        # text
        padding = 0.007
        self.canvas.create_text( (0.0 + padding) * w, padding  * w, text="Horizontal", font=("Consolas", int(0.02 * w)), fill="#bbb", anchor='nw')
        self.canvas.create_text( (0.5 + padding )* w, padding  * w, text="Vertical",   font=("Consolas", int(0.02 * w)), fill="#bbb", anchor='nw')

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

    def draw(self, files=None):  
        if files:
            self.files = files
        radio_selected = self.radio_content.get()
        if radio_selected == 1:
            self.draw1()
        elif radio_selected == 2:
            self.draw2()
        else:
            self.draw3()

    def draw1(self):
        self.tree.place_forget()
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas.delete("all")
        self.draw_axis()
        self.draw_diagrams()

    def draw2(self):
        self.tree.place_forget()
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)


        self.canvas.delete("all")


        def rect(band):
            bandname, letter, fmin_sr, fmax_sr, fmin_all, fmax_all, hsl = band
            bandname = str(int(bandname)) # delete leading zero because of space

            h, s, l = hsl
            hsl1 = (h, s, 80)
            # create band for all operators
            self.canvas.create_rectangle(self.scale(fmin_all),80, self.scale(fmax_all), 120, width=0.1, fill=Helper.hsl(*hsl1), outline="")
            # creat sunrise bands 
            self.canvas.create_rectangle(self.scale(fmin_sr),85, self.scale(fmax_sr), 115, width=0.1, fill=Helper.hsl(*hsl), outline="")

            # create text
            self.canvas.create_text(self.scale(fmin_sr), 20, text=letter, font=("Consolas", 9), fill=Helper.hsl(*hsl), anchor='nw')
            self.canvas.create_text(self.scale(fmin_sr), 40, text=bandname, font=("Consolas", 9), fill=Helper.hsl(*hsl), anchor='nw')


        for band in Settings.bands:
            rect(band)

        # create standard freqs
        for f in Settings.std_freqs:
            x0 = self.scale(f)
            y0 = 130
            x1 = x0
            y1 = 150

            self.canvas.create_line(x0, y0, x1, y1, fill="#aaa")

    
        # create frequency lines
        header_infos = Helper.inspect_msis(self.files, deep=False)
        for entry in header_infos:
            try:
                f = float(entry['freq'])
            except:
                f = 0
            x0 = self.scale(f)
            y0 = 70
            x1 = x0
            y1 = 130

            self.canvas.create_line(x0, y0, x1, y1)

    def draw3(self):
        self.canvas.place_forget()
        self.tree.place(x=0, y=0, relwidth=1, relheight=1)

        for item in self.tree.get_children():
            self.tree.delete(item)

        header_infos = Helper.inspect_msis(self.files, deep=True)
        header_infos = sorted(header_infos, key=lambda x: x[self.sort_by], reverse=not self.sort_ascending)

        for entry in header_infos:
            self.tree.insert("", "end", values=(entry['file'], entry['vendor'], entry['freq'], entry['bandname'], entry['letter'], entry['tilt'], entry['gain']))              
    
    def scale(self, f):
        w = self.winfo_width()
        h = self.winfo_height()
        fmin, fmax = 700, 3810
        space = 10
        x = (f - fmin) / (fmax - fmin) * (w - 2 * space) + space
        return x
    
    def unscale(self, x):
        w = self.winfo_width()
        h = self.winfo_height()
        fmin, fmax = 700, 3810
        space = 10
        f = (fmax - fmin) * (x - space) / (w - 2 * space) + fmin
        return f

    def draw_diagrams(self):
            pattern_colors = Settings.pattern_colors
           
            w = self.winfo_width()
            a = self.padding * w

            files = self.files
            if len(self.files) > 50:
                files = self.files[0:50]
                app.set_statusbar("Drawing patterns limited to 50")

            for i, msi_file in enumerate(files):
                if pathlib.Path(msi_file).suffix.lower() == '.msi':
                    color = pattern_colors[i % len(pattern_colors)]
                    # draw pattern
                    self.draw_pattern(msi_file, color)

                    # lines for one pattern
                    header = Helper.read_header(msi_file)
                    if len(files) <= 1: 
                        for k, line in enumerate(header):
                            line = line.strip()
                            if k==0:
                                my_font = font.Font(family=self.fontname, size=self.fontsize, weight="bold")
                            else:
                                my_font = (self.fontname, self.fontsize)
                            self.canvas.create_text(10, w/2 + k * self.fontsize * 1.5, text=line, fill=color, font=my_font, anchor='nw')

                    # show 1 line for one paattern
                    else:
                        text = msi_file
                        for k, line in enumerate(header):
                            line = line.strip('\n').strip()
                            if len(line) > 0:
                                text = text + '|' + line.strip()
                        self.canvas.create_text(10, w/2 + i * self.fontsize * 1.5, text=text, fill=color, font=(self.fontname, self.fontsize), anchor='nw')

    def set_files(self, files):
        self.files = files

    def draw_pattern(self, msi_file, color):

        w = self.winfo_width()
        a = self.padding * w
        r0 = w/4 - a

        dic = Helper.make_pattern_dic(msi_file)
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

        # ------ Menue -----
        self.menu_bar = tk.Menu(self)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Make passive Atoll import", command=self.on_make_passive_atoll)
        file_menu.add_command(label="Make active Atoll import", command=self.on_make_active_atoll)

        self.menu_bar.add_cascade(label="Action", menu=file_menu)

        # Attach the menu bar to the window
        self.config(menu=self.menu_bar)

        # ------ status bar -------
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")  # Initial status message

        self.status_bar = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)


        # ------ Main Paned Window ------
        self.pw_main = tk.PanedWindow(self, orient="horizontal")
        self.pw_main.pack(expand=True, fill='both' )

        # ------ Sub Paned Windows ------
        self.pw1 = ttk.PanedWindow(self.pw_main)
        self.pw_main.add(self.pw1)

        self.pw2 = ttk.PanedWindow(self.pw_main)
        self.pw_main.add(self.pw2)

        self.pw3 = ttk.PanedWindow(self.pw_main)
        self.pw_main.add(self.pw3)
        
        # ---------- Drawing ----------
        self.drawing = Drawing(self.pw3, self)

        # ----------- Filelist ---------
        self.file_table = FileList(self.pw2, self.drawing, self)

        # --------- Double Browser -------------------
        self.browser1 = FolderBrowser(self.pw1, self.file_table, flag='A')
        self.browser1.set_folder(self.root_folder)

        self.browser2 = FolderBrowser(self.pw1, self.file_table, flag='B')
        self.browser2.set_folder(self.root_folder)


        # ---- Add to Panes ------
        self.pw1.add(self.browser1)
        self.pw1.add(self.browser2)
        self.pw2.add(self.file_table)
        self.pw3.add(self.drawing)


        # -------- initial drawing --------
        self.file_table.get_files(self.root_folder, 'A')
        self.file_table.select_file(self.start_msi)


    def set_statusbar(self, s):
        self.status_var.set(s)

    def on_make_passive_atoll(self, *args):
        files = self.file_table.files_selected
        Helper.make_passive_atoll(files)

    def on_make_active_atoll(self, *args):
        files = self.file_table.files_selected
        Helper.make_active_atoll(files)



if __name__ == '__main__':
    if len(sys.argv) > 1:
        start_msi = sys.argv[1]
    else:
        start_msi = ''
    app = App(start_msi)
    app.mainloop()