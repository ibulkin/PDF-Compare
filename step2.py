import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()  # Скрыть главное окно

file_path = filedialog.askopenfilename(title="Выбери файл для теста")
print("Файл выбран:", file_path)

root.destroy()