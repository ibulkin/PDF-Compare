import tkinter as tk
from tkinter import filedialog
import fitz  # pymupdf
from PIL import Image, ImageTk
import io

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Выбери PDF для предпросмотра")
print("Файл выбран:", file_path)

if file_path:
    doc = fitz.open(file_path)
    page = doc.load_page(0)  # первая страница
    pix = page.get_pixmap()
    img_data = pix.tobytes("png")

    # Создаём окно для показа картинки
    img = Image.open(io.BytesIO(img_data))
    tk_img = ImageTk.PhotoImage(img)
    win = tk.Toplevel()
    win.title("Превью первой страницы PDF")
    label = tk.Label(win, image=tk_img)
    label.pack()
    print("Окно с превью открыто, закрой его для завершения программы.")

    # Не закрывать окно сразу!
    win.mainloop()
    doc.close()
else:
    print("Файл не выбран.")