import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz
from PIL import Image, ImageTk
import io
import cv2
import numpy as np
import os
import platform

LANGUAGES = {
    "ru": {
        "choose_pdf": "Выбрать PDF",
        "compare": "Сравнить",
        "clear": "Сбросить",
        "fit": "На весь экран",
        "scale": "Масштаб",
        "status_selected": "Файлы выбраны.",
        "status_choose1": "Выберите ОРИГИНАЛЬНЫЙ PDF",
        "status_choose2": "Выберите ФИНАЛЬНЫЙ PDF",
        "original_file": "ОРИГИНАЛЬНЫЙ ФАЙЛ",
        "final_file": "ФИНАЛЬНЫЙ ФАЙЛ",
        "diff_count": "Отличий найдено: {}",
        "about_title": "О программе",
        "about_body": "PDF Bitmap Compare PRO\nАвтор: Игорь (2025)\nДля профессионального сравнения PDF-графики на Mac.\nВсе права защищены.",
        "lang": "Язык"
    },
    "en": {
        "choose_pdf": "Choose PDF",
        "compare": "Compare",
        "clear": "Clear",
        "fit": "Fit to Window",
        "scale": "Scale",
        "status_selected": "Files selected.",
        "status_choose1": "Select ORIGINAL PDF",
        "status_choose2": "Select FINAL PDF",
        "original_file": "ORIGINAL FILE",
        "final_file": "FINAL FILE",
        "diff_count": "Differences found: {}",
        "about_title": "About",
        "about_body": "PDF Bitmap Compare PRO\nAuthor: Igor (2025)\nFor professional PDF graphics comparison on Mac.\nAll rights reserved.",
        "lang": "Language"
    },
    "he": {
        "choose_pdf": "בחר PDF",
        "compare": "השווה",
        "clear": "נקה",
        "fit": "התאם למסך",
        "scale": "קנה מידה",
        "status_selected": "קבצים נבחרו.",
        "status_choose1": "בחר PDF מקורי",
        "status_choose2": "בחר PDF סופי",
        "original_file": "קובץ מקורי",
        "final_file": "קובץ סופי",
        "diff_count": "הבדלים נמצאו: {}",
        "about_title": "אודות",
        "about_body": "PDF Bitmap Compare PRO\nמאת: איגור (2025)\nלהשוואת גרפיקה PDF מקצועית במק.\nכל הזכויות שמורות.",
        "lang": "שפה"
    }
}

class PDFBitmapCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Bitmap Compare PRO")
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{int(sw*0.95)}x{int(sh*0.92)}+10+20")
        root.minsize(800, 700)
        self.language = "ru"
        self.pdf_paths = [None, None]
        self.scale_factor = 3.0
        self.tk_img_original = None
        self.tk_img_final = None
        self.cv_img_original = None
        self.cv_img_final = None
        self.diff_boxes = []
        self.active_box_idx = None
        self._drag_data = {"x": 0, "y": 0}
        self._hand_mode = False
        self._canvas_offset = [0, 0]
        self._is_panning = False
        self.create_ui()
        self.bind_hand_mode()
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit)

    def tr(self, key):
        return LANGUAGES[self.language][key]

    def set_language(self, lang):
        self.language = lang
        self.update_labels()

    def update_labels(self):
        self.btn_choose.config(text=self.tr("choose_pdf"))
        self.btn_compare.config(text=self.tr("compare"))
        self.btn_clear.config(text=self.tr("clear"))
        self.btn_fit.config(text=self.tr("fit"))
        self.label_original.config(text=self.tr("original_file"))
        self.label_final.config(text=self.tr("final_file"))
        self.status.config(text=self.tr("status_selected"))
        self.menu_lang.entryconfig(0, label="Русский")
        self.menu_lang.entryconfig(1, label="English")
        self.menu_lang.entryconfig(2, label="עברית")
        self.menu_help.entryconfig(0, label=self.tr("about_title"))
        self.scale_label.config(text=self.tr("scale"))

    def create_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Arial", 13), padding=6)
        style.configure("TLabel", background="#F8F8F8", font=("Arial", 14))
        style.configure("Header.TLabel", font=("Arial", 15, "bold"), background="#F1F1F1")
        style.configure("Status.TLabel", font=("Arial", 14), background="#F8F8F8", foreground="#357b3c")
        style.configure("TFrame", background="#F8F8F8")
        style.configure("Border.TFrame", background="#F8F8F8", borderwidth=2, relief="groove")
        style.configure("Separator.TFrame", background="#DADADA")

        # --- Меню ---
        menubar = tk.Menu(self.root)
        self.menu_lang = tk.Menu(menubar, tearoff=0)
        self.menu_lang.add_command(label="Русский", command=lambda: self.set_language("ru"))
        self.menu_lang.add_command(label="English", command=lambda: self.set_language("en"))
        self.menu_lang.add_command(label="עברית", command=lambda: self.set_language("he"))
        menubar.add_cascade(label=self.tr("lang"), menu=self.menu_lang)
        self.menu_help = tk.Menu(menubar, tearoff=0)
        self.menu_help.add_command(label=self.tr("about_title"), command=self.show_about)
        menubar.add_cascade(label="Help", menu=self.menu_help)
        self.root.config(menu=menubar)

        # --- Верхняя панель управления ---
        control_frame = ttk.Frame(self.root, padding=(10, 7))
        control_frame.pack(fill="x", padx=0, pady=(0,0))
        self.btn_choose = ttk.Button(control_frame, text=self.tr("choose_pdf"), command=self.choose_files)
        self.btn_choose.pack(side="left", padx=4)
        self.btn_compare = ttk.Button(control_frame, text=self.tr("compare"), command=self.compare)
        self.btn_compare.pack(side="left", padx=4)
        self.btn_clear = ttk.Button(control_frame, text=self.tr("clear"), command=self.clear_boxes)
        self.btn_clear.pack(side="left", padx=4)
        self.btn_fit = ttk.Button(control_frame, text=self.tr("fit"), command=self.fit_to_window)
        self.btn_fit.pack(side="left", padx=4)
        self.status = ttk.Label(control_frame, text=self.tr("status_selected"), style="Status.TLabel")
        self.status.pack(side="left", padx=14)
        ttk.Separator(self.root, orient="horizontal").pack(fill="x")

        # --- Масштаб ---
        self.scale_label = ttk.Label(control_frame, text=self.tr("scale"))
        self.scale_label.pack(side="left", padx=(40,2))
        self.zoom_var = tk.DoubleVar(value=3.0)
        self.zoom_slider = ttk.Scale(control_frame, from_=1.0, to=6.0, variable=self.zoom_var, orient="horizontal", command=self.update_zoom, length=180)
        self.zoom_slider.pack(side="left", padx=4)
        self.zoom_val_label = ttk.Label(control_frame, text="3.00x")
        self.zoom_val_label.pack(side="left", padx=2)

        # --- Основная область ---
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=6, pady=5)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- ОРИГИНАЛ ---
        frame_original = ttk.Frame(main_frame, style="Border.TFrame")
        frame_original.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0,4))
        self.label_original = ttk.Label(frame_original, text=self.tr("original_file"), style="Header.TLabel", anchor="center")
        self.label_original.pack(fill="x", padx=2, pady=(2, 1))
        self.canvas_original = tk.Canvas(frame_original, bg="#fff", highlightthickness=0, cursor="arrow", bd=0, relief="flat")
        self.canvas_original.pack(fill="both", expand=True, padx=7, pady=(0,7))
        self.canvas_original.bind("<Button-1>", self.on_canvas_click)

        # --- ФИНАЛЬНЫЙ ---
        frame_final = ttk.Frame(main_frame, style="Border.TFrame")
        frame_final.grid(row=1, column=0, sticky="nsew", padx=0, pady=(4,0))
        self.label_final = ttk.Label(frame_final, text=self.tr("final_file"), style="Header.TLabel", anchor="center")
        self.label_final.pack(fill="x", padx=2, pady=(2, 1))
        self.canvas_final = tk.Canvas(frame_final, bg="#fff", highlightthickness=0, cursor="arrow", bd=0, relief="flat")
        self.canvas_final.pack(fill="both", expand=True, padx=7, pady=(0,7))
        self.canvas_final.bind("<Button-1>", self.on_canvas_click)

    def show_about(self):
        messagebox.showinfo(self.tr("about_title"), self.tr("about_body"))

    def on_resize(self, event):
        if self.tk_img_original:
            self.display_image(self.canvas_original, self.tk_img_original)
        if self.tk_img_final:
            self.display_image(self.canvas_final, self.tk_img_final)

    def bind_hand_mode(self):
        self.root.bind("<space>", self.activate_hand_mode)
        self.root.bind("<KeyRelease-space>", self.deactivate_hand_mode)

    def activate_hand_mode(self, event):
        self._hand_mode = True
        # --- Системная рука для macOS и Windows/Linux ---
        if platform.system() == "Windows" and os.path.exists("hand.png"):
            try:
                self.canvas_original.config(cursor="@hand.png")
                self.canvas_final.config(cursor="@hand.png")
            except:
                self.canvas_original.config(cursor="hand2")
                self.canvas_final.config(cursor="hand2")
        else:
            self.canvas_original.config(cursor="hand2")
            self.canvas_final.config(cursor="hand2")
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.bind("<ButtonPress-1>", self.start_pan)
            canvas.bind("<B1-Motion>", self.pan)

    def deactivate_hand_mode(self, event):
        self._hand_mode = False
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.config(cursor="arrow")
            canvas.unbind("<ButtonPress-1>")
            canvas.unbind("<B1-Motion>")
            canvas.bind("<Button-1>", self.on_canvas_click)

    def start_pan(self, event):
        self._is_panning = True
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._canvas_offset = [
            self.canvas_original.xview()[0] if self.canvas_original.xview() else 0,
            self.canvas_original.yview()[0] if self.canvas_original.yview() else 0,
        ]

    def pan(self, event):
        if not self._is_panning:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        canvases = [self.canvas_original, self.canvas_final]
        for canvas in canvases:
            x0, x1 = canvas.xview()
            y0, y1 = canvas.yview()
            scroll_x = -dx / canvas.winfo_width()
            scroll_y = -dy / canvas.winfo_height()
            new_x = min(max(self._canvas_offset[0] + scroll_x, 0), 1)
            new_y = min(max(self._canvas_offset[1] + scroll_y, 0), 1)
            canvas.xview_moveto(new_x)
            canvas.yview_moveto(new_y)

    def choose_files(self):
        self.status.config(text=self.tr("status_choose1"))
        file1 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file1: return
        self.pdf_paths[0] = file1

        self.status.config(text=self.tr("status_choose2"))
        file2 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file2: return
        self.pdf_paths[1] = file2

        self.status.config(text=self.tr("status_selected"))
        self.fit_to_window()

    def fit_to_window(self):
        if not all(self.pdf_paths):
            return
        doc1, doc2 = fitz.open(self.pdf_paths[0]), fitz.open(self.pdf_paths[1])
        w1, h1 = doc1[0].rect.width, doc1[0].rect.height
        w2, h2 = doc2[0].rect.width, doc2[0].rect.height
        cw = self.canvas_original.winfo_width() if self.canvas_original.winfo_width() > 0 else 1200
        ch = self.canvas_original.winfo_height() if self.canvas_original.winfo_height() > 0 else 500
        cf = self.canvas_final.winfo_height() if self.canvas_final.winfo_height() > 0 else 500
        max_w = max(w1, w2)
        max_h = max(h1, h2)
        zoom_w = cw / max_w
        zoom_h = (ch + cf) / (h1 + h2)
        zoom = min(zoom_w, zoom_h)
        zoom = max(1.0, min(zoom, 6.0))
        self.scale_factor = zoom
        self.zoom_var.set(zoom)
        self.zoom_val_label.config(text=f"{self.scale_factor:.2f}x")
        self.render_pdf_images()
        doc1.close()
        doc2.close()

    def update_zoom(self, val):
        try:
            self.scale_factor = float(val)
        except Exception:
            self.scale_factor = 3.0
        self.zoom_val_label.config(text=f"{self.scale_factor:.2f}x")
        self.render_pdf_images()

    def render_pdf_images(self):
        self.tk_img_original, self.cv_img_original = self.render_pdf_image(self.pdf_paths[0])
        self.tk_img_final, self.cv_img_final = self.render_pdf_image(self.pdf_paths[1])
        self.display_image(self.canvas_original, self.tk_img_original)
        self.display_image(self.canvas_final, self.tk_img_final)

    def render_pdf_image(self, pdf_path):
        doc = fitz.open(pdf_path)
        page = doc[0]
        zoom_matrix = fitz.Matrix(self.scale_factor, self.scale_factor)
        pix = page.get_pixmap(matrix=zoom_matrix)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        cv_img = np.array(img)[:, :, ::-1]
        tk_img = ImageTk.PhotoImage(img)
        doc.close()
        return tk_img, cv_img

    def display_image(self, canvas, tk_img):
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.image = tk_img
        canvas.config(scrollregion=(0, 0, tk_img.width(), tk_img.height()))
        if self.diff_boxes:
            self.draw_diff_boxes()

    def compare(self):
        if not (self.cv_img_original is not None and self.cv_img_final is not None):
            return
        gray1 = cv2.cvtColor(self.cv_img_original, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.cv_img_final, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(cnt) for cnt in contours]
        boxes = self.merge_boxes(boxes, min_distance=20)
        self.diff_boxes = [(x / self.scale_factor, y / self.scale_factor, w / self.scale_factor, h / self.scale_factor) for (x, y, w, h) in boxes]
        self.active_box_idx = None
        self.status.config(text=self.tr("diff_count").format(len(self.diff_boxes)))
        self.render_pdf_images()
        self.draw_diff_boxes()

    def merge_boxes(self, boxes, min_distance=20):
        result = []
        for box in boxes:
            x, y, w, h = box
            found = False
            for i, (xx, yy, ww, hh) in enumerate(result):
                if abs(y - yy) < min_distance or abs((y + h) - (yy + hh)) < min_distance:
                    nx0 = min(x, xx)
                    ny0 = min(y, yy)
                    nx1 = max(x + w, xx + ww)
                    ny1 = max(y + h, yy + hh)
                    result[i] = (nx0, ny0, nx1 - nx0, ny1 - ny0)
                    found = True
                    break
            if not found:
                result.append(box)
        return result

    def draw_diff_boxes(self):
        for idx, (x, y, w, h) in enumerate(self.diff_boxes):
            x0, y0, x1, y1 = [c * self.scale_factor for c in (x, y, x + w, y + h)]
            color = "yellow" if idx == self.active_box_idx else "red"
            for canvas in [self.canvas_original, self.canvas_final]:
                canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=2, tags=f"diffbox_{idx}")

    def on_canvas_click(self, event):
        if self._hand_mode:
            return
        canvas = event.widget
        x = canvas.canvasx(event.x) / self.scale_factor
        y = canvas.canvasy(event.y) / self.scale_factor
        for idx, (bx, by, bw, bh) in enumerate(self.diff_boxes):
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self.active_box_idx = idx
                self.center_on_box(bx, by, bw, bh)
                self.draw_diff_boxes()
                break

    def center_on_box(self, x, y, w, h):
        for canvas in [self.canvas_original, self.canvas_final]:
            width = int(canvas.winfo_width())
            height = int(canvas.winfo_height())
            img_width = canvas.image.width()
            img_height = canvas.image.height()
            sx = max(0, ((x + w / 2) * self.scale_factor - width // 2) / (img_width - width + 1))
            sy = max(0, ((y + h / 2) * self.scale_factor - height // 2) / (img_height - height + 1))
            canvas.xview_moveto(sx)
            canvas.yview_moveto(sy)

    def clear_boxes(self):
        self.diff_boxes = []
        self.active_box_idx = None
        self.render_pdf_images()
        self.status.config(text=self.tr("status_selected"))

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFBitmapCompareApp(root)
    root.mainloop()
