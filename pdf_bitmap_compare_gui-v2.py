import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz
from PIL import Image, ImageTk
import io
import cv2
import numpy as np

LANGUAGES = {
    "ru": {
        "choose": "Выбрать PDF",
        "compare": "Сравнить",
        "fit": "Отобразить на всю страницу",
        "scale": "Масштаб",
        "about": "О программе",
        "about_msg": "PDF Bitmap Compare PRO\n2024–2025\nДля Игоря",
        "diffs": "Отличия",
        "original": "ОРИГИНАЛЬНЫЙ PDF",
        "final": "ФИНАЛЬНЫЙ PDF",
        "lang": "Язык",
        "select_orig": "Выберите ОРИГИНАЛЬНЫЙ PDF",
        "select_final": "Выберите ФИНАЛЬНЫЙ PDF",
        "files_chosen": "Файлы выбраны.",
        "must_choose": "Нужно выбрать два файла.",
    },
    "en": {
        "choose": "Choose PDF",
        "compare": "Compare",
        "fit": "Fit to Window",
        "scale": "Scale",
        "about": "About",
        "about_msg": "PDF Bitmap Compare PRO\n2024–2025\nFor Igor",
        "diffs": "Differences",
        "original": "ORIGINAL PDF",
        "final": "FINAL PDF",
        "lang": "Language",
        "select_orig": "Select ORIGINAL PDF",
        "select_final": "Select FINAL PDF",
        "files_chosen": "Files chosen.",
        "must_choose": "You must choose two files.",
    },
    "he": {
        "choose": "בחר PDF",
        "compare": "השווה",
        "fit": "התאם למסך",
        "scale": "קנה מידה",
        "about": "אודות",
        "about_msg": "PDF Bitmap Compare PRO\n2024–2025\nלאיגור",
        "diffs": "הבדלים",
        "original": "PDF מקורי",
        "final": "PDF סופי",
        "lang": "שפה",
        "select_orig": "בחר PDF מקורי",
        "select_final": "בחר PDF סופי",
        "files_chosen": "הקבצים נבחרו.",
        "must_choose": "עליך לבחור שני קבצים.",
    },
}

def tr(key, lang):
    return LANGUAGES[lang].get(key, key)

