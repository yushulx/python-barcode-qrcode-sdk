#!/usr/bin/env python3
"""
Command-line barcode scanner using Dynamsoft Barcode Reader SDK
"""
import sys
import os
from dynamsoft_barcode_reader_bundle import *


def scan_barcode(image_path):
    """
    Scan barcode from a single image file
    
    Args:
        image_path: Path to the image file containing barcode
    """
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return
    
    # Initialize license
    # Using public trial license (requires network connection)
    errorCode, errorMsg = LicenseManager.init_license("DLS2eyJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSJ9")
    if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print(f"License initialization failed: ErrorCode: {errorCode}, ErrorString: {errorMsg}")
        return
    
    # Create CaptureVisionRouter instance
    cvr_instance = CaptureVisionRouter()
    
    # Capture barcode from image
    print(f"Scanning barcode from: {image_path}")
    result = cvr_instance.capture(image_path, EnumPresetTemplate.PT_READ_BARCODES.value)
    
    # Check for errors
    if result.get_error_code() != EnumErrorCode.EC_OK:
        print(f"Error: {result.get_error_code()} - {result.get_error_string()}")
        return
    
    # Get barcode results
    barcode_result = result.get_decoded_barcodes_result()
    if barcode_result is None or len(barcode_result.get_items()) == 0:
        print("No barcode detected.")
        return
    
    # Display results
    items = barcode_result.get_items()
    print(f"\n✓ Decoded {len(items)} barcode(s):\n")
    for index, item in enumerate(items):
        print(f"Result {index + 1}:")
        print(f"  Format: {item.get_format_string()}")
        print(f"  Text: {item.get_text()}")
        print()


def scan_directory(directory_path):
    """
    Scan barcodes from all images in a directory
    
    Args:
        directory_path: Path to directory containing images
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return
    
    # Initialize license
    errorCode, errorMsg = LicenseManager.init_license("DLS2eyJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSJ9")
    if errorCode != EnumErrorCode.EC_OK and errorCode != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print(f"License initialization failed: ErrorCode: {errorCode}, ErrorString: {errorMsg}")
        return
    
    # Create CaptureVisionRouter instance
    cvr_instance = CaptureVisionRouter()
    
    # Set up DirectoryFetcher as input
    fetcher = DirectoryFetcher()
    fetcher.set_directory(directory_path)
    cvr_instance.set_input(fetcher)
    
    # Create result receiver
    class MyCapturedResultReceiver(CapturedResultReceiver):
        def __init__(self):
            super().__init__()
        
        def on_decoded_barcodes_received(self, result):
            tag = result.get_original_image_tag()
            if isinstance(tag, FileImageTag):
                print(f"\nFile: {tag.get_file_path()}")
            
            if result.get_error_code() != EnumErrorCode.EC_OK:
                print(f"Error: {result.get_error_string()}")
            else:
                items = result.get_items()
                if len(items) > 0:
                    print(f"Detected {len(items)} barcode(s):")
                    for index, item in enumerate(items):
                        print(f"  Result {index + 1}:")
                        print(f"    Format: {item.get_format_string()}")
                        print(f"    Text: {item.get_text()}")
                else:
                    print("No barcodes detected.")
    
    # Create image source state listener
    class MyImageSourceStateListener(ImageSourceStateListener):
        def __init__(self, cvr_instance):
            super().__init__()
            self.cvr_instance = cvr_instance
        
        def on_image_source_state_received(self, state):
            if state == EnumImageSourceState.ISS_EXHAUSTED:
                if self.cvr_instance is not None:
                    self.cvr_instance.stop_capturing()
    
    # Register listeners
    receiver = MyCapturedResultReceiver()
    cvr_instance.add_result_receiver(receiver)
    listener = MyImageSourceStateListener(cvr_instance)
    cvr_instance.add_image_source_state_listener(listener)
    
    # Start capturing
    print(f"Scanning barcodes from directory: {directory_path}\n")
    errorCode, errorMsg = cvr_instance.start_capturing("", True)
    if errorCode != EnumErrorCode.EC_OK:
        print(f"Error: {errorMsg}")
    else:
        print("\n✓ Directory scan completed.")


def print_usage():
    """Print usage information"""
    print("Command-line Barcode Scanner using Dynamsoft Barcode Reader SDK")
    print("\nUsage:")
    print("  python barcode_scanner.py <image_path>          # Scan a single image")
    print("  python barcode_scanner.py --dir <directory>     # Scan all images in a directory")
    print("\nExamples:")
    print("  python barcode_scanner.py barcode.jpg")
    print("  python barcode_scanner.py --dir ./images")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    if sys.argv[1] == "--dir":
        if len(sys.argv) < 3:
            print("Error: Directory path required.")
            print_usage()
            sys.exit(1)
        scan_directory(sys.argv[2])
    elif sys.argv[1] in ["-h", "--help"]:
        print_usage()
    else:
        scan_barcode(sys.argv[1])


if __name__ == "__main__":
    main()
