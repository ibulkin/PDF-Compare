import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
file = filedialog.askopenfilename()
print("Файл выбран:", file)
# root.destroy()  # Можно раскомментировать