"""
viewer.py — Barcode Annotation Viewer
======================================
Pure-Python viewer using tkinter (built-in) and Pillow for image decoding.

Dependencies
------------
    pip install Pillow
    pip install tkinterdnd2   # optional – enables OS drag-and-drop

Usage
-----
    python viewer.py [annotations.json]

Keyboard shortcuts
------------------
    Left / Right   navigate images
    O              open JSON file
    Scroll wheel   zoom in / out
    Click + drag   pan image
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk, ImageOps
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_OK = True
except ImportError:
    TkinterDnD = None
    DND_FILES = None
    _DND_OK = False

# ---------------------------------------------------------------------------
# Overlay colors (cycle through for multiple barcodes)
# ---------------------------------------------------------------------------
_COLORS = ["#00c850", "#1e90ff", "#ffa000", "#dc32c8", "#00d2d2"]


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
_TkBase = TkinterDnD.Tk if _DND_OK else tk.Tk


class ViewerApp(_TkBase):
    def __init__(self, json_path=None):
        super().__init__()
        self.title("Barcode Annotation Viewer")
        self.geometry("1440x860")

        # ---- State --------------------------------------------------------
        self._json_path = None
        self._json_records = {}    # basename -> list of barcode dicts
        self._image_paths = []     # loaded image abs paths (ordered)
        self._current_idx = None

        # Canvas zoom / pan
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._drag_start = None
        self._original_image = None   # PIL Image for the displayed frame
        self._photo_ref = None        # ImageTk.PhotoImage (keep reference)
        self._resize_job = None       # debounce id for resize events

        self._build_ui()
        self._bind_keys()

        if not _PIL_OK:
            messagebox.showerror(
                "Missing Dependency",
                "Pillow is required for image display.\n\nInstall with:\n    pip install Pillow"
            )

        if json_path and os.path.isfile(json_path):
            self._load_json(json_path)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ---- Toolbar ---------------------------------------------------
        tb = tk.Frame(self, bd=1, relief=tk.FLAT)
        tb.pack(fill=tk.X, padx=4, pady=(4, 0))

        tk.Button(tb, text="Load Images…", command=self._on_load_files).pack(side=tk.LEFT, padx=2)
        tk.Button(tb, text="Load Folder…", command=self._on_load_folder).pack(side=tk.LEFT, padx=2)
        tk.Button(tb, text="Open JSON…",   command=self._on_open_json).pack(side=tk.LEFT, padx=2)

        self._info_var = tk.StringVar(value="No file loaded.")
        tk.Label(tb, textvariable=self._info_var, fg="gray",
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=12)

        # ---- Horizontal paned window -----------------------------------
        self._paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        self._paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # -- Left: image list --------------------------------------------
        left = tk.Frame(self._paned, width=220)
        left.pack_propagate(False)

        tk.Label(left, text="Images", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, padx=6, pady=(4, 0))

        list_frame = tk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(
            list_frame, selectmode=tk.SINGLE, font=("Arial", 9),
            activestyle="none", yscrollcommand=sb.set
        )
        sb.config(command=self._listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_list_select)

        self._hint_lbl = tk.Label(
            left, text="Load images or a folder, then open a JSON to show annotations.",
            fg="gray", font=("Arial", 8), wraplength=210, justify=tk.LEFT
        )
        self._hint_lbl.pack(anchor=tk.W, padx=4, pady=(0, 4))

        self._paned.add(left, minsize=160)

        # -- Center: canvas + navigation ---------------------------------
        center = tk.Frame(self._paned)

        self._canvas = tk.Canvas(center, bg="#2b2b2b", cursor="fleur")
        self._canvas.pack(fill=tk.BOTH, expand=True)

        self._canvas.bind("<MouseWheel>",    self._on_wheel)   # Windows
        self._canvas.bind("<Button-4>",      self._on_wheel)   # Linux up
        self._canvas.bind("<Button-5>",      self._on_wheel)   # Linux down
        self._canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self._canvas.bind("<B1-Motion>",     self._on_pan_move)
        self._canvas.bind("<Configure>",     self._on_canvas_resize)

        nav = tk.Frame(center)
        nav.pack(fill=tk.X, padx=4, pady=2)
        tk.Button(nav, text="< Prev", width=7, command=self._prev_image).pack(side=tk.LEFT, padx=2)
        tk.Button(nav, text="Next >", width=7, command=self._next_image).pack(side=tk.RIGHT, padx=2)
        self._nav_var = tk.StringVar(value="0 / 0")
        tk.Label(nav, textvariable=self._nav_var, font=("Arial", 10)).pack(side=tk.LEFT, expand=True)

        self._paned.add(center, minsize=500)

        # -- Right: barcode details tree ---------------------------------
        right = tk.Frame(self._paned, width=260)
        right.pack_propagate(False)

        tk.Label(right, text="Barcodes", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, padx=6, pady=(4, 0))

        tree_frame = tk.Frame(right)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(tree_frame, columns=("value",), show="tree headings")
        self._tree.heading("#0",      text="Property")
        self._tree.heading("value",   text="Value")
        self._tree.column("#0",       width=130, stretch=True)
        self._tree.column("value",    width=200, stretch=True)

        tsb_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL,   command=self._tree.yview)
        tsb_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=tsb_y.set, xscrollcommand=tsb_x.set)
        tsb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        tsb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._paned.add(right, minsize=200)

        # ---- Drag-and-drop ---------------------------------------------
        if _DND_OK:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)

        self.after(150, self._set_initial_sash)

        # ---- Status bar ------------------------------------------------
        self._statusbar = tk.Label(
            self, text="Open a JSON annotation file to begin.",
            bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9), fg="#333"
        )
        self._statusbar.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=1)

    def _bind_keys(self):
        self.bind("<Left>",  lambda e: self._prev_image())
        self.bind("<Right>", lambda e: self._next_image())
        self.bind("o",       lambda e: self._on_open_json())
        self.bind("O",       lambda e: self._on_open_json())

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------
    def _on_load_files(self):
        paths = filedialog.askopenfilenames(
            title="Load Images",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp"),
                ("All files", "*.*"),
            ]
        )
        if paths:
            self._add_images(list(paths))

    def _on_load_folder(self):
        folder = filedialog.askdirectory(title="Load Image Folder")
        if not folder:
            return
        paths = []
        for root_dir, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")):
                    paths.append(os.path.join(root_dir, f))
        if paths:
            self._add_images(paths)
        else:
            messagebox.showinfo("No Images", "No image files found in that folder.")

    def _add_images(self, paths):
        existing = set(self._image_paths)
        new = [p for p in paths if p not in existing]
        if not new:
            return
        self._image_paths.extend(new)
        self._rebuild_list()
        self._hint_lbl.config(text=f"{len(self._image_paths)} image(s) loaded.")
        self._set_status(f"{len(self._image_paths)} image(s) loaded.")

    def _on_open_json(self):
        path = filedialog.askopenfilename(
            title="Open Annotation JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self._load_json(path)

    # ------------------------------------------------------------------
    # JSON loading
    # ------------------------------------------------------------------
    def _load_json(self, json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        fmt = data.get("format", "")
        if "barcode-benchmark" not in fmt:
            if not messagebox.askyesno(
                "Unsupported Format",
                f"Expected 'barcode-benchmark/1.0', got '{fmt}'.\nTry to load anyway?"
            ):
                return

        self._json_path = json_path
        self._json_records = {}
        for entry in data.get("images", []):
            file_field = entry.get("file", "")
            basename = os.path.basename(file_field) if file_field else ""
            if basename:
                self._json_records[basename] = entry.get("barcodes", [])

        total_bc = sum(len(v) for v in self._json_records.values())
        self._info_var.set(
            f"{os.path.basename(json_path)}  —  "
            f"{len(self._json_records)} entry(ies),  {total_bc} barcode(s)"
        )
        self.title(f"Barcode Annotation Viewer — {os.path.basename(json_path)}")
        self._rebuild_list()
        self._set_status(
            f"JSON loaded: {os.path.basename(json_path)}  "
            f"({len(self._json_records)} image entries)"
        )

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------
    def _rebuild_list(self):
        # Remember which path is currently shown so we can restore it
        current_path = (
            self._image_paths[self._current_idx]
            if self._current_idx is not None and self._current_idx < len(self._image_paths)
            else None
        )

        self._listbox.delete(0, tk.END)
        for path in self._image_paths:
            basename = os.path.basename(path)
            barcodes = self._json_records.get(basename)
            if barcodes is not None:
                label = f"{basename}  [{len(barcodes)}]"
            else:
                label = basename
            self._listbox.insert(tk.END, label)

        # Apply colors: green = has entries, grey = 0 entries, black = no match
        for i, path in enumerate(self._image_paths):
            barcodes = self._json_records.get(os.path.basename(path))
            if barcodes is None:
                color = "#111111"
            elif len(barcodes) > 0:
                color = "#006400"
            else:
                color = "#787878"
            self._listbox.itemconfig(i, fg=color)

        # Restore or initialise selection
        if current_path and current_path in self._image_paths:
            new_idx = self._image_paths.index(current_path)
            self._listbox.selection_set(new_idx)
            self._listbox.see(new_idx)
            # Refresh display: JSON may have just been loaded
            self._show_image(new_idx)
        elif self._image_paths and self._current_idx is None:
            self._listbox.selection_set(0)
            self._listbox.event_generate("<<ListboxSelect>>")

    def _on_list_select(self, event):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._image_paths):
            return
        self._current_idx = idx
        self._nav_var.set(f"{idx + 1} / {len(self._image_paths)}")
        self._show_image(idx)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _prev_image(self):
        if self._current_idx is None or not self._image_paths:
            return
        new = self._current_idx - 1
        if new >= 0:
            self._listbox.selection_clear(0, tk.END)
            self._listbox.selection_set(new)
            self._listbox.see(new)
            self._listbox.event_generate("<<ListboxSelect>>")

    def _next_image(self):
        if self._current_idx is None or not self._image_paths:
            return
        new = self._current_idx + 1
        if new < len(self._image_paths):
            self._listbox.selection_clear(0, tk.END)
            self._listbox.selection_set(new)
            self._listbox.see(new)
            self._listbox.event_generate("<<ListboxSelect>>")

    # ------------------------------------------------------------------
    # Image display
    # ------------------------------------------------------------------
    def _show_image(self, idx):
        if not _PIL_OK:
            return
        abs_path = self._image_paths[idx]
        basename = os.path.basename(abs_path)

        self._canvas.delete("all")
        self._tree.delete(*self._tree.get_children())

        try:
            pil_img = Image.open(abs_path)
            pil_img = ImageOps.exif_transpose(pil_img)   # EXIF orientation
            pil_img = pil_img.convert("RGB")
        except Exception as exc:
            self._canvas.create_text(
                20, 20, anchor=tk.NW, text=f"Cannot read:\n{exc}", fill="red",
                font=("Arial", 11)
            )
            self._set_status(f"Cannot read: {basename}")
            return

        self._original_image = pil_img
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._fit_image()   # resets zoom/pan to fit, then renders + draws overlays

        barcodes = self._json_records.get(basename, [])
        self._populate_tree(barcodes)

        if barcodes:
            self._set_status(f"{basename}  —  {len(barcodes)} barcode(s) from JSON")
        else:
            suffix = " (not in JSON)" if self._json_path else " (no JSON loaded)"
            self._set_status(f"{basename}  —  no annotation{suffix}")

    def _fit_image(self):
        """Scale image to fill ~95 % of the canvas, centered."""
        if self._original_image is None:
            return
        cw = self._canvas.winfo_width()  or 800
        ch = self._canvas.winfo_height() or 600
        iw, ih = self._original_image.size
        scale = min(cw / iw, ch / ih) * 0.95
        self._zoom = scale
        self._pan_x = (cw - iw * scale) / 2
        self._pan_y = (ch - ih * scale) / 2
        self._render()

    def _render(self):
        """Redraw the image (resized) and all overlay polygons."""
        if self._original_image is None:
            return
        self._canvas.delete("all")

        iw, ih = self._original_image.size
        new_w = max(1, int(iw * self._zoom))
        new_h = max(1, int(ih * self._zoom))

        resized = self._original_image.resize((new_w, new_h), Image.LANCZOS)
        self._photo_ref = ImageTk.PhotoImage(resized)
        self._canvas.create_image(int(self._pan_x), int(self._pan_y),
                                   anchor=tk.NW, image=self._photo_ref)

        # Draw barcode overlays for the current image
        if self._current_idx is not None:
            basename = os.path.basename(self._image_paths[self._current_idx])
            barcodes = self._json_records.get(basename, [])
            self._draw_overlays(barcodes)

    def _draw_overlays(self, barcodes):
        for i, bc in enumerate(barcodes):
            pts_raw = bc.get("points", [])
            if len(pts_raw) < 2:
                continue
            color = _COLORS[i % len(_COLORS)]

            # Convert image coords → canvas coords
            def to_canvas(p):
                return (p[0] * self._zoom + self._pan_x,
                        p[1] * self._zoom + self._pan_y)

            canvas_pts = []
            for p in pts_raw:
                cx, cy = to_canvas(p)
                canvas_pts.extend([cx, cy])

            # Polygon outline
            if len(canvas_pts) >= 4:
                self._canvas.create_polygon(
                    canvas_pts, outline=color, fill="", width=2, tags="ov"
                )

            # Corner dots + label
            for p in pts_raw:
                cx, cy = to_canvas(p)
                self._canvas.create_oval(
                    cx-4, cy-4, cx+4, cy+4,
                    outline=color, fill=color, tags="ov"
                )

            tx, ty = to_canvas(pts_raw[0])
            label = f'[{bc.get("format","?")}] {bc.get("text","")}'
            self._canvas.create_text(
                tx, max(0.0, ty - 16), anchor=tk.NW, text=label,
                fill=color, font=("Arial", 9, "bold"), tags="ov"
            )

    def _populate_tree(self, barcodes):
        self._tree.delete(*self._tree.get_children())
        for i, bc in enumerate(barcodes):
            root_id = self._tree.insert(
                "", tk.END, text=f"#{i + 1}", values=(bc.get("text", ""),), open=True
            )
            self._tree.insert(root_id, tk.END, text="Text",   values=(bc.get("text",   ""),))
            self._tree.insert(root_id, tk.END, text="Format", values=(bc.get("format", ""),))
            pts_raw = bc.get("points", [])
            pts_id = self._tree.insert(
                root_id, tk.END, text="Points",
                values=(f"{len(pts_raw)} corners",), open=True
            )
            for j, pt in enumerate(pts_raw):
                self._tree.insert(pts_id, tk.END,
                                  text=f"  P{j + 1}",
                                  values=(f"({float(pt[0]):.1f}, {float(pt[1]):.1f})",))

    # ------------------------------------------------------------------
    # Canvas interactions: zoom + pan
    # ------------------------------------------------------------------
    def _on_wheel(self, event):
        if self._original_image is None:
            return
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            factor = 1.15
        else:
            factor = 1.0 / 1.15
        mx, my = event.x, event.y
        self._pan_x = mx - (mx - self._pan_x) * factor
        self._pan_y = my - (my - self._pan_y) * factor
        self._zoom *= factor
        self._render()

    def _on_pan_start(self, event):
        self._drag_start = (event.x, event.y)

    def _on_pan_move(self, event):
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._pan_x += dx
        self._pan_y += dy
        self._drag_start = (event.x, event.y)
        self._render()

    def _on_canvas_resize(self, event):
        """Debounced: re-fit the image whenever the canvas is resized."""
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._fit_image)

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------
    def _on_drop(self, event):
        """Handle files/folders dropped onto the window (tkinterdnd2)."""
        raw = event.data.strip()
        # Paths with spaces are wrapped in {} by tkinterdnd2
        paths = []
        remaining = raw
        while remaining:
            if remaining.startswith('{'):
                end = remaining.find('}')
                if end == -1:
                    paths.append(remaining[1:])
                    break
                paths.append(remaining[1:end])
                remaining = remaining[end + 1:].strip()
            else:
                space = remaining.find(' ')
                if space == -1:
                    paths.append(remaining)
                    break
                paths.append(remaining[:space])
                remaining = remaining[space:].strip()

        json_files = []
        image_files = []
        for p in paths:
            if os.path.isdir(p):
                for root_dir, _, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")
                        ):
                            image_files.append(os.path.join(root_dir, f))
            elif p.lower().endswith(".json"):
                json_files.append(p)
            elif p.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp")
            ):
                image_files.append(p)
        if json_files:
            self._load_json(json_files[0])
        if image_files:
            self._add_images(image_files)

    def _set_initial_sash(self):
        """Position sashes so the image canvas takes most of the window width."""
        try:
            total = self.winfo_width()
            self._paned.sash_place(0, 220, 1)
            self._paned.sash_place(1, total - 260, 1)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def _set_status(self, msg):
        self._statusbar.config(text=msg)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    json_arg = sys.argv[1] if len(sys.argv) > 1 else None
    app = ViewerApp(json_path=json_arg)
    app.mainloop()
