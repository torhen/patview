import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os, re, pathlib, sys

class App:
    def __init__(self, argv):
        self.max_patterns_to_load = 50
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        self.root = tk.Tk()
        self.root.title('patview') 
        # self.root.geometry('1400x1400')
        self.root.option_add('*tearOff', False)  # no dotted line in menu, don't forget the star
        
        # Set font for the menu
        menu_font = tkfont.Font(family="Helvetica", size=14) 
        self.root.option_add("*Menu*Font", menu_font)

        # create menu bar
        self.menubar = tk.Menu(self.root, tearoff=False)
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar)


        # add file menu
        self.menubar.add_cascade(
            label="File",
            menu=self.file_menu,
        )

        self.file_menu.add_command(
            label='Open',
            command=self.menu_file_open
        )

        self.file_menu.add_command(
            label='Close all',
            command=self.menu_file_close_all
        )

        # self.file_menu.add_command(
        #     label='Exit',
        #     command=self.menu_file_exit
        # )

        # matplotlib 
        self.fig = plt.figure(figsize=(12, 12), dpi=70)
        # Create the left half axes (two plots stacked)
        self.ax_hori = self.fig.add_subplot(2, 2, 1, projection='polar') 
        self.ax_vert = self.fig.add_subplot(2, 2, 3, projection='polar')
        
        ticks = [n * np.pi/6 for n in range(12)] # ticks 0, 30, 60, ... degree

        # ax hori
        self.ax_hori.set_ylim(30, 0)
        self.ax_hori.set_theta_direction(-1)
        self.ax_hori.grid(True, linestyle='--', color='gray', linewidth=0.5)
        self.ax_hori.set_xticks(ticks)  # 0, 90, 180, 270 degrees
        self.ax_hori.set_yticks([30,20,10,3,0])
        self.ax_hori.set_yticklabels([])
        self.ax_hori.text(0,0,'0dB', va='bottom')
        self.ax_hori.text(0,10,'10dB', va='bottom')
        self.ax_hori.text(0,20,'20dB', va='bottom')
        self.ax_hori.text(0,30,'30dB', va='bottom')

        # ax vert
        self.ax_vert.set_ylim(30, 0)
        self.ax_vert.set_theta_direction(-1)
        self.ax_vert.grid(True, linestyle='--', color='gray', linewidth=0.5)
        self.ax_vert.set_xticks(ticks)  # 0, 90, 180, 270 degrees
        self.ax_vert.set_yticks([30,20,10,3,0])
        self.ax_vert.set_yticklabels(['30dB', '20dB', '10dB', '', '0dB'])
        self.ax_vert.set_yticklabels([])
        self.ax_vert.text(0,0,'0dB', va='bottom')
        self.ax_vert.text(0,10,'10dB', va='bottom')
        self.ax_vert.text(0,20,'20dB', va='bottom')
        self.ax_vert.text(0,30,'30dB', va='bottom')
    

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack() 

        # status bar
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor='w', padx=10, font=menu_font)
        self.status_bar.pack(side='bottom', fill='x')


        # commandline argument
        if len(argv) > 1:
            #print('start with', argv[1])
            self.draw_pattern((argv[1]))
        
        self.root.mainloop()

    def menu_file_open(self):
        file_paths = filedialog.askopenfilenames(
            title="Select an MSI File",
            initialdir=self.current_dir,
            filetypes=[("MSI Files", "*.msi"), ("All Files", "*.*")],  # Filter for .msi files
        )

        warning = ''
        if len(file_paths) > self.max_patterns_to_load: # two much files
            file_paths = file_paths[0:self.max_patterns_to_load]
            warning = f'patterns limited to {self.max_patterns_to_load}'


        for i, file_path in enumerate(file_paths):
            self.status_bar.config(text=f'{warning} loading {i+1}/{len(file_paths)} {file_path}')
            self.root.update_idletasks()
            self.draw_pattern(file_path)

        self.status_bar.config(text=f'{len(file_paths)} loaded.')
        self.root.update_idletasks()

    def menu_file_close_all(self):
        self.ax_hori.lines.clear()

        if self.ax_hori.get_legend() is not None:
            self.ax_hori.get_legend().remove()

        self.ax_vert.lines.clear()

        # reset the color schme
        self.ax_vert.set_prop_cycle(None)
        self.ax_hori.set_prop_cycle(None)

        self.canvas.draw()
        

    def draw_pattern(self, file_path):
        dic = self.parse(file_path)


        hori_degs = np.array(dic['hori_degs'])
        hori_gains = np.array(dic['hori_gains'])
 


        vert_degs = np.array(dic['vert_degs'])
        vert_gains = np.array(dic['vert_gains'])    
        self.ax_hori.plot(np.radians(hori_degs), hori_gains, label=pathlib.Path(file_path).name)
        self.ax_vert.plot(np.radians(vert_degs), vert_gains)


        # Legend
        self.ax_hori.legend(bbox_to_anchor=(1.1, 1), loc='upper left', borderaxespad=0)

        self.canvas.draw()

        self.current_dir = pathlib.Path(file_path).parent

    def menu_file_exit(self):
        self.root.destroy()


    def parse(self, file_name):

        with open(file_name) as fin:
            lines = fin.readlines()

        status = ''
        hori_degs = []
        hori_gains = []
        vert_degs = []
        vert_gains = []
        for line in lines:
            line = line.strip()

            if r:= re.match(r'HORIZONTAL\s+360', line):
                status = 'hori'
                continue

            if r := re.match(r'VERTICAL\s+360', line):
                status = 'vert'
                continue

            if r := re.match(r'(\d+(\.\d+)?)\s+(\d+(\.\d+)?)', line): # check for int or float
                deg = float(r.group(1))
                gain = float(r.group(3))
                if status == 'hori':
                    hori_degs.append(deg)
                    hori_gains.append(gain)
                elif status =='vert':
                    vert_degs.append(deg)
                    vert_gains.append(gain)
                else:
                    print('status wrong')


        if len(hori_degs) != 360:
            print(f"Error: hori_degs has len {len(hori_degs)} but should be 360")

        return {'hori_degs' : hori_degs,
                'hori_gains' : hori_gains,
                'vert_degs' : vert_degs,
                'vert_gains' : vert_gains,
                }



App(sys.argv)