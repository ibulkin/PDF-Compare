import tkinter as tk
from tkinter import filedialog
import fitz  # pymupdf

def get_page_object_count(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    count = len(page.get_drawings()) + len(page.get_text("blocks"))
    doc.close()
    return count

root = tk.Tk()
root.withdraw()
file1 = filedialog.askopenfilename(title="Выбери первый PDF")
file2 = filedialog.askopenfilename(title="Выбери второй PDF")

if not file1 or not file2:
    print("Файл(ы) не выбран(ы)")
    exit()

count1 = get_page_object_count(file1)
count2 = get_page_object_count(file2)

print(f"В первом PDF объектов: {count1}")
print(f"Во втором PDF объектов: {count2}")

if count1 == count2:
    print("Количество объектов совпадает.")
else:
    print("Количество объектов отличается!")