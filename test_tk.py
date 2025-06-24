import tkinter as tk

root = tk.Tk()
root.title("Тестовое окно")
label = tk.Label(root, text="Всё работает!")
label.pack(padx=50, pady=50)
root.mainloop()