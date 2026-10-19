import sys
import os
from typing import Optional, Tuple, List
import cv2
import numpy as np
from dynamsoft_capture_vision_bundle import *

# Constants
LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
CONTOUR_COLOR = (0, 255, 0)  # Green
TEXT_COLOR = (0, 0, 255)     # Red
CONTOUR_THICKNESS = 2
TEXT_THICKNESS = 2
FONT_SCALE = 0.5
TEXT_OFFSET_Y = 10
QUIT_COMMANDS = {'q', 'quit', 'exit'}

# Display settings
MAX_WINDOW_WIDTH = 1200
MAX_WINDOW_HEIGHT = 800
WINDOW_MARGIN = 50

# ANSI color codes for terminal output
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"

class MyIntermediateResultReceiver(IntermediateResultReceiver):
    """Enhanced intermediate result receiver for capturing page images."""
    
    def __init__(self, im: IntermediateResultManager):
        self.images = {}
        self.im = im
        super().__init__()

    def on_localized_barcodes_received(self, result: "LocalizedBarcodesUnit", info: IntermediateResultExtraInfo) -> None:
        """Handle localized barcode results and capture images."""
        try:
            hash_id = result.get_original_image_hash_id()
            if hash_id and self.im:
                image = self.im.get_original_image(hash_id)
                
                if image is not None and self.images.get(hash_id) is None:
                    try:
                        image_io = ImageIO()
                        saved = image_io.save_to_numpy(image)
                        if saved is not None:
                            # Handle different return formats
                            if isinstance(saved, tuple) and len(saved) == 3:
                                error_code, error_message, numpy_array = saved
                                if error_code == 0 and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                                    print(f"{CYAN}✓ Captured image for hash ID: {hash_id}{RESET}")
                            elif isinstance(saved, tuple) and len(saved) == 2:
                                success, numpy_array = saved
                                if success and numpy_array is not None:
                                    self.images[hash_id] = numpy_array
                                    print(f"{CYAN}✓ Captured image for hash ID: {hash_id}{RESET}")
                            else:
                                # Direct numpy array return
                                self.images[hash_id] = saved
                                print(f"{CYAN}✓ Captured image for hash ID: {hash_id}{RESET}")
                    except Exception as e:
                        print(f"{YELLOW}⚠ Warning: Could not save intermediate image: {e}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠ Warning: Error in intermediate result receiver: {e}{RESET}")

def get_screen_size() -> Tuple[int, int]:
    """Get screen dimensions for window sizing.
    
    Returns:
        Tuple of (width, height) or default values if detection fails
    """
    try:
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
        return screen_width, screen_height
    except:
        # Fallback to default values
        return 1920, 1080

def resize_image_for_display(image: np.ndarray, max_width: int = MAX_WINDOW_WIDTH, max_height: int = MAX_WINDOW_HEIGHT) -> Tuple[np.ndarray, float]:
    """Resize image to fit within display constraints while maintaining aspect ratio.
    
    Args:
        image: Input image array
        max_width: Maximum window width
        max_height: Maximum window height
        
    Returns:
        Tuple of (resized_image, scale_factor)
    """
    height, width = image.shape[:2]
    
    # Calculate scaling factor
    scale_width = max_width / width
    scale_height = max_height / height
    scale = min(scale_width, scale_height, 1.0)  # Don't upscale
    
    if scale < 1.0:
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized_image, scale
    
    return image, 1.0

def setup_window(window_name: str, image: np.ndarray) -> None:
    """Setup OpenCV window with proper positioning and sizing.
    
    Args:
        window_name: Name of the window
        image: Image to be displayed
    """
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    # Get screen size and position window
    screen_width, screen_height = get_screen_size()
    height, width = image.shape[:2]
    
    # Center the window
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    
    cv2.moveWindow(window_name, x, y)

