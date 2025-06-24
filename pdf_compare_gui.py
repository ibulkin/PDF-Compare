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
        "about": "О программе",
        "about_msg": "PDF Bitmap Compare PRO\n2025\nIgor Bulkin© ibulkin@gmail.com",
        "diffs": "Отличия",
        "original": "ОРИГИНАЛЬНЫЙ PDF",
        "final": "ФИНАЛЬНЫЙ PDF",
        "lang": "Язык",
        "files_chosen": "Файлы выбраны.",
        "select_orig": "Выберите ОРИГИНАЛЬНЫЙ PDF",
        "select_final": "Выберите ФИНАЛЬНЫЙ PDF",
        "must_choose": "Нужно выбрать два файла.",
        "scale": "Масштаб",
        "minus": "-",
        "plus": "+",
        "zero": "0",
    },
    "en": {
        "choose": "Choose PDF",
        "compare": "Compare",
        "about": "About",
        "about_msg": "PDF Bitmap Compare PRO\n2025\nIgor Bulkin© ibulkin@gmail.com",
        "diffs": "Differences",
        "original": "ORIGINAL PDF",
        "final": "FINAL PDF",
        "lang": "Language",
        "files_chosen": "Files chosen.",
        "select_orig": "Select ORIGINAL PDF",
        "select_final": "Select FINAL PDF",
        "must_choose": "You must choose two files.",
        "scale": "Scale",
        "minus": "-",
        "plus": "+",
        "zero": "0",
    },
    "he": {
        "choose": "בחר PDF",
        "compare": "השווה",
        "about": "אודות",
        "about_msg": "PDF Bitmap Compare PRO\n2025\nאיגור בולקין© ibulkin@gmail.com",
        "diffs": "הבדלים",
        "original": "PDF מקורי",
        "final": "PDF סופי",
        "lang": "שפה",
        "files_chosen": "הקבצים נבחרו.",
        "select_orig": "בחר PDF מקורי",
        "select_final": "בחר PDF סופי",
        "must_choose": "יש לבחור שני קבצים.",
        "scale": "קנה מידה",
        "minus": "-",
        "plus": "+",
        "zero": "0",
    }
}

def tr(key, lang):
    return str(LANGUAGES[lang].get(key, key))

