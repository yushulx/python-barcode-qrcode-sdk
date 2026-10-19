import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Optional, Tuple, Dict, List
import cv2
import numpy as np
from PIL import Image, ImageTk
from dynamsoft_capture_vision_bundle import *
import threading
from pathlib import Path
import datetime

# Try to import PDF support (not needed - Dynamsoft handles PDFs directly)
PDF_SUPPORT = True  # Always available with Dynamsoft SDK

# Constants
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
CONTOUR_COLOR = (0, 255, 0)  # Green
TEXT_COLOR = (0, 0, 255)     # Red
CONTOUR_THICKNESS = 2
TEXT_THICKNESS = 2
FONT_SCALE = 0.5
TEXT_OFFSET_Y = 10

class MyIntermediateResultReceiver(IntermediateResultReceiver):
    def __init__(self, im: IntermediateResultManager):
        self.images = {}
        self.im = im
        super().__init__()

    def on_localized_barcodes_received(self, result: "LocalizedBarcodesUnit", info: IntermediateResultExtraInfo) -> None:
        try:
            hash_id = result.get_original_image_hash_id()
            if hash_id and self.im:
                image = self.im.get_original_image(hash_id)
                
                if image is not None and self.images.get(hash_id) is None:
                    try:
                        image_io = ImageIO()
                        saved = image_io.save_to_numpy(image)
                        if saved is not None:
                            # Handle tuple return (error_code, error_message, numpy_array)
                            if isinstance(saved, tuple) and len(saved) == 3:
                                error_code, error_message, numpy_array = saved
                                if error_code == 0 and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                            elif isinstance(saved, tuple) and len(saved) == 2:
                                # Handle (success, array) format
                                success, numpy_array = saved
                                if success and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                            else:
                                # Direct numpy array return
                                self.images[hash_id] = saved
                    except Exception:
                        # Silently ignore intermediate result processing errors
                        # These are not critical for the main functionality
                        pass
        except Exception:
            # Silently handle any unexpected errors in the receiver
            # These are not critical for the main barcode detection functionality
            pass

class BarcodeReaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamsoft Barcode Reader - GUI")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.cvr_instance = None
        self.custom_receiver = None
        self.current_file_path = None
        self.current_pages = {}  # Store page data {page_index: cv_image}
        self.page_hash_mapping = {}  # Map page_index to hash_id
        self.current_page_index = 0
        self.page_results = {}  # Store barcode results for each page
        self.is_processing = False
        
        # Create GUI first so log_message can work
        self.create_widgets()
        
        # Initialize Dynamsoft after GUI is ready
        self.initialize_license()
        
        # Setup drag and drop
        self.setup_drag_drop()
        
    def initialize_license(self):
        """Initialize the Dynamsoft license."""
        try:
            error_code, error_message = LicenseManager.init_license(LICENSE_KEY)
            
            if error_code == EnumErrorCode.EC_OK or error_code == EnumErrorCode.EC_LICENSE_CACHE_USED:
                self.cvr_instance = CaptureVisionRouter()
                intermediate_result_manager = self.cvr_instance.get_intermediate_result_manager()
                self.custom_receiver = MyIntermediateResultReceiver(intermediate_result_manager)
                intermediate_result_manager.add_result_receiver(self.custom_receiver)
                self.log_message("✅ License initialized successfully!", "INFO")
            else:
                self.log_message(f"❌ License initialization failed: {error_code}, {error_message}", "ERROR")
                messagebox.showerror("License Error", f"Failed to initialize license: {error_message}")
        except Exception as e:
            self.log_message(f"❌ Error initializing license: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to initialize: {e}")
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)  # Image panel gets more space
        main_frame.rowconfigure(1, weight=1)
        
        # Control panel (left side)
        self.create_control_panel(main_frame)
        
        # Image display area (center)
        self.create_image_panel(main_frame)
        
        # Results panel (right side)
        self.create_results_panel(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_control_panel(self, parent):
        """Create the control panel with buttons and navigation."""
        control_frame = ttk.LabelFrame(parent, text="📁 File Controls", padding="10")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        control_frame.configure(width=250)
        
        # Load file button
        load_btn = ttk.Button(control_frame, text="📂 Load File", command=self.load_file, width=25)
        load_btn.pack(pady=5)
        
        # File info frame
        info_frame = ttk.LabelFrame(control_frame, text="File Information", padding="5")
        info_frame.pack(fill=tk.X, pady=10)
        
        self.file_info_label = ttk.Label(info_frame, text="No file loaded", wraplength=200, font=('Arial', 9))
        self.file_info_label.pack(pady=5)
        
        self.file_size_label = ttk.Label(info_frame, text="", font=('Arial', 8), foreground='gray')
        self.file_size_label.pack()
        
        # Page navigation
        self.nav_frame = ttk.LabelFrame(control_frame, text="📄 Page Navigation", padding="5")
        
        nav_buttons_frame = ttk.Frame(self.nav_frame)
        nav_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.prev_button = ttk.Button(nav_buttons_frame, text="◀ Prev", command=self.prev_page, state=tk.DISABLED, width=8)
        self.prev_button.pack(side=tk.LEFT, padx=2)
        
        self.next_button = ttk.Button(nav_buttons_frame, text="Next ▶", command=self.next_page, state=tk.DISABLED, width=8)
        self.next_button.pack(side=tk.RIGHT, padx=2)
        
        self.page_label = ttk.Label(self.nav_frame, text="Page: 0/0", font=('Arial', 10, 'bold'))
        self.page_label.pack(pady=5)
        
        # Page jump frame
        jump_frame = ttk.Frame(self.nav_frame)
        jump_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(jump_frame, text="Go to page:", font=('Arial', 8)).pack(side=tk.LEFT)
        self.page_entry = ttk.Entry(jump_frame, width=5, font=('Arial', 8))
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind('<Return>', self.jump_to_page)
        
        ttk.Button(jump_frame, text="Go", command=self.jump_to_page, width=4).pack(side=tk.LEFT, padx=2)
        
        # Processing controls
        process_frame = ttk.LabelFrame(control_frame, text="🔍 Barcode Detection", padding="5")
        process_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(process_frame, text="🔍 Detect Barcodes", command=self.process_current_file, state=tk.DISABLED, width=25)
        self.process_button.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(process_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Processing options
        options_frame = ttk.LabelFrame(process_frame, text="Options", padding="2")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.auto_process_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-process on load", variable=self.auto_process_var).pack(anchor=tk.W)
        
        self.show_confidence_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Show confidence", variable=self.show_confidence_var).pack(anchor=tk.W)
        
        # Action buttons
        action_frame = ttk.LabelFrame(control_frame, text="⚡ Actions", padding="5")
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="💾 Export Results", command=self.export_results, state=tk.DISABLED, width=25).pack(pady=2)
        self.export_button = action_frame.winfo_children()[-1]
        
        ttk.Button(action_frame, text="📋 Copy to Clipboard", command=self.copy_to_clipboard, state=tk.DISABLED, width=25).pack(pady=2)
        self.copy_button = action_frame.winfo_children()[-1]
        
        ttk.Button(action_frame, text="🗑️ Clear All", command=self.clear_all, width=25).pack(pady=10)
        
        # PDF Support info
        if PDF_SUPPORT:
            pdf_info = ttk.Label(control_frame, text="✅ Native PDF support enabled\\nvia Dynamsoft SDK", 
                                 foreground='green', font=('Arial', 8), wraplength=200)
            pdf_info.pack(pady=5)
    
    def create_image_panel(self, parent):
        """Create the main image display panel."""
        image_frame = ttk.LabelFrame(parent, text="🖼️ Image Display", padding="10")
        image_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(1, weight=1)
        
        # Toolbar
        toolbar = ttk.Frame(image_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.zoom_var = tk.StringVar(value="Fit")
        zoom_combo = ttk.Combobox(toolbar, textvariable=self.zoom_var, values=["25%", "50%", "75%", "100%", "125%", "150%", "200%", "Fit"], 
                                 state="readonly", width=8)
        zoom_combo.pack(side=tk.LEFT, padx=5)
        zoom_combo.bind('<<ComboboxSelected>>', self.on_zoom_change)
        
        ttk.Button(toolbar, text="🔍+", command=self.zoom_in, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍-", command=self.zoom_out, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↻", command=self.reset_view, width=4).pack(side=tk.LEFT, padx=2)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(image_frame)
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.image_canvas = tk.Canvas(canvas_frame, bg='white', relief=tk.SUNKEN, borderwidth=2)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.image_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Mouse wheel binding for zoom
        self.image_canvas.bind("<Control-MouseWheel>", self.on_mouse_wheel_zoom)
        self.image_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Drop zone setup
        self.setup_drop_zone()
        
        # Current zoom and pan state
        self.current_zoom = 1.0
        self.image_id = None
        self.original_image = None
    
    def create_results_panel(self, parent):
        """Create the results panel."""
        results_frame = ttk.LabelFrame(parent, text="📊 Barcode Results", padding="10")
        results_frame.grid(row=0, column=2, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        results_frame.configure(width=350)
        
        # Results summary
        summary_frame = ttk.Frame(results_frame)
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.results_summary = ttk.Label(summary_frame, text="Total Barcodes: 0", font=('Arial', 11, 'bold'))
        self.results_summary.pack(side=tk.LEFT)
        
        self.page_summary = ttk.Label(summary_frame, text="", font=('Arial', 9), foreground='gray')
        self.page_summary.pack(side=tk.RIGHT)
        
        # Results text area with improved formatting
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = ScrolledText(text_frame, width=35, height=25, wrap=tk.WORD, font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for beautiful colored output
        self.results_text.tag_configure('header', font=('Arial', 12, 'bold'), foreground='#1E3A8A', background='#F0F8FF')
        self.results_text.tag_configure('barcode_num', font=('Arial', 10, 'bold'), foreground='#DC2626', background='#FEF2F2')
        self.results_text.tag_configure('format', font=('Arial', 9, 'bold'), foreground='#7C2D12', background='#FEF7ED')
        self.results_text.tag_configure('text_content', foreground='#15803D', font=('Consolas', 9, 'bold'), background='#F0FDF4')
        self.results_text.tag_configure('location', foreground='#1E40AF', font=('Consolas', 8), background='#EFF6FF')
        self.results_text.tag_configure('separator', foreground='#6B7280', font=('Arial', 8))
        self.results_text.tag_configure('success', foreground='#059669', font=('Arial', 9, 'bold'), background='#ECFDF5')
    
    def create_status_bar(self, parent):
        """Create the status bar.""" 
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Processing time label
        self.time_label = ttk.Label(status_frame, text="", font=('Arial', 8), foreground='gray')
        self.time_label.grid(row=0, column=1, padx=(0, 10))
        
        # Memory usage (if available)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label = ttk.Label(status_frame, text=f"Memory: {memory_mb:.1f} MB", font=('Arial', 8), foreground='gray')
            self.memory_label.grid(row=0, column=2)
        except ImportError:
            pass
    
    def setup_drop_zone(self):
        """Setup the drag and drop zone."""
        self.drop_text_id = self.image_canvas.create_text(
            200, 150, 
            text="🖼️ Drag and drop files here\n\n📁 Supported formats:\n• Images: JPG, PNG, BMP, TIFF\n• PDF files (native support)\n\n🖱️ Or click 'Load File' button", 
            font=('Arial', 12), 
            fill='#666666',
            anchor=tk.CENTER,
            justify=tk.CENTER
        )
        
    def setup_drag_drop(self):
        """Setup drag and drop functionality using tkinterdnd2."""
        try:
            import tkinterdnd2 as tkdnd
            # Check if the root window supports drag and drop
            if hasattr(self.root, 'drop_target_register'):
                # Enable drag and drop for the canvas
                self.root.drop_target_register(tkdnd.DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.on_drop)
                print("✅ Full drag-and-drop support enabled")
            else:
                print("⚠️  Root window doesn't support drag-and-drop")
                self.image_canvas.bind('<Button-1>', self.on_canvas_click)
        except ImportError:
            print("⚠️  tkinterdnd2 not available - using basic file loading only")
            # Basic event bindings
            self.image_canvas.bind('<Button-1>', self.on_canvas_click)
        except Exception as e:
            print(f"⚠️  Drag-and-drop setup failed: {e}")
            self.image_canvas.bind('<Button-1>', self.on_canvas_click)
    
    def on_drop(self, event):
        """Handle file drop events."""
        try:
            files = event.data.split()
            if files:
                # Remove curly braces and quotes if present
                file_path = files[0].strip('{}').strip('\\"').strip("'")
                self.load_file_path(file_path)
        except Exception as e:
            self.log_message(f"❌ Error handling dropped file: {e}", "ERROR")
    
    def log_message(self, message, level="INFO"):
        """Log a message with timestamp and level."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Check if GUI widgets are initialized
        if not hasattr(self, 'results_text') or not hasattr(self, 'status_bar'):
            print(f"[{timestamp}] {level}: {message}")
            return
        
        # Configure log tags if not already done
        if not hasattr(self, '_log_tags_configured'):
            self.results_text.tag_configure('log_time', foreground='#6B7280', font=('Arial', 8))
            self.results_text.tag_configure('log_info', foreground='#374151', font=('Arial', 9))
            self.results_text.tag_configure('log_error', foreground='#DC2626', font=('Arial', 9, 'bold'))
            self.results_text.tag_configure('log_warning', foreground='#D97706', font=('Arial', 9, 'bold'))
            self.results_text.tag_configure('log_success', foreground='#059669', font=('Arial', 9, 'bold'))
            self._log_tags_configured = True
        
        # Insert timestamp and message with proper formatting
        self.results_text.insert(tk.END, f"[{timestamp}] ", 'log_time')
        
        # Use appropriate tag based on level
        tag_name = f"log_{level.lower()}"
        self.results_text.insert(tk.END, f"{message}\n", tag_name)
        self.results_text.see(tk.END)
        
        # Update status bar
        self.status_bar.configure(text=message)
        self.root.update_idletasks()
    
    def load_file(self):
        """Open file dialog to load an image or PDF."""
        file_types = [
            ("All Supported", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.tif;*.webp" + (";*.pdf" if PDF_SUPPORT else "")),
            ("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.tif;*.webp"),
        ]
        
        if PDF_SUPPORT:
            file_types.append(("PDF files", "*.pdf"))
        
        file_types.append(("All files", "*.*"))
        
        file_path = filedialog.askopenfilename(
            title="Select Image or PDF file",
            filetypes=file_types
        )
        
        if file_path:
            self.load_file_path(file_path)
    
    def load_file_path(self, file_path):
        """Load a file from the given path."""
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File not found: {file_path}")
                return
            
            self.log_message(f"📂 Loading file: {os.path.basename(file_path)}")
            
            self.current_file_path = file_path
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            file_size = os.path.getsize(file_path)
            
            # Update file info
            self.file_info_label.configure(text=f"📄 {file_name}")
            size_text = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
            self.file_size_label.configure(text=f"Size: {size_text}")
            
            # Clear previous data
            self.current_pages = {}
            self.page_hash_mapping = {}
            self.page_results = {}
            self.current_page_index = 0
            
            # Clear custom receiver images
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            if file_ext == '.pdf':
                self.load_pdf_file(file_path)
            else:
                self.load_single_image(file_path)
            
            self.process_button.configure(state=tk.NORMAL)
            
            # Auto-process if enabled
            if self.auto_process_var.get():
                self.root.after(100, self.process_current_file)  # Small delay to allow UI update
            
        except Exception as e:
            self.log_message(f"❌ Error loading file: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def load_single_image(self, file_path):
        """Load a single image file."""
        try:
            # Load image
            cv_image = cv2.imread(file_path)
            if cv_image is None:
                raise ValueError("Could not load image - invalid format or corrupted file")
            
            self.current_pages = {0: cv_image}
            self.original_image = cv_image
            self.display_image(cv_image)
            
            # Hide navigation for single images
            self.nav_frame.pack_forget()
            
            self.log_message(f"✅ Loaded image: {cv_image.shape[1]}x{cv_image.shape[0]} pixels")
            
        except Exception as e:
            raise Exception(f"Failed to load image: {e}")
    
    def load_pdf_file(self, file_path):
        """Load PDF file using Dynamsoft SDK - pages will be captured by intermediate receiver."""
        try:
            self.log_message("📄 Loading PDF file...")
            
            # Clear previous intermediate result images
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            # Set the PDF file path
            self.current_pages = {}  # Will be populated after processing
            self.current_page_index = 0
            
            # Show placeholder until processing is complete
            self.show_pdf_loading_message()
            
            self.log_message("✅ PDF file loaded - process to view pages", "SUCCESS")
            
        except Exception as e:
            raise Exception(f"Failed to load PDF: {e}")
    
    def show_pdf_loading_message(self):
        """Show a message indicating PDF is loaded and ready to process."""
        self.image_canvas.delete("all")
        self.image_canvas.create_text(
            300, 200,
            text="📄 PDF File Loaded\n\n🔍 Click 'Detect Barcodes' to process\nand view PDF pages\n\nDynamsoft SDK will automatically\nconvert PDF pages during processing",
            font=('Arial', 12),
            fill='#666666',
            anchor=tk.CENTER,
            justify=tk.CENTER
        )
    
    def display_image(self, cv_image):
        """Display an OpenCV image on the canvas."""
        try:
            if cv_image is None:
                return
            
            # Store original for zoom operations
            self.original_image = cv_image
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)
            
            # Apply zoom
            self.apply_zoom_to_image(pil_image)
            
        except Exception as e:
            self.log_message(f"❌ Error displaying image: {e}", "ERROR")
    
    def apply_zoom_to_image(self, pil_image):
        """Apply current zoom level to image and display it."""
        try:
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not yet initialized, try again later
                self.root.after(100, lambda: self.apply_zoom_to_image(pil_image))
                return
            
            original_width, original_height = pil_image.size
            
            if self.zoom_var.get() == "Fit":
                # Calculate scaling factor to fit canvas
                scale_x = canvas_width / original_width
                scale_y = canvas_height / original_height
                scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond 100%
                self.current_zoom = scale
            else:
                # Use specified zoom percentage
                zoom_percent = int(self.zoom_var.get().rstrip('%'))
                self.current_zoom = zoom_percent / 100.0
                scale = self.current_zoom
            
            new_width = max(1, int(original_width * scale))
            new_height = max(1, int(original_height * scale))
            
            # Resize image
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_photo = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and remove drop zone text
            self.image_canvas.delete("all")
            
            # Display image centered
            self.image_id = self.image_canvas.create_image(
                new_width // 2, new_height // 2,
                image=self.current_photo,
                anchor=tk.CENTER
            )
            
            # Update scroll region
            self.image_canvas.configure(scrollregion=(0, 0, new_width, new_height))
            
            # Update status
            zoom_text = f"Zoom: {int(self.current_zoom * 100)}%"
            self.status_bar.configure(text=f"Image displayed - {zoom_text}")
            
        except Exception as e:
            self.log_message(f"❌ Error applying zoom: {e}", "ERROR")
    
    def on_zoom_change(self, event=None):
        """Handle zoom level change."""
        if self.original_image is not None:
            # Get current page image (with or without annotations)
            current_cv_image = self.get_current_display_image()
            rgb_image = cv2.cvtColor(current_cv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            self.apply_zoom_to_image(pil_image)
    
    def zoom_in(self):
        """Zoom in by 25%."""
        current_zoom = int(self.current_zoom * 100)
        new_zoom = min(current_zoom + 25, 500)  # Max 500%
        self.zoom_var.set(f"{new_zoom}%")
        self.on_zoom_change()
    
    def zoom_out(self):
        """Zoom out by 25%."""
        current_zoom = int(self.current_zoom * 100)
        new_zoom = max(current_zoom - 25, 10)  # Min 10%
        self.zoom_var.set(f"{new_zoom}%")
        self.on_zoom_change()
    
    def reset_view(self):
        """Reset zoom to fit."""
        self.zoom_var.set("Fit")
        self.on_zoom_change()
    
    def on_mouse_wheel_zoom(self, event):
        """Handle mouse wheel zoom."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_canvas_click(self, event):
        """Handle canvas click events."""
        # Could be used for future features like barcode selection
        pass
    
    def get_current_display_image(self):
        """Get the current page image with annotations if available."""
        if self.current_page_index not in self.current_pages:
            return None
        
        cv_image = self.current_pages[self.current_page_index]
        
        # If we have results for this page, draw them
        if self.current_page_index in self.page_results:
            cv_image = self.draw_barcode_annotations(cv_image, self.page_results[self.current_page_index])
        
        return cv_image
    
    def prev_page(self):
        """Navigate to previous page."""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_current_page()
            self.update_navigation_state()
    
    def next_page(self):
        """Navigate to next page."""
        if self.current_page_index < len(self.current_pages) - 1:
            self.current_page_index += 1
            self.display_current_page()
            self.update_navigation_state()
    
    def jump_to_page(self, event=None):
        """Jump to a specific page number."""
        try:
            page_num = int(self.page_entry.get())
            if 1 <= page_num <= len(self.current_pages):
                self.current_page_index = page_num - 1
                self.display_current_page()
                self.update_navigation_state()
                self.page_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Invalid Page", f"Page number must be between 1 and {len(self.current_pages)}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid page number")
    
    def display_current_page(self):
        """Display the current page."""
        current_image = self.get_current_display_image()
        if current_image is not None:
            self.display_image(current_image)
            self.display_page_results()
    
    def update_navigation_state(self):
        """Update navigation button states and page label."""
        total_pages = len(self.current_pages)
        current = self.current_page_index + 1
        
        self.page_label.configure(text=f"Page: {current}/{total_pages}")
        
        self.prev_button.configure(state=tk.NORMAL if self.current_page_index > 0 else tk.DISABLED)
        self.next_button.configure(state=tk.NORMAL if self.current_page_index < total_pages - 1 else tk.DISABLED)
    
    def process_current_file(self):
        """Process the current file for barcode detection."""
        if not self.current_file_path or self.is_processing:
            return
        
        self.is_processing = True
        self.process_button.configure(state=tk.DISABLED, text="🔄 Processing...")
        self.progress_bar.start()
        
        # Clear previous results
        self.page_results = {}
        self.page_hash_mapping = {}
        if self.custom_receiver:
            self.custom_receiver.images.clear()
        
        # Record start time
        self.process_start_time = datetime.datetime.now()
        
        self.log_message("🔍 Starting barcode detection...")
        
        # Run processing in a separate thread
        thread = threading.Thread(target=self._process_file_thread)
        thread.daemon = True
        thread.start()
    
    def _process_file_thread(self):
        """Process file in a separate thread."""
        try:
            results = self.cvr_instance.capture_multi_pages(
                self.current_file_path, 
                EnumPresetTemplate.PT_READ_BARCODES.value
            )
            
            # Process results on main thread
            self.root.after(0, self._process_results, results)
            
        except Exception as e:
            self.root.after(0, self._process_error, str(e))
    
    def _process_results(self, results):
        """Process detection results on main thread."""
        try:
            self.page_results = {}
            self.page_hash_mapping = {}
            total_barcodes = 0
            
            result_list = results.get_results()
            
            # First, build the page mapping from results to maintain correct order
            for i, result in enumerate(result_list):
                if result.get_error_code() == EnumErrorCode.EC_OK:
                    hash_id = result.get_original_image_hash_id()
                    items = result.get_items()
                    
                    # Map page index to hash_id and store results
                    page_index = i
                    self.page_hash_mapping[page_index] = hash_id
                    self.page_results[page_index] = items
                    total_barcodes += len(items)
                else:
                    self.log_message(f"⚠️ Error on page {i+1}: {result.get_error_string()}", "WARNING")
            
            # Extract pages from intermediate receiver for PDF files AFTER building the mapping
            if self.current_file_path and self.current_file_path.lower().endswith('.pdf'):
                self._extract_pdf_pages_from_receiver()
            
            # Setup navigation for multi-page PDFs
            if self.current_file_path and self.current_file_path.lower().endswith('.pdf') and len(self.current_pages) > 1:
                self.nav_frame.pack(fill=tk.X, pady=10)
                self.update_navigation_state()
            elif len(self.current_pages) <= 1:
                self.nav_frame.pack_forget()
            
            # Calculate processing time
            process_time = (datetime.datetime.now() - self.process_start_time).total_seconds()
            
            # Update UI
            self.results_summary.configure(text=f"Total Barcodes: {total_barcodes}")
            self.display_current_page()
            self.display_page_results()
            
            # Enable export buttons if barcodes found
            state = tk.NORMAL if total_barcodes > 0 else tk.DISABLED
            self.export_button.configure(state=state)
            self.copy_button.configure(state=state)
            
            # Update time display
            self.time_label.configure(text=f"Processing time: {process_time:.2f}s")
            
            self.log_message(f"✅ Processing complete! Found {total_barcodes} barcode(s) in {process_time:.2f}s", "SUCCESS")
            
        except Exception as e:
            self._process_error(str(e))
        finally:
            self.is_processing = False
            self.process_button.configure(state=tk.NORMAL, text="🔍 Detect Barcodes")
            self.progress_bar.stop()
    
    def _process_error(self, error_message):
        """Handle processing errors."""
        self.log_message(f"❌ Processing error: {error_message}", "ERROR")
        messagebox.showerror("Processing Error", f"Failed to process file: {error_message}")
        
        self.is_processing = False
        self.process_button.configure(state=tk.NORMAL, text="🔍 Detect Barcodes")
        self.progress_bar.stop()
    
    def draw_barcode_annotations(self, cv_image, items):
        """Draw barcode detection results on the image."""
        if not items:
            return cv_image
        
        annotated_image = cv_image.copy()
        
        for i, item in enumerate(items):
            location = item.get_location()
            points = [(int(point.x), int(point.y)) for point in location.points]
            
            # Draw contour with different colors for each barcode
            colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            color = colors[i % len(colors)]
            
            cv2.drawContours(annotated_image, [np.array(points)], 0, color, CONTOUR_THICKNESS)
            
            # Add text label with background for better visibility
            text = item.get_text()
            if len(text) > 20:  # Truncate long text
                text = text[:17] + "..."
            
            x1, y1 = points[0]
            
            # Get text size for background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_THICKNESS)
            
            # Draw background rectangle
            cv2.rectangle(annotated_image, 
                         (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                         (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                         (255, 255, 255), -1)
            
            # Draw border around background
            cv2.rectangle(annotated_image, 
                         (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                         (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                         color, 1)
            
            # Draw text
            cv2.putText(annotated_image, text, (x1, y1 - TEXT_OFFSET_Y),
                       cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
            
            # Add barcode number
            cv2.putText(annotated_image, f"#{i+1}", (x1 - 20, y1),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return annotated_image
    
    def display_page_results(self):
        """Display barcode results for the current page with enhanced formatting."""
        self.results_text.delete(1.0, tk.END)
        
        if self.current_page_index not in self.page_results:
            self.results_text.insert(tk.END, "No barcode results for this page.\n")
            self.page_summary.configure(text="")
            return
        
        items = self.page_results[self.current_page_index]
        
        if not items:
            self.results_text.insert(tk.END, "No barcodes found on this page.\n")
            self.page_summary.configure(text="")
            return
        
        # Update page summary
        self.page_summary.configure(text=f"Page {self.current_page_index + 1}: {len(items)} barcode(s)")
        
        # Beautiful header with page info
        self.results_text.insert(tk.END, f"📄 PAGE {self.current_page_index + 1} RESULTS\n", 'header')
        self.results_text.insert(tk.END, "═" * 50 + "\n\n", 'separator')
        
        for i, item in enumerate(items, 1):
            format_type = item.get_format_string()
            text = item.get_text()
            
            # Barcode header with nice styling
            self.results_text.insert(tk.END, f"� BARCODE #{i:02d}\n", 'barcode_num')
            self.results_text.insert(tk.END, "─" * 25 + "\n", 'separator')
            
            # Format with emoji and better spacing
            self.results_text.insert(tk.END, "📋 Format:  ", 'format')
            self.results_text.insert(tk.END, f"{format_type}\n", 'format')
            
            # Content with better visual separation
            self.results_text.insert(tk.END, "💬 Content: ", 'text_content')
            self.results_text.insert(tk.END, f'"{text}"\n', 'text_content')
            
            # Confidence if available and enabled
            if self.show_confidence_var.get():
                try:
                    confidence = item.get_confidence()
                    if confidence is not None:
                        self.results_text.insert(tk.END, "📊 Confidence: ", 'format')
                        self.results_text.insert(tk.END, f"{confidence}/100\n", 'format')
                except Exception as e:
                    # If confidence is not available, show a debug message (only in development)
                    pass
            
            # Location points with better formatting
            location = item.get_location()
            self.results_text.insert(tk.END, "📍 Location: ", 'location')
            
            # Format points more elegantly
            points = location.points
            if len(points) >= 4:
                # Show as corners: TL → TR → BR → BL
                point_labels = ["TL", "TR", "BR", "BL"]
                points_text = " → ".join([f"{label}({int(p.x)},{int(p.y)})" for p, label in zip(points[:4], point_labels)])
            else:
                points_text = " → ".join([f"({int(p.x)},{int(p.y)})" for p in points])
            
            self.results_text.insert(tk.END, f"{points_text}\n", 'location')
            
            # Area calculation with better formatting
            try:
                points_coords = [(p.x, p.y) for p in location.points]
                area = self.calculate_polygon_area(points_coords)
                self.results_text.insert(tk.END, "📐 Area:     ", 'location')
                
                # Format area with appropriate units
                if area > 10000:
                    self.results_text.insert(tk.END, f"{area:,.0f} px² ({area/10000:.1f}k px²)\n", 'location')
                else:
                    self.results_text.insert(tk.END, f"{area:.0f} px²\n", 'location')
            except:
                pass
            
            # Add some spacing between barcodes
            if i < len(items):
                self.results_text.insert(tk.END, "\n" + "▪" * 40 + "\n\n", 'separator')
        
        # Final summary
        self.results_text.insert(tk.END, f"\n✨ Found {len(items)} barcode(s) on this page", 'header')
    
    def calculate_polygon_area(self, points):
        """Calculate the area of a polygon using the shoelace formula."""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2.0
    
    def export_results(self):
        """Export barcode results to a file."""
        if not self.page_results:
            messagebox.showwarning("No Results", "No barcode results to export.")
            return
        
        # Ask for export format
        formats = ["Text (.txt)", "CSV (.csv)", "JSON (.json)"]
        choice = self._ask_export_format(formats)
        
        if choice is None:
            return
        
        # Get file extension
        extensions = {0: ".txt", 1: ".csv", 2: ".json"}
        ext = extensions[choice]
        
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=ext,
            filetypes=[(f"{formats[choice].split()[0]} files", f"*{ext}"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                if ext == ".txt":
                    self._export_to_text(file_path)
                elif ext == ".csv":
                    self._export_to_csv(file_path)
                elif ext == ".json":
                    self._export_to_json(file_path)
                
                self.log_message(f"💾 Results exported to: {os.path.basename(file_path)}", "SUCCESS")
                messagebox.showinfo("Export Complete", f"Results exported successfully to:\\n{file_path}")
                
            except Exception as e:
                self.log_message(f"❌ Export error: {e}", "ERROR")
                messagebox.showerror("Export Error", f"Failed to export results: {e}")
    
    def _ask_export_format(self, formats):
        """Ask user to choose export format."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Export Format")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        result = [None]
        
        ttk.Label(dialog, text="Select export format:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        var = tk.IntVar()
        for i, fmt in enumerate(formats):
            ttk.Radiobutton(dialog, text=fmt, variable=var, value=i).pack(anchor=tk.W, padx=20, pady=2)
        
        var.set(0)  # Default to first option
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def on_ok():
            result[0] = var.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return result[0]
    
    def _export_to_text(self, file_path):
        """Export results to text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Dynamsoft Barcode Reader - Detection Results\\n")
            f.write("=" * 60 + "\\n")
            f.write(f"Source File: {self.current_file_path}\\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write("=" * 60 + "\\n\\n")
            
            total_barcodes = 0
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                f.write(f"Page {page_index + 1}:\\n")
                f.write("-" * 20 + "\\n")
                
                if not items:
                    f.write("No barcodes found.\\n\\n")
                    continue
                
                for i, item in enumerate(items, 1):
                    format_type = item.get_format_string()
                    text = item.get_text()
                    
                    f.write(f"Barcode {i}:\\n")
                    f.write(f"  Format: {format_type}\\n")
                    f.write(f"  Text: {text}\\n")
                    
                    location = item.get_location()
                    f.write("  Location Points:\\n")
                    for j, point in enumerate(location.points):
                        f.write(f"    Point {j+1}: ({int(point.x)}, {int(point.y)})\\n")
                    f.write("\\n")
                    
                    total_barcodes += 1
                
                f.write("\\n")
            
            f.write(f"Total Barcodes Found: {total_barcodes}\\n")
    
    def _export_to_csv(self, file_path):
        """Export results to CSV file."""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Page', 'Barcode_Number', 'Format', 'Text', 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4'])
            
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                
                for i, item in enumerate(items, 1):
                    format_type = item.get_format_string()
                    text = item.get_text()
                    location = item.get_location()
                    
                    points = [int(p.x) for p in location.points] + [int(p.y) for p in location.points]
                    row = [page_index + 1, i, format_type, text] + points[:8]  # Limit to 4 points
                    writer.writerow(row)
    
    def _export_to_json(self, file_path):
        """Export results to JSON file."""
        import json
        
        export_data = {
            "source_file": self.current_file_path,
            "export_time": datetime.datetime.now().isoformat(),
            "total_pages": len(self.current_pages),
            "pages": []
        }
        
        for page_index in sorted(self.page_results.keys()):
            items = self.page_results[page_index]
            
            page_data = {
                "page_number": page_index + 1,
                "barcode_count": len(items),
                "barcodes": []
            }
            
            for i, item in enumerate(items, 1):
                format_type = item.get_format_string()
                text = item.get_text()
                location = item.get_location()
                
                barcode_data = {
                    "barcode_number": i,
                    "format": format_type,
                    "text": text,
                    "location": {
                        "points": [{"x": int(p.x), "y": int(p.y)} for p in location.points]
                    }
                }
                
                page_data["barcodes"].append(barcode_data)
            
            export_data["pages"].append(page_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def copy_to_clipboard(self):
        """Copy barcode results to clipboard."""
        if not self.page_results:
            messagebox.showwarning("No Results", "No barcode results to copy.")
            return
        
        try:
            # Generate text summary
            text_content = []
            for page_index in sorted(self.page_results.keys()):
                items = self.page_results[page_index]
                if items:
                    text_content.append(f"Page {page_index + 1}:")
                    for i, item in enumerate(items, 1):
                        text_content.append(f"  {i}. [{item.get_format_string()}] {item.get_text()}")
                    text_content.append("")
            
            clipboard_text = "\\n".join(text_content)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            self.log_message("📋 Results copied to clipboard", "SUCCESS")
            messagebox.showinfo("Copied", "Barcode results copied to clipboard!")
            
        except Exception as e:
            self.log_message(f"❌ Clipboard error: {e}", "ERROR")
            messagebox.showerror("Clipboard Error", f"Failed to copy to clipboard: {e}")
    
    def clear_all(self):
        """Clear all data and reset the application."""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all data?"):
            self.current_file_path = None
            self.current_pages = {}
            self.page_hash_mapping = {}
            self.page_results = {}
            self.current_page_index = 0
            self.original_image = None
            
            # Clear custom receiver
            if self.custom_receiver:
                self.custom_receiver.images.clear()
            
            # Clear UI
            self.image_canvas.delete("all")
            self.setup_drop_zone()
            
            self.results_text.delete(1.0, tk.END)
            self.results_summary.configure(text="Total Barcodes: 0")
            
            # Safely configure page_summary if it exists
            if hasattr(self, 'page_summary'):
                self.page_summary.configure(text="")
            
            self.file_info_label.configure(text="No file loaded")
            self.file_size_label.configure(text="")
            self.time_label.configure(text="")
            
            # Reset buttons
            self.process_button.configure(state=tk.DISABLED)
            self.export_button.configure(state=tk.DISABLED)
            self.copy_button.configure(state=tk.DISABLED)
            
            # Hide navigation
            self.nav_frame.pack_forget()
            
            # Reset zoom
            self.zoom_var.set("Fit")
            self.current_zoom = 1.0
            
            self.log_message("🗑️ Application reset")
    
    def _extract_pdf_pages_from_receiver(self):
        """Extract PDF pages from the intermediate result receiver."""
        if not self.custom_receiver or not self.custom_receiver.images:
            return
        
        # Clear current pages
        self.current_pages = {}
        
        # Extract pages using the correct hash_id order from page_hash_mapping
        # This ensures pages are in the correct sequence as returned by the SDK
        for page_index in sorted(self.page_hash_mapping.keys()):
            hash_id = self.page_hash_mapping[page_index]
            if hash_id in self.custom_receiver.images:
                numpy_image = self.custom_receiver.images[hash_id]
                if numpy_image is not None:
                    try:
                        # Convert from numpy array to OpenCV format if needed
                        if hasattr(numpy_image, 'shape') and len(numpy_image.shape) == 3:
                            # Already in BGR format for OpenCV
                            self.current_pages[page_index] = numpy_image
                        elif hasattr(numpy_image, 'shape'):
                            # Convert if needed
                            self.current_pages[page_index] = numpy_image
                        else:
                            self.log_message(f"⚠️ Unexpected image format for page {page_index}: {type(numpy_image)}", "WARNING")
                    except Exception as e:
                        self.log_message(f"⚠️ Error processing page {page_index}: {e}", "WARNING")
                        continue
        
        # Set the first page as current
        if self.current_pages:
            self.current_page_index = 0
            # Get the first page in correct order
            first_page_index = min(self.current_pages.keys())
            self.original_image = self.current_pages[first_page_index]
            self.log_message(f"✅ Extracted {len(self.current_pages)} page(s) from PDF in correct order", "SUCCESS")
        else:
            self.log_message("⚠️ No pages extracted from PDF", "WARNING")


def main():
    """Main application entry point."""
    # Create root window
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()
        print("Warning: tkinterdnd2 not available. Drag and drop functionality disabled.")
    
    # Set window properties
    root.title("Dynamsoft Barcode Reader - GUI")
    
    # Set the application icon (if available)
    try:
        root.iconbitmap('barcode_icon.ico')
    except:
        pass  # Icon file not found, continue without it
    
    # Create and run the application
    app = BarcodeReaderGUI(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit the Barcode Reader?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    print("🚀 Starting Dynamsoft Barcode Reader GUI...")
    print("📁 Supported formats: JPG, PNG, BMP, TIFF, WEBP" + (", PDF" if PDF_SUPPORT else ""))
    
    # Start the main loop
    root.mainloop()


if __name__ == '__main__':
    main()