def initialize_license() -> Tuple[bool, Optional[str]]:
    """Initialize the Dynamsoft license.
    
    Returns:
        Tuple of (success, error_message)
    """
    error_code, error_message = LicenseManager.init_license(LICENSE_KEY)
    
    if error_code == EnumErrorCode.EC_OK or error_code == EnumErrorCode.EC_LICENSE_CACHE_USED:
        return True, None
    else:
        return False, f"License initialization failed: ErrorCode: {error_code}, ErrorString: {error_message}"

def get_user_input() -> str:
    """Get image path input from user with clear instructions."""
    prompt = (
        f"\n{CYAN}{'='*60}\n"
        f"📁 INPUT OPTIONS:\n"
        f"{'='*60}\n"
        f"• Enter full path to image file (JPG, PNG, BMP, TIFF, WEBP)\n"
        f"• Enter full path to PDF file (multi-page support)\n"
        f"• Type 'q', 'quit', or 'exit' to quit\n"
        f"{'='*60}{RESET}\n"
        f">> Path: "
    )
    return input(prompt).strip('\'"').strip()

def validate_image_path(image_path: str) -> bool:
    """Validate if the image path exists and is a valid file.
    
    Args:
        image_path: Path to the image or PDF file
        
    Returns:
        True if valid, False otherwise
    """
    if not image_path:  # Empty path for sample image
        return True
        
    if not os.path.exists(image_path):
        print(f"{RED}✗ Error: The file path '{image_path}' does not exist.{RESET}")
        return False
        
    if not os.path.isfile(image_path):
        print(f"{RED}✗ Error: The path '{image_path}' is not a file.{RESET}")
        return False
        
    # Check if it's a valid image or PDF file
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.pdf'}
    _, ext = os.path.splitext(image_path.lower())
    
    if ext not in valid_extensions:
        print(f"{YELLOW}⚠ Warning: '{ext}' might not be a supported format.{RESET}")
        print(f"{CYAN}ℹ Supported formats: {', '.join(sorted(valid_extensions))}{RESET}")
    elif ext == '.pdf':
        print(f"{BLUE}📄 PDF file detected - will process all pages{RESET}")
        
    return True