class PDFBitmapCompareApp:
    def __init__(self, root):
        self.root = root
        self.language = "ru"
        self.root.title("PDF Bitmap Compare PRO")
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
        self.init_ui()
        self.bind_hand_mode()
        self.root.bind("<Configure>", self.on_resize)

    def init_ui(self):
        control_frame = tk.Frame(self.root, bg="#ededed")
        control_frame.pack(fill="x", padx=8, pady=4)

        # Язык
        ttk.Label(control_frame, text=tr("lang", self.language)).pack(side="right", padx=3)
        self.lang_var = tk.StringVar(value=self.language)
        self.lang_menu = ttk.Combobox(control_frame, textvariable=self.lang_var, values=list(LANGUAGES.keys()), width=4, state="readonly")
        self.lang_menu.pack(side="right")
        self.lang_menu.bind("<<ComboboxSelected>>", self.change_language)

        self.btn_about = tk.Button(control_frame, text=tr("about", self.language), command=self.show_about)
        self.btn_about.pack(side="right", padx=12)

        self.btn_choose = tk.Button(control_frame, text=tr("choose", self.language), command=self.choose_files)
        self.btn_choose.pack(side="left")
        self.btn_compare = tk.Button(control_frame, text=tr("compare", self.language), command=self.compare)
        self.btn_compare.pack(side="left", padx=10)
        self.btn_fit = tk.Button(control_frame, text=tr("fit", self.language), command=self.fit_to_window)
        self.btn_fit.pack(side="left", padx=10)

        self.zoom_slider = tk.Scale(control_frame, from_=3.0, to=6.0, resolution=0.05, orient="horizontal",
                                    label=tr("scale", self.language), command=self.update_zoom)
        self.zoom_slider.set(3.0)
        self.zoom_slider.pack(side="left", padx=10)
        self.status = tk.Label(control_frame, text="", bg="#ededed")
        self.status.pack(side="left", padx=10)

        canv_frame = tk.Frame(self.root)
        canv_frame.pack(fill="both", expand=True)
        canv_frame.rowconfigure(0, weight=1)
        canv_frame.rowconfigure(1, weight=1)
        canv_frame.columnconfigure(0, weight=1)
        self.canv_frame = canv_frame

        # Верхний Canvas (Оригинал)
        self.canvas_original = tk.Canvas(canv_frame, bg="white", cursor="arrow", highlightthickness=0)
        self.canvas_original.grid(row=0, column=0, sticky="nsew")
        self.canvas_original.bind("<Button-1>", self.on_canvas_click)
        self.scrollbar_orig_y = tk.Scrollbar(canv_frame, orient="vertical", command=self.canvas_original.yview)
        self.scrollbar_orig_x = tk.Scrollbar(canv_frame, orient="horizontal", command=self.canvas_original.xview)
        self.canvas_original.config(yscrollcommand=self.scrollbar_orig_y.set, xscrollcommand=self.scrollbar_orig_x.set)
        self.scrollbar_orig_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_orig_x.grid(row=1, column=0, sticky="ew")
        self.lbl_original = tk.Label(self.canvas_original, text=tr("original", self.language), bg="#ffffff", font=("Arial", 12, "bold"))
        self.canvas_original.create_window(15, 8, window=self.lbl_original, anchor="nw")

        # Нижний Canvas (Финальный)
        self.canvas_final = tk.Canvas(canv_frame, bg="white", cursor="arrow", highlightthickness=0)
        self.canvas_final.grid(row=2, column=0, sticky="nsew")
        self.canvas_final.bind("<Button-1>", self.on_canvas_click)
        self.scrollbar_fin_y = tk.Scrollbar(canv_frame, orient="vertical", command=self.canvas_final.yview)
        self.scrollbar_fin_x = tk.Scrollbar(canv_frame, orient="horizontal", command=self.canvas_final.xview)
        self.canvas_final.config(yscrollcommand=self.scrollbar_fin_y.set, xscrollcommand=self.scrollbar_fin_x.set)
        self.scrollbar_fin_y.grid(row=2, column=1, sticky="ns")
        self.scrollbar_fin_x.grid(row=3, column=0, sticky="ew")
        self.lbl_final = tk.Label(self.canvas_final, text=tr("final", self.language), bg="#ffffff", font=("Arial", 12, "bold"))
        self.canvas_final.create_window(15, 8, window=self.lbl_final, anchor="nw")

        canv_frame.rowconfigure(0, weight=1)
        canv_frame.rowconfigure(2, weight=1)
        canv_frame.columnconfigure(0, weight=1)

    def show_about(self):
        messagebox.showinfo(tr("about", self.language), tr("about_msg", self.language))

    def on_resize(self, event):
        h = max(1, self.canv_frame.winfo_height())
        w = max(1, self.canv_frame.winfo_width())
        h_each = max(1, (h - 20) // 2)
        self.canvas_original.config(width=w-20, height=h_each)
        self.canvas_final.config(width=w-20, height=h_each)
        if self.tk_img_original:
            self.display_image(self.canvas_original, self.tk_img_original)
        if self.tk_img_final:
            self.display_image(self.canvas_final, self.tk_img_final)

    def bind_hand_mode(self):
        self.root.bind("<space>", self.activate_hand_mode)
        self.root.bind("<KeyRelease-space>", self.deactivate_hand_mode)

    def activate_hand_mode(self, event):
        self._hand_mode = True
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.config(cursor="hand2")
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
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def pan(self, event):
        dx = self._drag_data["x"] - event.x
        dy = self._drag_data["y"] - event.y
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.xview_scroll(int(dx), "units")
            canvas.yview_scroll(int(dy), "units")
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def choose_files(self):
        self.status.config(text=tr("select_orig", self.language))
        file1 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file1: return
        self.pdf_paths[0] = file1

        self.status.config(text=tr("select_final", self.language))
        file2 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file2: return
        self.pdf_paths[1] = file2

        self.status.config(text=tr("files_chosen", self.language))
        self.auto_fit_to_window()

    def get_fit_scale(self):
        doc1 = fitz.open(self.pdf_paths[0])
        doc2 = fitz.open(self.pdf_paths[1])
        page1, page2 = doc1[0], doc2[0]
        width1, height1 = page1.rect.width, page1.rect.height
        width2, height2 = page2.rect.width, page2.rect.height
        doc1.close()
        doc2.close()
        canv_height = max(1, self.canv_frame.winfo_height() // 2)
        canv_width = max(1, self.canv_frame.winfo_width())
        k1 = min(canv_width / width1, canv_height / height1)
        k2 = min(canv_width / width2, canv_height / height2)
        k = min(k1, k2, 3.0)
        return k

    def auto_fit_to_window(self):
        k = self.get_fit_scale()
        self.scale_factor = k
        self.zoom_slider.set(round(k, 2))
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
        # подпись над Canvas
        if canvas == self.canvas_original:
            canvas.create_window(15, 8, window=self.lbl_original, anchor="nw")
        elif canvas == self.canvas_final:
            canvas.create_window(15, 8, window=self.lbl_final, anchor="nw")

    def compare(self):
        gray1 = cv2.cvtColor(self.cv_img_original, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.cv_img_final, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(cnt) for cnt in contours]
        boxes = self.merge_boxes(boxes, min_distance=20)
        self.diff_boxes = [(x / self.scale_factor, y / self.scale_factor, w / self.scale_factor, h / self.scale_factor) for (x, y, w, h) in boxes]
        self.active_box_idx = None
        self.update_status()
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

    def update_zoom(self, val):
        prev_scale = self.scale_factor
        self.scale_factor = float(val)
        centers = []
        for canvas in [self.canvas_original, self.canvas_final]:
            width = int(canvas.winfo_width())
            height = int(canvas.winfo_height())
            cx = canvas.canvasx(width // 2) / prev_scale
            cy = canvas.canvasy(height // 2) / prev_scale
            centers.append((cx, cy))
        self.render_pdf_images()
        for idx, canvas in enumerate([self.canvas_original, self.canvas_final]):
            width = int(canvas.winfo_width())
            height = int(canvas.winfo_height())
            img_width = canvas.image.width()
            img_height = canvas.image.height()
            cx, cy = centers[idx]
            x0 = max(0, (cx * self.scale_factor - width // 2) / (img_width - width + 1))
            y0 = max(0, (cy * self.scale_factor - height // 2) / (img_height - height + 1))
            canvas.xview_moveto(x0)
            canvas.yview_moveto(y0)
        self.update_status()

    def fit_to_window(self):
        self.auto_fit_to_window()
        self.update_status()

    def update_status(self):
        text = f"{tr('diffs', self.language)}: {len(self.diff_boxes)}"
        self.status.config(text=text)
        self.zoom_slider.config(label=f"{tr('scale', self.language)}")

    def change_language(self, event):
        self.language = self.lang_var.get()
        self.btn_about.config(text=tr("about", self.language))
        self.btn_choose.config(text=tr("choose", self.language))
        self.btn_compare.config(text=tr("compare", self.language))
        self.btn_fit.config(text=tr("fit", self.language))
        self.lbl_original.config(text=tr("original", self.language))
        self.lbl_final.config(text=tr("final", self.language))
        self.status.config(text=f"{tr('diffs', self.language)}: {len(self.diff_boxes)}")
        self.zoom_slider.config(label=tr("scale", self.language))
        self.lang_menu.set(self.language)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1300x1000")
    root.minsize(800, 700)
    app = PDFBitmapCompareApp(root)
    root.mainloop()