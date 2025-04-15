import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfile, askdirectory
from tkmacosx import Button
import os
import time
import pandas as pd
from io import StringIO
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
import subprocess

LARGE_FONT = ("Raleway", 18)

class QuiverHS(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "QuiverHS")
        container = tk.Frame(self, width=600, height=300)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = { }

        for page in (StartPage, KIE, EIE):
            frame = page(container, self)

            self.frames[page] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.configure(bg='#b4d9cc')
        tk.Frame.grid(self, rowspan=2, columnspan=2)
        tk.Label(self, text="Welcome to QuiverHS!", font=LARGE_FONT, bg='#b4d9cc').place(relx=.5, rely=.2, anchor='center')

        Button(self, text="KIE Calculations", command=lambda:controller.show_frame(KIE), height=150, width = 200, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.1, rely=.6, anchor='w')

        Button(self, text="EIE Calculations", command=lambda:controller.show_frame(EIE), height=150, width = 200, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.9, rely=.6, anchor='e')

class KIE(tk.Frame):

    #def validate(self):
        # try:
        #     if float(self.freqEn.get()) <= 0:
        #         self.error = tk.Label(self, text = "The frequency scaling factor should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # except ValueError:
        #     self.error = tk.Label(self, text = "The frequency scaling factor should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # try:
        #     if float(self.rsmEn1.get()) <= 0 or float(self.rsmEn2.get()) <= 0 or float(self.rsmEn3.get()) <= 0 or float(self.rsmEn4.get()) <= 0:
        #         self.error = tk.Label(self, text="The rotational symmetry number should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # except ValueError:
        #     self.error = tk.Label(self, text="The rotational symmetry number should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # try:
        #     if float(self.rangeEn.get()) < 0:
        #         self.error = tk.Label(self, text="The temperature should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # except ValueError:
        #     self.error = tk.Label(self, text="The temperature should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # try:
        #     if float(self.incEn.get()) <= 0 or float(self.incEn.get()) > float(self.rangeEn.get()):
        #         self.error = tk.Label(self, text = "The temperature increment should be greater than 0 and less than the temperature range.", font=("Arial", 12), fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        # except ValueError:
        #     print("set default values for temp increment and range")# set default values for the two

    def open_file(self, num):
        file = askopenfile(mode='r', title="Select a .out or .config file")
        if file:
            if (('.out' in file.name) or ('.config' in file.name) or ('.log' in file.name)):
                self.files[num] = file
                if num == 0:
                    self.browseUR.set("Uploaded")
                elif num == 1:
                    self.browseLR.set("Uploaded")
                elif num == 2:
                    self.browseUT.set("Uploaded")
                for i in range(0, 3):
                    if(self.files[i] == None):
                        return
                self.calculate['state'] = 'normal'
            else:
                self.error = tk.Label(self, text = "The file should have a .txt extension.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')

    def open_direc(self):
        direc = askdirectory(title='Select a folder for the output folder to be created in')
        if direc:
            self.path = direc
            self.browseDirec.set("Uploaded")
    
    def ready(self):
        entries = self.rangeEn.get().split(",")
        increment = int(self.incEn.get())
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if(len(entries) == 1):
            entries.append(entries[0])
            increment = 1
        num = float(entries[0])
        final = float(entries[1])

        folder_name = f"QuiverHS_Output_{int(time.time())}"
        folder_path = os.path.join(self.path, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        while(num <= final):
            self.updating = tk.Label(self, text=f"Currently on temperature {num}", fg='red', bg='#b4d9cc')
            self.updating.place(relx=.8, rely=.9, anchor='center')
            print(f"For the temperature {num}")
            file_name = f"output_{num}.txt"
            file_path = os.path.join(folder_path, file_name)
            # logging.basicConfig(
            #     handlers=[logging.FileHandler(file_path), logging.StreamHandler(sys.stdout)],
            #     level=logging.INFO,
            #     format='%(asctime)s - %(message)s'
            # )
            with open(file_path, 'w'):
                pass
            command = f"python3 src/quiver_working.py -v {self.files[0].name} {self.files[1].name} {self.files[2].name} {num} {file_path}"
            os.system(command)
            num = num + increment
            print()


        # column_names = ['Isotopologue', 'Name', 'Uncorrected', 'Wigner', 'Bell']
        column_names = ['Isotopologue', 'Name', 'Uncorrected', 'Wigner', 'Bell', 'Enthalpy', 'Entropy']
        df = pd.DataFrame(columns=column_names)

        file_list = os.listdir(folder_path)
        for filename in file_list:
            path = os.path.join(folder_path, filename)
            if os.path.isfile(path):
                with open(path, 'r') as file:
                    file_contents = file.read()
                    lines = str(file_contents).strip().split("\n")
                    # filtered_lines = [line for line in lines if len(line.split()) <= 5]
                    filtered_lines = [line for line in lines if len(line.split()) <= 7]
                    filtered_data = "\n".join(filtered_lines)

                    print('FILTERED DATA', filtered_data)

                    df1 = pd.DataFrame(columns=column_names)
                    df1 = pd.read_csv(StringIO(filtered_data), sep="\s+", skiprows=3)
                    df1 = df1.iloc[1:]
                    df1['Temperature'] = float(lines[0].split()[1][:-1])

                    # print("df1 before concatenation:", df1)
                    # print("df before concatenation:", df)
                    
                    df = pd.concat([df, df1])
        
        #df = df.drop(columns=['Isotopologue'])
        #indices = np.lexsort((df.index, df['Temperature']))
        indices = np.lexsort((df['Temperature'], df.index))
        df = df.iloc[indices]
        print(df)
        df.to_csv(folder_path + "/output.csv", index=False)

        selected_rows = df[df['Name'] == 'H5']

        plt.figure(figsize=(8, 6))
        plt.scatter(selected_rows['Temperature'], selected_rows['Bell'], marker='o', color='green', label='H5')
        plt.xlabel('Temperature')
        plt.ylabel('Bell KIEs')
        plt.title(f'H5 Bell KIEs')
        plt.legend()
        plt.grid(True)
        plt.show()

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
       
        self.configure(bg='#b4d9cc')
        self.error = None
        self.files = [None] * 3
        self.browseUR = tk.StringVar()
        self.browseLR = tk.StringVar()
        self.browseUT = tk.StringVar()
        self.browseDirec = tk.StringVar()
        self.browseUR.set("Browse")
        self.browseLR.set("Browse")
        self.browseUT.set("Browse")
        self.browseDirec.set("Browse")

        tk.Label(self, text="KIE Calculations!", font=LARGE_FONT, bg='#b4d9cc').place(relx=.5, rely=.1, anchor='center')
        Button(self, text="Back", command=lambda:controller.show_frame(StartPage), width = 50, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.01, rely=.05, anchor='w')
        tk.Label(self, text="Configuration File", bg='#b4d9cc').place(relx=.25, rely=.25, anchor='e')
        tk.Label(self, text="Ground State File", bg='#b4d9cc').place(relx=.25, rely=.45, anchor='e')
        tk.Label(self, text="Transition State File", bg='#b4d9cc').place(relx=.25, rely=.65, anchor='e')
        tk.Label(self, text="Output Folder", bg='#b4d9cc').place(relx=.25, rely=.85, anchor='e')
        tk.Label(self, text="Frequency Scaling", bg='#b4d9cc').place(relx=.65, rely=.61, anchor='e')
        tk.Label(self, text="Factor", bg='#b4d9cc').place(relx=.65, rely=.675, anchor='e')
        tk.Label(self, text="σ - Rotational", bg='#b4d9cc').place(relx=.8, rely =.12, anchor='w')
        tk.Label(self, text="Symmetry Number", bg='#b4d9cc').place(relx=.775, rely =.18, anchor='w')
        
        #make list
        Button(self, textvariable=self.browseUR, command=lambda:self.open_file(0), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.35, rely=.25, anchor='center')
        Button(self, textvariable=self.browseLR, command=lambda:self.open_file(1), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.35, rely=.45, anchor='center')
        Button(self, textvariable=self.browseUT, command=lambda:self.open_file(2), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.35, rely=.65, anchor='center')
        Button(self, textvariable=self.browseDirec, command=lambda:self.open_direc(), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.35, rely=.85, anchor='center')
        
        self.freqEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.freqEn.insert(0, 1.0)
        self.freqEn.place(relx=.75, rely=.65, anchor='e')

        #make list
        self.rsmEn1 = tk.Entry(self, width = 4, highlightthickness=0)
        self.rsmEn1.insert(0, 1.0)
        self.rsmEn1.place(relx=.83, rely=.25, anchor='w')

        self.rsmEn2 = tk.Entry(self, width = 4, highlightthickness=0)
        self.rsmEn2.insert(0, 1.0)
        self.rsmEn2.place(relx=.83, rely=.45, anchor='w')

        self.rsmEn3 = tk.Entry(self, width = 4, highlightthickness=0)
        self.rsmEn3.insert(0, 1.0)
        self.rsmEn3.place(relx=.83, rely=.65, anchor='w')

        # self.rsmEn4 = tk.Entry(self, width = 4, highlightthickness=0)
        # self.rsmEn4.insert(0, 1.0)
        # self.rsmEn4.place(relx=.83, rely=.55, anchor='w')

        #tk.Label(self, text="Temp. (K)", bg='#b4d9cc').place(relx=.15, rely=.75, anchor='center')
        tk.Label(self, text="Temp. (K)", bg='#b4d9cc').place(relx=.65, rely=.25, anchor='e')
        tk.Label(self, text="Either 1 temp or a range with 2 temps.", font=("Arial", 9), fg='red', bg='#b4d9cc').place(relx=.63, rely=.31, anchor='center')
        tk.Label(self, text="Separate temps with a comma.", font=("Arial", 9), fg='red', bg='#b4d9cc').place(relx=.63, rely=.355, anchor='center')
        tk.Label(self, text="Temp. Increment", bg='#b4d9cc').place(relx=.65, rely=.45, anchor='e')
        tk.Label(self, text="Only for a temp. range.", font=("Arial", 9), fg='red', bg='#b4d9cc').place(relx=.63, rely=.51, anchor='center')


        # self.tempEn = tk.Entry(self, width = 5, highlightthickness=0)
        # self.tempEn.insert(0, 298.15)
        # self.tempEn.place(relx=.21, rely=.75, anchor='w')

        self.rangeEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.rangeEn.place(relx=.75, rely=.25, anchor='e')

        self.incEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.incEn.insert(0, 1)
        self.incEn.place(relx=.75, rely=.45, anchor='e')

        self.calculate = Button(self, text="Calculate!", command=lambda:self.ready(), width = 100, state='disabled', bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", disabledbackground="#89c0b6", disabledforeground='white', focuscolor='#448c8a')
        self.calculate.place(relx=.75, rely=.85, anchor='center')

class EIE(tk.Frame):

    def validate(self):
        self.error = tk.Label(self, text="", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        try:
            if float(self.freqEn.get()) <= 0:
                self.error = tk.Label(self, text = "The frequency scaling factor should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        except ValueError:
            self.error = tk.Label(self, text = "The frequency scaling factor should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        try:
            if float(self.rsmEn1.get()) <= 0 or float(self.rsmEn2.get()) <= 0:
                self.error = tk.Label(self, text="The rotational symmetry number should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        except ValueError:
            self.error = tk.Label(self, text="The rotational symmetry number should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        try:
            if float(self.tempEn.get()) < 0:
                self.error = tk.Label(self, text="The temperature should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        except ValueError:
            self.error = tk.Label(self, text="The temperature should be greater than 0.", fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        try:
            if float(self.incEn.get()) <= 0 or float(self.incEn.get()) > float(self.rangeEn.get()):
                self.error = tk.Label(self, text = "The temperature increment should be greater than 0 and less than the temperature range.", font=("Arial", 12), fg='red', bg='#b4d9cc').place(relx=.5, rely =.03, anchor='center')
        except ValueError:
            print("set default values for temp increment and range")# set default values for the two

    def open_file(self, num):
        file = askopenfile(mode='r', title="Select a .log file")
        if file:
            if '.log' in file.name:
                self.error = tk.Label(self, text="The file should have a .log extension", fg='#b4d9cc', bg='#b4d9cc').place(relx=.5, rely=.05, anchor='center')
                if num == 0:
                    self.file1 = file
                    self.browse1.set("Uploaded")
                else:
                    self.file2 = file
                    self.browse2.set("Uploaded")
            else:
                self.error = tk.Label(self, text="The file should have a .log extension", fg='red', bg='#b4d9cc').place(relx=.5, rely=.05, anchor='center')

        
        if(self.file1 and self.file2):
            self.calculate['state'] = 'normal'

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
       
        self.configure(bg='#b4d9cc')
        self.error = None
        self.file1 = None
        self.file2 = None
        self.browse1 = tk.StringVar()
        self.browse2 = tk.StringVar()
        self.browse1.set("Browse")
        self.browse2.set("Browse")

        tk.Label(self, text="EIE Calculations!", font=LARGE_FONT, bg='#b4d9cc').place(relx=.5, rely=.12, anchor='center')
        Button(self, text="Back", command=lambda:controller.show_frame(StartPage), width = 50, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.01, rely=.05, anchor='w')
        tk.Label(self, text="Ground State Log or Freqchk File #1", bg='#b4d9cc').place(relx=.5, rely=.3, anchor='e')
        tk.Label(self, text="Ground State Log or Freqchk File #2", bg='#b4d9cc').place(relx=.5, rely=.45, anchor='e')
        tk.Label(self, text="Frequency Scaling Factor", bg='#b4d9cc').place(relx=.5, rely=.6, anchor='e')
        tk.Label(self, text="σ - Rotational", bg='#b4d9cc').place(relx=.8, rely =.12, anchor='w')
        tk.Label(self, text="Symmetry Number", bg='#b4d9cc').place(relx=.775, rely =.18, anchor='w')
        
        #make list
        Button(self, textvariable=self.browse1, command=lambda:self.open_file(0), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.65, rely=.3, anchor='center')
        Button(self, textvariable=self.browse2, command=lambda:self.open_file(1), width=100, bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", focuscolor='#448c8a').place(relx=.65, rely=.45, anchor='center')
        
        self.freqEn = tk.Entry(self, width = 4, highlightthickness=0)
        self.freqEn.insert(0, 1.0)
        self.freqEn.place(relx=.64, rely=.6, anchor='e')

        #make list
        self.rsmEn1 = tk.Entry(self, width = 4, highlightthickness=0)
        self.rsmEn1.insert(0, 1.0)
        self.rsmEn1.place(relx=.83, rely=.3, anchor='w')

        self.rsmEn2 = tk.Entry(self, width = 4, highlightthickness=0)
        self.rsmEn2.insert(0, 1.0)
        self.rsmEn2.place(relx=.83, rely=.45, anchor='w')

        tk.Label(self, text="Temp. (K)", bg='#b4d9cc').place(relx=.15, rely=.75, anchor='center')
        tk.Label(self, text="Temp. Range (K)", bg='#b4d9cc').place(relx=.45, rely=.75, anchor='center')
        tk.Label(self, text="Increment", bg='#b4d9cc').place(relx=.75, rely=.75, anchor='center')

        self.tempEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.tempEn.insert(0, 298.15)
        self.tempEn.place(relx=.21, rely=.75, anchor='w')

        self.rangeEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.rangeEn.place(relx=.536, rely=.75, anchor='w')

        self.incEn = tk.Entry(self, width = 5, highlightthickness=0)
        self.incEn.place(relx=.81, rely=.75, anchor='w')

        self.calculate = Button(self, text="Calculate!", command=lambda:self.validate(), width = 100, state='disabled', bg='#448c8a', fg='white', borderless=1, activebackground="#89c0b6", disabledbackground="#89c0b6", disabledforeground='white', focuscolor='#448c8a')
        self.calculate.place(relx=.5, rely=.9, anchor='center')

    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.error = None
        self.configure(bg='#b4d9cc')
        self.browse1_text = tk.StringVar()
        self.browse2_text = tk.StringVar()
        self.label1_text = tk.StringVar()
        self.label2_text = tk.StringVar()
        self.browse1_text.set("Browse")
        self.browse2_text.set("Browse")
        self.label1_text.set("")
        self.label2_text.set("")
        self.file1 = None
        self.file2 = None
        tk.Label(self, textvariable=self.label1_text, bg='#b4d9cc').place(relx=.8, rely=.4, anchor='w')
        tk.Label(self, textvariable=self.label2_text, bg='#b4d9cc').place(relx=.8, rely=.6, anchor='w')
        tk.Label(self, text="EIE Calculations!", font=LARGE_FONT, bg='#b4d9cc').place(relx=.5, rely=.2, anchor='center')
        tk.Label(self, text="Ground State Log or Freqchk File #1", bg='#b4d9cc').place(relx=.5, rely=.4, anchor='e')
        Button(self, textvariable=self.browse1_text, command=lambda:self.open_file(1), width=100, bg='#448c8a', fg='white', borderless=1, overbackground="#89c0b6").place(relx=.7, rely=.4, anchor='center')
        tk.Label(self, text="Ground State Log or Freqchk File #2", bg='#b4d9cc').place(relx=.5, rely=.6, anchor='e')
        Button(self, textvariable=self.browse2_text, command=lambda:self.open_file(2), width=100, bg='#448c8a', fg='white', borderless=1, overbackground="#89c0b6").place(relx=.7, rely=.6, anchor='center')
        self.calculate = Button(self, text="Calculate!", command=lambda:self.doStuff(), width = 100, state='disabled', bg='#448c8a', fg='white', borderless=1, overbackground="#89c0b6", disabledbackground="#89c0b6", disabledforeground='white')
        self.calculate.place(relx=.5, rely=.85, anchor='center')
        Button(self, text="Back", command=lambda:controller.show_frame(StartPage), width = 50, bg='#448c8a', fg='white', borderless=1, overbackground="#89c0b6").place(relx=.01, rely=.05, anchor='w')     
    """
app = QuiverHS()
app.geometry("600x300")
app.mainloop()