class PDFBitmapCompareApp:
    def __init__(self, root):
        self.root = root
        self.language = "ru"
        self.root.title("PDF Bitmap Compare PRO")
        self.root.configure(bg="#F3F3F3")
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.pdf_paths: list[str | None] = [None, None]  # type: ignore  # noqa
        self.tk_img_original = None
        self.tk_img_final = None
        self.cv_img_original = None
        self.cv_img_final = None
        self.diff_boxes = []
        self.show_diffs = False
        self.active_box_idx = None
        self.scale_percent = 0
        self.max_scale_percent = 120
        self.min_scale_percent = 0
        self._rendering = False
        self.fit_scale = 1.0
        self._hand_mode = False
        self._pan_data = {"drag": False, "x": 0, "y": 0}
        self.init_ui()
        self.root.bind("<KeyPress-space>", self.enable_hand_mode)
        self.root.bind("<KeyRelease-space>", self.disable_hand_mode)
        self.root.bind("<Configure>", self.on_resize)

    def init_ui(self):
        control_frame = tk.Frame(self.root, bg="#F3F3F3")
        control_frame.pack(fill="x", padx=12, pady=6)

        ttk.Label(control_frame, text=tr("lang", self.language)).pack(side="right", padx=3)
        self.lang_var = tk.StringVar(value=self.language)
        self.lang_menu = ttk.Combobox(control_frame, textvariable=self.lang_var, values=list(LANGUAGES.keys()), width=4, state="readonly")
        self.lang_menu.pack(side="right")
        self.lang_menu.bind("<<ComboboxSelected>>", self.change_language)

        self.btn_about = tk.Button(control_frame, text=tr("about", self.language), command=self.show_about, bg="#F3F3F3", relief="flat")
        self.btn_about.pack(side="right", padx=8)

        self.btn_choose = tk.Button(control_frame, text=tr("choose", self.language), command=self.choose_files, bg="#eaeaea", relief="groove")
        self.btn_choose.pack(side="left", padx=2)

        self.btn_compare = tk.Button(control_frame, text=tr("compare", self.language), command=self.toggle_compare, bg="#eaeaea", relief="groove")
        self.btn_compare.pack(side="left", padx=10)

        # --- Кнопки перехода по отличиям ---
        self.btn_prev_diff = tk.Button(control_frame, text="⟨", command=self.prev_diff, bg="#eaeaea", relief="groove")
        self.btn_prev_diff.pack(side="left", padx=2)
        self.btn_next_diff = tk.Button(control_frame, text="⟩", command=self.next_diff, bg="#eaeaea", relief="groove")
        self.btn_next_diff.pack(side="left", padx=2)

        scale_frame = tk.Frame(control_frame, bg="#F3F3F3")
        scale_frame.pack(side="left", padx=12)

        self.btn_minus = tk.Button(scale_frame, text=tr("minus", self.language), width=2, command=self.scale_minus, relief="groove")
        self.btn_minus.pack(side="left", padx=2)

        self.btn_zero = tk.Button(scale_frame, text=tr("zero", self.language), width=2, command=self.scale_reset, relief="groove")
        self.btn_zero.pack(side="left", padx=2)

        self.btn_plus = tk.Button(scale_frame, text=tr("plus", self.language), width=2, command=self.scale_plus, relief="groove")
        self.btn_plus.pack(side="left", padx=2)

        self.scale_label = tk.Label(scale_frame, text="100%", bg="#F3F3F3", font=("SF Pro Text", 12, "bold"))
        self.scale_label.pack(side="left", padx=6)

        self.status = tk.Label(control_frame, text="", bg="#F3F3F3", fg="#555555", font=("SF Pro Text", 11))
        self.status.pack(side="left", padx=18)

        canv_frame = tk.Frame(self.root, bg="#F3F3F3")
        canv_frame.pack(fill="both", expand=True)
        canv_frame.rowconfigure(0, weight=1)
        canv_frame.rowconfigure(1, weight=0)
        canv_frame.rowconfigure(2, weight=1)
        canv_frame.columnconfigure(0, weight=1)
        self.canv_frame = canv_frame

        # Верхний Canvas — оригинал
        self.canvas_original = tk.Canvas(canv_frame, bg="#f9f9f9", highlightthickness=0)
        self.canvas_original.grid(row=0, column=0, sticky="nsew")
        self.canvas_original.config(xscrollincrement=1, yscrollincrement=1)
        self.canvas_original.create_text(20, 20, text=str(tr("original", self.language)), anchor="nw", font=("SF Pro Text", 13, "bold"), fill="#222", tags="label")
        self.canvas_original.bind("<Button-1>", self.on_canvas_click)
        self.canvas_original.bind("<Enter>", lambda e: self.canvas_original.focus_set())
        # --- видимые скроллбары (ширина 2, цвет как фон) ---
        self.scrollbar_orig_y = tk.Scrollbar(
            canv_frame, orient="vertical", command=self.canvas_original.yview, width=2,
            troughcolor="#f9f9f9", bg="#f9f9f9", highlightthickness=0
        )
        self.scrollbar_orig_x = tk.Scrollbar(
            canv_frame, orient="horizontal", command=self.canvas_original.xview, width=2,
            troughcolor="#f9f9f9", bg="#f9f9f9", highlightthickness=0
        )
        self.canvas_original.config(yscrollcommand=self.scrollbar_orig_y.set, xscrollcommand=self.scrollbar_orig_x.set)
        self.scrollbar_orig_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_orig_x.grid(row=1, column=0, sticky="ew")
        self.canvas_original.config(yscrollcommand=self.sync_yview, xscrollcommand=self.sync_xview)

        # Разделитель
        self.divider = tk.Frame(canv_frame, height=2, bg="#222222")
        self.divider.grid(row=1, column=0, sticky="ew")

        # Нижний Canvas — финал
        self.canvas_final = tk.Canvas(canv_frame, bg="#f9f9f9", highlightthickness=0)
        self.canvas_final.grid(row=2, column=0, sticky="nsew")
        self.canvas_final.config(xscrollincrement=1, yscrollincrement=1)
        self.canvas_final.create_text(20, 20, text=str(tr("final", self.language)), anchor="nw", font=("SF Pro Text", 13, "bold"), fill="#222", tags="label")
        self.canvas_final.bind("<Button-1>", self.on_canvas_click)
        self.canvas_final.bind("<Enter>", lambda e: self.canvas_final.focus_set())
        self.scrollbar_fin_y = tk.Scrollbar(
            canv_frame, orient="vertical", command=self.canvas_final.yview, width=2,
            troughcolor="#f9f9f9", bg="#f9f9f9", highlightthickness=0
        )
        self.scrollbar_fin_x = tk.Scrollbar(
            canv_frame, orient="horizontal", command=self.canvas_final.xview, width=2,
            troughcolor="#f9f9f9", bg="#f9f9f9", highlightthickness=0
        )
        self.canvas_final.config(yscrollcommand=self.scrollbar_fin_y.set, xscrollcommand=self.scrollbar_fin_x.set)
        self.scrollbar_fin_y.grid(row=2, column=1, sticky="ns")
        self.scrollbar_fin_x.grid(row=3, column=0, sticky="ew")
        self.canvas_final.config(yscrollcommand=self.sync_yview_final, xscrollcommand=self.sync_xview_final)

        # Навигация мышкой
        self.canvas_original.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas_final.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas_original.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
        self.canvas_final.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
        self.canvas_original.bind("<Command-MouseWheel>", self.on_command_mousewheel)
        self.canvas_final.bind("<Command-MouseWheel>", self.on_command_mousewheel)

    def show_about(self):
        messagebox.showinfo(tr("about", self.language), tr("about_msg", self.language))

    def choose_files(self):
        self.status.config(text=tr("select_orig", self.language))
        file1 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file1: return
        self.pdf_paths[0] = file1  # type: ignore  # noqa

        self.status.config(text=tr("select_final", self.language))
        file2 = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file2: return
        self.pdf_paths[1] = file2  # type: ignore  # noqa

        self.status.config(text=tr("files_chosen", self.language))
        self.scale_percent = 0
        self.render_pdf_images()

    def get_fit_scale(self):
        # Вычисляет минимальный fit-to-window масштаб для обоих PDF, чтобы размеры совпадали
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

    def scale_plus(self):
        if self.scale_percent < self.max_scale_percent:
            self.scale_percent += 20
            self.render_pdf_images()

    def scale_minus(self):
        if self.scale_percent > self.min_scale_percent:
            self.scale_percent -= 20
            self.render_pdf_images()

    def scale_reset(self):
        self.scale_percent = 0
        self.render_pdf_images()
        # Сброс прокрутки после ресета масштаба
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)

    def render_pdf_images(self):
        if not self.pdf_paths[0] or not self.pdf_paths[1]:
            return
        if self._rendering:
            return
        self._rendering = True
        # fit_scale теперь общий для обоих PDF
        fit_scale = self.get_fit_scale()
        user_scale = 1 + self.scale_percent / 100
        scale = fit_scale * user_scale

        doc1 = fitz.open(self.pdf_paths[0])
        page1 = doc1[0]
        pix1 = page1.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)  # type: ignore  # noqa
        img1 = Image.open(io.BytesIO(pix1.tobytes("ppm"))).convert("RGB")
        self.cv_img_original = np.array(img1)[:, :, ::-1]
        self.tk_img_original = ImageTk.PhotoImage(img1)
        doc1.close()

        doc2 = fitz.open(self.pdf_paths[1])
        page2 = doc2[0]
        pix2 = page2.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)  # type: ignore  # noqa
        img2 = Image.open(io.BytesIO(pix2.tobytes("ppm"))).convert("RGB")
        self.cv_img_final = np.array(img2)[:, :, ::-1]
        self.tk_img_final = ImageTk.PhotoImage(img2)
        doc2.close()

        self.display_image(self.canvas_original, self.tk_img_original)
        self.display_image(self.canvas_final, self.tk_img_final)

        self.scale_label.config(text=f"{int(user_scale * 100)}%")
        self._rendering = False
        self.draw_diff_boxes()

    def display_image(self, canvas, tk_img):
        canvas.delete("pdfimg")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        img_w = tk_img.width()
        img_h = tk_img.height()
        idx = 0 if canvas == self.canvas_original else 1
        
        # Простое центрирование изображения
        if img_w < w:
            x0 = (w - img_w) // 2
        else:
            x0 = 0
        if img_h < h:
            y0 = (h - img_h) // 2
        else:
            y0 = 0
            
        print(f"DISPLAY {idx}: img={img_w}x{img_h}, canvas={w}x{h}, pos=({x0},{y0})")
        
        canvas.create_image(x0, y0, anchor="nw", image=tk_img, tags="pdfimg")
        canvas.image = tk_img
        canvas.image_offset = (x0, y0)
        
        # Правильная настройка scrollregion для прокрутки
        # scrollregion должен включать всю область изображения
        scroll_w = max(img_w, w)
        scroll_h = max(img_h, h)
        canvas.config(scrollregion=(0, 0, scroll_w, scroll_h))

    def toggle_compare(self):
        if self.show_diffs:
            self.show_diffs = False
            self.active_box_idx = None
        else:
            self.compare()
            self.show_diffs = True
            self.render_pdf_images()
        self.draw_diff_boxes()

    def compare(self):
        if self.cv_img_original is None or self.cv_img_final is None:
            self.status.config(text=tr("must_choose", self.language))
            return
        gray1 = cv2.cvtColor(self.cv_img_original, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.cv_img_final, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(cnt) for cnt in contours]
        boxes = self.merge_boxes(boxes, min_distance=18)
        self.diff_boxes = [(x, y, w, h) for (x, y, w, h) in boxes]
        self.active_box_idx = None
        self.update_status()
        self.draw_diff_boxes()

    def merge_boxes(self, boxes, min_distance=18):
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
        for idx, canvas in enumerate([self.canvas_original, self.canvas_final]):
            ids = canvas.find_all()
            for id_ in ids:
                if "pdfimg" not in canvas.gettags(id_):
                    canvas.delete(id_)
            if self.show_diffs and self.diff_boxes:
                for box_idx, (x, y, w, h) in enumerate(self.diff_boxes):
                    rx = int(x * self.fit_scale + getattr(canvas, "image_offset", (0, 0))[0])
                    ry = int(y * self.fit_scale + getattr(canvas, "image_offset", (0, 0))[1])
                    rw = int(w * self.fit_scale)
                    rh = int(h * self.fit_scale)
                    if rw > 0 and rh > 0:
                        color = "yellow" if self.active_box_idx == box_idx else "red"
                        canvas.create_rectangle(
                            rx, ry, rx + rw, ry + rh,
                            outline=color, width=2, tags=f"diffbox_{box_idx}"
                        )

    def update_status(self):
        if self.diff_boxes and self.active_box_idx is not None:
            text = f"{tr('diffs', self.language)}: {len(self.diff_boxes)}  [{self.active_box_idx+1}/{len(self.diff_boxes)}]"
        else:
            text = f"{tr('diffs', self.language)}: {len(self.diff_boxes)}"
        self.status.config(text=text)

    def change_language(self, event):
        self.language = self.lang_var.get()
        self.btn_about.config(text=tr("about", self.language))
        self.btn_choose.config(text=tr("choose", self.language))
        self.btn_compare.config(text=tr("compare", self.language))
        self.status.config(text=f"{tr('diffs', self.language)}: {len(self.diff_boxes)}")
        self.btn_minus.config(text=tr("minus", self.language))
        self.btn_plus.config(text=tr("plus", self.language))
        self.btn_zero.config(text=tr("zero", self.language))
        self.lang_menu.set(self.language)
        self.draw_diff_boxes()

    def enable_hand_mode(self, event=None):
        if not self._hand_mode:
            self.toggle_hand_mode()

    def disable_hand_mode(self, event=None):
        if self._hand_mode:
            self.toggle_hand_mode()

    def toggle_hand_mode(self, event=None):
        self._hand_mode = not self._hand_mode
        cursor = "hand2" if self._hand_mode else "arrow"
        for canvas in [self.canvas_original, self.canvas_final]:
            canvas.config(cursor=cursor)
            # Удаляем все привязки мыши
            canvas.unbind("<Button-1>")
            canvas.unbind("<ButtonPress-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<ButtonRelease-1>")
            if self._hand_mode:
                # В режиме руки - привязываем события перетаскивания
                canvas.bind("<ButtonPress-1>", self.start_pan)
                canvas.bind("<B1-Motion>", self.pan)
                canvas.bind("<ButtonRelease-1>", self.end_pan)
            else:
                # В обычном режиме - привязываем клик для выбора различий
                canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Сбрасываем drag только если переходим из режима руки в обычный режим И drag не активен
        if not self._hand_mode and self._pan_data["drag"]:
            print(f"TOGGLE_HAND_MODE: drag is active ({self._pan_data['drag']}), keeping it True")
            # Не сбрасываем drag, если он активен - это может быть ложное переключение режима

    def start_pan(self, event):
        print("START_PAN CALLED", event.x, event.y)
        print(f"START_PAN: _hand_mode = {self._hand_mode}")
        print(f"START_PAN: widget = {event.widget}")
        if not self._hand_mode:
            print("START_PAN: not hand_mode, returning")
            return
        event.widget.focus_set()
        self._pan_data["drag"] = True
        self._pan_data["x"] = event.x
        self._pan_data["y"] = event.y
        print(f"START_PAN: drag set to True, pan_data = {self._pan_data}")

    def pan(self, event):
        print("PAN CALLED", event.x, event.y)
        if not self._hand_mode or not self._pan_data["drag"]:
            print("PAN: not hand_mode or not drag")
            return
        dx = event.x - self._pan_data["x"]
        dy = event.y - self._pan_data["y"]
        print(f"PAN: dx={dx}, dy={dy}")
        for canvas in [self.canvas_original, self.canvas_final]:
            img = self.tk_img_original if canvas == self.canvas_original else self.tk_img_final
            if img is None:
                continue
            img_w, img_h = img.width(), img.height()
            can_w, can_h = canvas.winfo_width(), canvas.winfo_height()
            # Прокручиваем только если изображение больше canvas
            if img_w > can_w:
                scroll_x = int(-dx / 2)  # ускорено
                if scroll_x != 0:
                    canvas.xview_scroll(scroll_x, "units")
            if img_h > can_h:
                scroll_y = int(-dy / 2)  # ускорено
                if scroll_y != 0:
                    canvas.yview_scroll(scroll_y, "units")
        self._pan_data["x"] = event.x
        self._pan_data["y"] = event.y
        self.draw_diff_boxes()

    def end_pan(self, event):
        print("END_PAN CALLED", event.x, event.y)
        print(f"END_PAN: widget = {event.widget}")
        print(f"END_PAN: drag was {self._pan_data['drag']}")
        if self._pan_data["drag"]:
            self._pan_data["drag"] = False
            print(f"END_PAN: drag set to {self._pan_data['drag']}")
        else:
            print("END_PAN: drag was already False, ignoring")

    def on_mousewheel(self, event):
        # event.delta на Mac обычно +-120, на Windows +-120 или +-1
        # Просто колесо — вертикально синхронно
        lines = -1 if event.delta > 0 else 1
        # Прокручиваем оба Canvas синхронно
        self.canvas_original.yview_scroll(lines, "units")
        self.canvas_final.yview_scroll(lines, "units")

    def on_shift_mousewheel(self, event):
        # Shift+Wheel — обычно горизонтальная прокрутка
        lines = -1 if event.delta > 0 else 1
        self.canvas_original.xview_scroll(lines, "units")
        self.canvas_final.xview_scroll(lines, "units")

    def on_command_mousewheel(self, event):
        # Command+Wheel — как горизонтальная прокрутка
        lines = -1 if event.delta > 0 else 1
        self.canvas_original.xview_scroll(lines, "units")
        self.canvas_final.xview_scroll(lines, "units")

    def on_canvas_click(self, event):
        if not self.show_diffs or not self.diff_boxes:
            return
        canvas = event.widget
        idx = 0 if canvas == self.canvas_original else 1
        offset_x, offset_y = getattr(canvas, "image_offset", (0, 0))
        x = canvas.canvasx(event.x) - offset_x
        y = canvas.canvasy(event.y) - offset_y
        found = False
        for box_idx, (bx, by, bw, bh) in enumerate(self.diff_boxes):
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if self.active_box_idx == box_idx:
                    self.active_box_idx = None  # снять выделение
                else:
                    self.active_box_idx = box_idx
                found = True
                break
        if found:
            self.draw_diff_boxes()

    def on_resize(self, event):
        # fit-to-window при изменении размера окна, но множитель пользователя сохраняется
        if self.tk_img_original or self.tk_img_final:
            # Принудительно обновляем размеры Canvas
            total_h = self.canv_frame.winfo_height()
            divider_h = self.divider.winfo_height() if self.divider else 2
            half_h = max(1, (total_h - divider_h) // 2)
            self.canvas_original.config(height=half_h)
            self.canvas_final.config(height=half_h)
            self.render_pdf_images()

    # --- Синхронизация прокрутки ---
    def sync_yview(self, *args):
        self.canvas_original.yview_moveto(float(args[0]))
        self.canvas_final.yview_moveto(float(args[0]))

    def sync_xview(self, *args):
        self.canvas_original.xview_moveto(float(args[0]))
        self.canvas_final.xview_moveto(float(args[0]))

    def sync_yview_final(self, *args):
        self.canvas_final.yview_moveto(float(args[0]))
        self.canvas_original.yview_moveto(float(args[0]))

    def sync_xview_final(self, *args):
        self.canvas_final.xview_moveto(float(args[0]))
        self.canvas_original.xview_moveto(float(args[0]))

    def next_diff(self):
        if not self.diff_boxes:
            return
        if self.active_box_idx is None:
            self.active_box_idx = 0
        else:
            self.active_box_idx = (self.active_box_idx + 1) % len(self.diff_boxes)
        self.scroll_to_box(self.active_box_idx)
        self.draw_diff_boxes()
        self.update_status()

    def prev_diff(self):
        if not self.diff_boxes:
            return
        if self.active_box_idx is None:
            self.active_box_idx = len(self.diff_boxes) - 1
        else:
            self.active_box_idx = (self.active_box_idx - 1) % len(self.diff_boxes)
        self.scroll_to_box(self.active_box_idx)
        self.draw_diff_boxes()
        self.update_status()

    def scroll_to_box(self, idx):
        # Прокрутить оба Canvas так, чтобы рамка была по центру
        if not self.diff_boxes or idx is None:
            return
        x, y, w, h = self.diff_boxes[idx]
        for canvas in [self.canvas_original, self.canvas_final]:
            can_w = canvas.winfo_width()
            can_h = canvas.winfo_height()
            offset_x = getattr(canvas, "image_offset", (0, 0))[0]
            offset_y = getattr(canvas, "image_offset", (0, 0))[1]
            rx = int(x * self.fit_scale + offset_x)
            ry = int(y * self.fit_scale + offset_y)
            rw = int(w * self.fit_scale)
            rh = int(h * self.fit_scale)
            # Центр рамки
            cx = rx + rw // 2
            cy = ry + rh // 2
            # Перевести в fraction для xview/yview
            if can_w > 0 and can_h > 0:
                frac_x = max(0, (cx - can_w // 2) / max(1, canvas.bbox("pdfimg")[2] - can_w))
                frac_y = max(0, (cy - can_h // 2) / max(1, canvas.bbox("pdfimg")[3] - can_h))
                canvas.xview_moveto(frac_x)
                canvas.yview_moveto(frac_y)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFBitmapCompareApp(root)
    root.mainloop()