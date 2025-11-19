#!/usr/bin/env python3
"""
Example usage of the Barcode Scanner

This script demonstrates various ways to use the barcode scanner programmatically.
"""

import os
import sys
from pathlib import Path

# Import the scanner (assuming it's in the same directory)
try:
    from barcode_scanner import BarcodeScanner
except ImportError:
    print("Error: Could not import BarcodeScanner")
    print("Make sure barcode_scanner.py is in the same directory")
    sys.exit(1)

def example_scan_single_image():
    """Example: Scan a single image."""
    
    print("Example 1: Scanning a single image")
    print("-" * 40)
    
    # Initialize scanner
    scanner = BarcodeScanner()
    
    # Example image path (replace with your actual image)
    image_path = "sample_images/test_qr.png"
    
    if os.path.exists(image_path):
        try:
            results = scanner.scan_image(image_path)
            scanner.print_results(results, image_path)
        except Exception as e:
            print(f"Error scanning image: {e}")
    else:
        print(f"Image not found: {image_path}")
        print("Create a sample image first by running: python generate_test_qr.py")

def example_scan_folder():
    """Example: Scan all images in a folder."""
    
    print("\nExample 2: Scanning a folder")
    print("-" * 40)
    
    scanner = BarcodeScanner()
    
    folder_path = "sample_images"
    
    if os.path.exists(folder_path):
        try:
            results = scanner.scan_folder(folder_path, recursive=True)
            
            # Print summary
            total_files = len(results)
            files_with_barcodes = sum(1 for file_results in results.values() if file_results)
            total_barcodes = sum(len(file_results) for file_results in results.values())
            
            print(f"Scanned {total_files} files")
            print(f"Found barcodes in {files_with_barcodes} files")
            print(f"Total barcodes found: {total_barcodes}")
            
            # Show detailed results for files with barcodes
            for file_path, file_results in results.items():
                if file_results:
                    print(f"\nResults for {file_path}:")
                    for result in file_results:
                        print(f"  - {result['text']} ({result['format']})")
            
        except Exception as e:
            print(f"Error scanning folder: {e}")
    else:
        print(f"Folder not found: {folder_path}")
        print("Create sample images first")

def example_save_to_json():
    """Example: Save results to JSON file."""
    
    print("\nExample 3: Saving results to JSON")
    print("-" * 40)
    
    scanner = BarcodeScanner()
    
    # Scan sample_images folder if it exists
    folder_path = "sample_images"
    output_file = "example_results.json"
    
    if os.path.exists(folder_path):
        try:
            results = scanner.scan_folder(folder_path)
            scanner.save_results_json(results, output_file)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No sample images folder found")

def example_with_license():
    """Example: Using a license key."""
    
    print("\nExample 4: Using with license key")
    print("-" * 40)
    
    # Replace with your actual license key
    license_key = "YOUR_LICENSE_KEY_HERE"
    
    if license_key != "YOUR_LICENSE_KEY_HERE":
        try:
            scanner = BarcodeScanner(license_key=license_key)
            print("Scanner initialized with license key")
            
            # Use the licensed scanner
            # ... your scanning code here ...
            
        except Exception as e:
            print(f"Error with license: {e}")
    else:
        print("To use a license key, replace 'YOUR_LICENSE_KEY_HERE' with your actual key")
        print("Get a license from: https://www.dynamsoft.com/barcode-reader/")

def create_sample_data():
    """Create some sample data for testing."""
    
    print("Creating sample data for testing...")
    
    # Create sample images directory
    sample_dir = Path("sample_images")
    sample_dir.mkdir(exist_ok=True)
    
    # Try to create a sample QR code
    try:
        import qrcode
        from PIL import Image
        
        # Create a simple QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("Hello from Barcode Scanner Example!")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(sample_dir / "example_qr.png")
        print("✅ Created example_qr.png")
        
        # Create another QR code with URL
        qr2 = qrcode.QRCode(version=1, box_size=10, border=5)
        qr2.add_data("https://www.dynamsoft.com/barcode-reader/")
        qr2.make(fit=True)
        
        img2 = qr2.make_image(fill_color="black", back_color="white")
        img2.save(sample_dir / "url_qr.png")
        print("✅ Created url_qr.png")
        
    except ImportError:
        print("⚠️  qrcode library not available")
        print("Install with: pip install qrcode[pil]")
        
        # Create placeholder files
        with open(sample_dir / "readme.txt", "w") as f:
            f.write("Place your barcode images here for testing\\n")
            f.write("Supported formats: JPG, PNG, BMP, TIFF, GIF\\n")
        print("✅ Created readme.txt with instructions")

def main():
    """Run all examples."""
    
    print("Barcode Scanner Examples")
    print("=" * 50)
    
    # Create sample data if needed
    create_sample_data()
    
    # Run examples
    example_scan_single_image()
    example_scan_folder()
    example_save_to_json()
    example_with_license()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("=" * 50)
    
    print("\nTry these command-line examples:")
    print("python barcode_scanner.py --help")
    print("python barcode_scanner.py --image sample_images/example_qr.png")
    print("python barcode_scanner.py --folder sample_images --output results.json")
    print("python barcode_scanner.py --webcam")

if __name__ == "__main__":
    main()