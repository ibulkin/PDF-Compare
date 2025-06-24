import tkinter as tk
from tkinter import filedialog

def main():
    root = tk.Tk()
    root.withdraw()  # Не показываем главное окно

    # Открываем диалог выбора файла
    filename = filedialog.askopenfilename(
        title="Выберите PDF-файл",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    print("Файл выбран:", filename)

if __name__ == "__main__":
    main()