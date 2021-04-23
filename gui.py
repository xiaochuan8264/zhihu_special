import tkinter as tk
import tkinter.filedialog, os

class window():
    def __init__(self):
        self.path = ''
        self.filename = ''
        self.window = tk.Tk()
        self.window.title('打开待分析文件')
        self.window.geometry('500x300')
        self.path_var = tk.StringVar()
        self.choice = tk.Button(self.window,text='目标文件', command=self.openFile)
        self.choice.pack()
        self.window.mainloop()

    def openFile(self):
        f = tk.filedialog.askopenfilename(filetypes=[('Html文件','.html')])
        self.path_var.set(f)
        self.path = self.path_var.get()
        self.filename = os.path.splitext(self.path.split('/')[-1])[0]
        self.choice.destroy()
        finish = tk.Button(self.window,text='开始程序', command=self.start)
        finish.pack()

    def start(self):
        self.window.destroy()

if __name__ == "__main__":
    win = window()