def draw_barcode_annotations(cv_image: np.ndarray, items) -> np.ndarray:
    """Draw barcode detection results directly on the original image.
    
    Args:
        cv_image: OpenCV image array (original size)
        items: Detected barcode items
        
    Returns:
        Annotated image at original size
    """
    if cv_image is None:
        return None
        
    annotated_image = cv_image.copy()
    
    # Adjust annotation parameters based on image size
    height, width = annotated_image.shape[:2]
    font_scale = max(0.3, min(1.0, (width + height) / 2000))
    thickness = max(1, int(2 * (width + height) / 2000))
    
    # Use different colors for multiple barcodes
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    
    for i, item in enumerate(items):
        color = colors[i % len(colors)]
        location = item.get_location()
        points = [(int(point.x), int(point.y)) for point in location.points]
        
        # Draw contour
        cv2.drawContours(annotated_image, [np.array(points)], 0, color, thickness)
        
        # Add text label with background for better visibility
        text = item.get_text()
        if len(text) > 30:  # Truncate very long text
            text = text[:27] + "..."
            
        x1, y1 = points[0]
        
        # Calculate text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        
        # Draw background rectangle
        cv2.rectangle(annotated_image, 
                     (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                     (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                     (255, 255, 255), -1)
        
        # Draw border
        cv2.rectangle(annotated_image, 
                     (x1 - 2, y1 - text_height - TEXT_OFFSET_Y - 2),
                     (x1 + text_width + 2, y1 - TEXT_OFFSET_Y + baseline + 2),
                     color, 1)
        
        # Draw text
        cv2.putText(annotated_image, text, (x1, y1 - TEXT_OFFSET_Y),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, TEXT_COLOR, thickness)
        
        # Add barcode number
        cv2.putText(annotated_image, f"#{i+1}", (x1 - 20, y1),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, color, max(1, thickness - 1))
    
    return annotated_image

def print_barcode_details(items, page_number: int = None) -> None:
    """Print detailed information about detected barcodes with enhanced formatting.
    
    Args:
        items: Detected barcode items
        page_number: Page number (for PDF files)
    """
    page_info = f" (Page {page_number})" if page_number is not None else ""
    print(f'\n{GREEN}🔍 Found {len(items)} barcode(s){page_info}:{RESET}')
    
    for i, item in enumerate(items, 1):
        format_type = item.get_format_string()
        text = item.get_text()
        
        print(f"\n{CYAN}{'─' * 25}")
        print(f"📊 Barcode #{i}{RESET}")
        print(f"{CYAN}{'─' * 25}{RESET}")
        print(f"{BLUE}📋 Format:{RESET} {format_type}")
        print(f"{BLUE}💬 Content:{RESET} {text}")
        
        # Show confidence if available
        try:
            confidence = item.get_confidence()
            if confidence is not None:
                print(f"{BLUE}📈 Confidence:{RESET} {confidence}/100")
        except:
            pass
        
        # Location information
        location = item.get_location()
        print(f"{BLUE}📍 Location Points:{RESET}")
        for j, point in enumerate(location.points):
            corner_labels = ["TL", "TR", "BR", "BL"]
            label = corner_labels[j] if j < len(corner_labels) else f"P{j+1}"
            print(f"   {label}: ({int(point.x):4d}, {int(point.y):4d})")
    
    print(f"{CYAN}{'═' * 50}{RESET}")

def process_image(cvr_instance: CaptureVisionRouter, image_path: str, custom_receiver: MyIntermediateResultReceiver) -> bool:
    """Process a single image or PDF file for barcode detection with individual page display.
    
    Args:
        cvr_instance: CaptureVisionRouter instance
        image_path: Path to the image or PDF file
        custom_receiver: Custom intermediate result receiver
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        print(f"\n{BLUE}🔄 Processing: {os.path.basename(image_path)}{RESET}")
        
        # Clear previous images
        custom_receiver.images.clear()
        
        # Capture barcodes from all pages
        results = cvr_instance.capture_multi_pages(image_path, EnumPresetTemplate.PT_READ_BARCODES.value)
        result_list = results.get_results()
        
        if not result_list:
            print(f"{YELLOW}⚠ No results returned from processing{RESET}")
            return False
        
        total_barcodes = 0
        processed_pages = 0
        
        # Process each page/result
        for page_index, result in enumerate(result_list):
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print(f"{RED}✗ Error on page {page_index + 1}: {result.get_error_string()}{RESET}")
                continue
            
            hash_id = result.get_original_image_hash_id()
            items = result.get_items()
            page_number = page_index + 1 if len(result_list) > 1 else None
            
            if not items:
                page_info = f" (Page {page_number})" if page_number else ""
                print(f"{YELLOW}⚠ No barcodes found{page_info}{RESET}")
            else:
                # Print barcode details
                print_barcode_details(items, page_number)
                total_barcodes += len(items)
            
            # Display image with annotations if available
            if hash_id in custom_receiver.images:
                try:
                    # Get the image from intermediate results
                    image_data = custom_receiver.images[hash_id]
                    
                    # Handle different image data formats
                    if isinstance(image_data, np.ndarray):
                        cv_image = image_data
                    elif isinstance(image_data, tuple) and len(image_data) >= 3:
                        cv_image = image_data[2]  # Third element should be the numpy array
                    else:
                        print(f"{YELLOW}⚠ Unexpected image data format for page {page_number}{RESET}")
                        continue
                    
                    if cv_image is not None and cv_image.size > 0:
                        # Draw annotations directly on original image (no coordinate scaling)
                        if items:
                            annotated_image = draw_barcode_annotations(cv_image, items)
                        else:
                            annotated_image = cv_image.copy()
                        
                        # Scale the annotated image for display
                        display_image, _ = resize_image_for_display(annotated_image)
                        
                        # Setup and show window with hash ID for unique identification
                        window_name = f"Page {page_number} ({hash_id})" if page_number else f"Barcode Detection - {os.path.basename(image_path)} ({hash_id})"
                        setup_window(window_name, display_image)
                        cv2.imshow(window_name, display_image)
                        
                        processed_pages += 1
                        
                        # For multi-page documents, wait for user input between pages
                        if len(result_list) > 1:
                            print(f"\n{CYAN}📄 Displaying Page {page_number} ({hash_id}) - Press any key to continue to next page...{RESET}")
                            cv2.waitKey(0)
                            cv2.destroyWindow(window_name)
                        
                except Exception as e:
                    print(f"{RED}✗ Error displaying page {page_number}: {e}{RESET}")
                    continue
            else:
                page_info = f" page {page_number}" if page_number else ""
                print(f"{YELLOW}⚠ No image data available for{page_info}{RESET}")
        
        # Final summary
        if len(result_list) > 1:
            print(f"\n{GREEN}✅ Processing complete!")
            print(f"   📄 Pages processed: {processed_pages}/{len(result_list)}")
            print(f"   🔍 Total barcodes found: {total_barcodes}{RESET}")
        elif processed_pages == 0:
            print(f"{YELLOW}⚠ No pages could be displayed{RESET}")
        else:
            # For single images, wait for final key press
            print(f"\n{CYAN}Press any key to close and continue...{RESET}")
            cv2.waitKey(0)
        
        cv2.destroyAllWindows()
        return True
        
    except Exception as e:
        print(f"{RED}✗ Unexpected error during processing: {e}{RESET}")
        cv2.destroyAllWindows()
        return False


def main() -> None:
    """Main application logic with enhanced user experience."""
    print(f"{CYAN}{'*' * 70}")
    print(f"🔍 Welcome to Dynamsoft Capture Vision - Barcode Scanner")
    print(f"📄 Supports Images (JPG, PNG, BMP, TIFF, WEBP) and PDF files")
    print(f"{'*' * 70}{RESET}")
    
    # Initialize license
    print(f"\n{BLUE}🔐 Initializing license...{RESET}")
    success, error_msg = initialize_license()
    if not success:
        print(f"{RED}✗ {error_msg}{RESET}")
        input("Press Enter to exit...")
        return
    
    print(f"{GREEN}✅ License initialized successfully!{RESET}")
    
    try:
        # Initialize capture vision router
        print(f"{BLUE}🚀 Initializing barcode detection engine...{RESET}")
        cvr_instance = CaptureVisionRouter()
        intermediate_result_manager = cvr_instance.get_intermediate_result_manager()
        custom_receiver = MyIntermediateResultReceiver(intermediate_result_manager)
        intermediate_result_manager.add_result_receiver(custom_receiver)
        print(f"{GREEN}✅ Engine ready!{RESET}")
        
        # Main processing loop
        while True:
            image_path = get_user_input()
            
            # Check for quit commands
            if image_path.lower() in QUIT_COMMANDS:
                print(f"{GREEN}👋 Goodbye!{RESET}")
                break
            
            # Validate input
            if not image_path:
                print(f"{YELLOW}⚠ Please provide a valid file path{RESET}")
                continue
                
            if not validate_image_path(image_path):
                continue
            
            # Process the file
            print(f"\n{BLUE}{'─' * 50}{RESET}")
            success = process_image(cvr_instance, image_path, custom_receiver)
            if not success:
                print(f"{RED}✗ Failed to process the file. Please try again.{RESET}")
            print(f"{BLUE}{'─' * 50}{RESET}")
                
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠ Operation cancelled by user.{RESET}")
    except Exception as e:
        print(f"{RED}✗ Unexpected error: {e}{RESET}")
    finally:
        cv2.destroyAllWindows()
        print(f"{CYAN}📱 Application closed.{RESET}")

if __name__ == '__main__':
    main()
