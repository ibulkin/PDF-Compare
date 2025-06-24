import tkinter as tk
from tkinter import filedialog
import fitz  # pymupdf

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Выбери PDF для чтения")
print("Файл выбран:", file_path)

if file_path:
    try:
        doc = fitz.open(file_path)
        print("PDF успешно открыт, страниц:", doc.page_count)
        doc.close()
    except Exception as e:
        print("Ошибка при открытии PDF:", e)

root.destroy()