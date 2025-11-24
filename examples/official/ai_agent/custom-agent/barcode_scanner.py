#!/usr/bin/env python3
"""
Command-line barcode scanner using Dynamsoft Barcode Reader SDK.

This script scans barcodes from image files or directories containing images.
It supports various barcode formats including QR codes, Code 128, EAN-13, PDF417, and more.

Usage:
    python barcode_scanner.py <image_path>
    python barcode_scanner.py <directory_path> --batch
    python barcode_scanner.py <image_path> --format QR_CODE
    python barcode_scanner.py <image_path> --verbose
"""

import argparse
import os
import sys
from pathlib import Path
from dynamsoft_barcode_reader_bundle import (
    LicenseManager, 
    CaptureVisionRouter, 
    EnumErrorCode, 
    EnumPresetTemplate
)


def setup_license():
    """Initialize the Dynamsoft license."""
    # Public trial license (requires internet connection)
    # For offline use, get a 30-day trial from: https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
    license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
    
    error_code, error_msg = LicenseManager.init_license(license_key)
    if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
        print(f"❌ License initialization failed: {error_msg}")
        print("💡 Get a free trial license: https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform")
        return False
    return True


def scan_single_image(image_path, verbose=False, target_format=None):
    """
    Scan barcodes from a single image file.
    
    Args:
        image_path (str): Path to the image file
        verbose (bool): Whether to show detailed output
        target_format (str): Specific barcode format to look for (optional)
    
    Returns:
        list: List of detected barcode results
    """
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found at '{image_path}'")
        return []

    try:
        # Create CaptureVisionRouter instance
        cvr_instance = CaptureVisionRouter()
        
        if verbose:
            print(f"🔍 Scanning '{image_path}'...")

        # Capture barcodes from image
        result = cvr_instance.capture(image_path, EnumPresetTemplate.PT_READ_BARCODES.value)

        # Check for errors
        if result.get_error_code() != EnumErrorCode.EC_OK:
            print(f"❌ Error scanning image: {result.get_error_string()}")
            return []

        # Get barcode results
        barcode_results = result.get_decoded_barcodes_result()
        if barcode_results is None or not barcode_results.get_items():
            if verbose:
                print("ℹ️  No barcodes detected.")
            return []

        items = barcode_results.get_items()
        
        # Filter by format if specified
        if target_format:
            items = [item for item in items if item.get_format_string() == target_format]
            if not items and verbose:
                print(f"ℹ️  No barcodes found matching format '{target_format}'.")
                return []

        # Display results
        if verbose:
            print(f"✅ Found {len(items)} barcode(s):")
        
        results = []
        for index, item in enumerate(items):
            result_data = {
                'format': item.get_format_string(),
                'text': item.get_text(),
                'confidence': getattr(item, 'get_confidence', lambda: None)() or 'N/A'
            }
            results.append(result_data)
            
            if verbose:
                print(f"  [{index + 1}]")
                print(f"    Format: {result_data['format']}")
                print(f"    Text:   {result_data['text']}")
                if result_data['confidence'] != 'N/A':
                    print(f"    Confidence: {result_data['confidence']}")
            else:
                print(f"{result_data['format']}: {result_data['text']}")

        return results

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return []


def scan_directory(directory_path, verbose=False, target_format=None):
    """
    Scan all images in a directory for barcodes.
    
    Args:
        directory_path (str): Path to directory containing images
        verbose (bool): Whether to show detailed output
        target_format (str): Specific barcode format to look for (optional)
    
    Returns:
        dict: Dictionary mapping file paths to their barcode results
    """
    if not os.path.isdir(directory_path):
        print(f"❌ Error: Directory not found at '{directory_path}'")
        return {}

    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
    
    # Find all image files
    image_files = []
    for file_path in Path(directory_path).rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(str(file_path))

    if not image_files:
        print(f"ℹ️  No image files found in '{directory_path}'")
        return {}

    print(f"🔍 Scanning {len(image_files)} image(s) in '{directory_path}'...")
    
    all_results = {}
    total_barcodes = 0

    for image_file in sorted(image_files):
        if verbose:
            print(f"\n📁 Processing: {os.path.basename(image_file)}")
        
        results = scan_single_image(image_file, verbose=False, target_format=target_format)
        if results:
            all_results[image_file] = results
            total_barcodes += len(results)
            
            if not verbose:
                print(f"📁 {os.path.basename(image_file)}: {len(results)} barcode(s)")
                for result in results:
                    print(f"   {result['format']}: {result['text']}")

    print(f"\n✅ Batch scan complete: {total_barcodes} total barcode(s) found in {len(all_results)} file(s)")
    return all_results


def main():
    """Main entry point for the barcode scanner."""
    parser = argparse.ArgumentParser(
        description="Scan barcodes from images using Dynamsoft Barcode Reader",
        epilog="Examples:\n"
               "  python barcode_scanner.py image.jpg\n"
               "  python barcode_scanner.py /path/to/images --batch\n"
               "  python barcode_scanner.py qr.png --format QR_CODE --verbose",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('path', help='Path to image file or directory')
    parser.add_argument('--batch', action='store_true', 
                       help='Process all images in the specified directory')
    parser.add_argument('--format', choices=[
        'QR_CODE', 'CODE_128', 'CODE_39', 'EAN_13', 'EAN_8', 'UPC_A', 'UPC_E',
        'CODABAR', 'ITF', 'PDF417', 'DATAMATRIX', 'AZTEC', 'MAXICODE'
    ], help='Filter results by specific barcode format')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()

    # Display header
    print("=" * 60)
    print("🔍 Dynamsoft Barcode Reader - Command Line Scanner")
    print("=" * 60)

    # Initialize license
    if not setup_license():
        sys.exit(1)

    # Determine scan mode
    if args.batch or os.path.isdir(args.path):
        if os.path.isfile(args.path):
            print("❌ Error: --batch flag specified but path is a file")
            sys.exit(1)
        scan_directory(args.path, args.verbose, args.format)
    else:
        scan_single_image(args.path, args.verbose, args.format)

    print("\n🎯 Scan complete!")


if __name__ == "__main__":
    main()