#!/usr/bin/env python3
"""
Command Line Barcode Scanner using Dynamsoft Barcode Reader SDK

This script provides a command-line interface for scanning barcodes from images
using the Dynamsoft Barcode Reader SDK.

Usage:
    python barcode_scanner.py --image path/to/image.jpg
    python barcode_scanner.py --webcam
    python barcode_scanner.py --folder path/to/folder/
"""

import argparse
import os
import sys
import cv2
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import dbr
    from dbr import BarcodeReader, BarcodeReaderError
except ImportError:
    print("Error: Dynamsoft Barcode Reader SDK not found.")
    print("Please install it using: pip install dynamsoft-barcode-reader")
    sys.exit(1)


class BarcodeScanner:
    """A command-line barcode scanner using Dynamsoft Barcode Reader SDK."""
    
    def __init__(self, license_key: Optional[str] = None):
        """
        Initialize the barcode scanner.
        
        Args:
            license_key: Dynamsoft license key (optional, will use trial if not provided)
        """
        self.reader = BarcodeReader()
        
        # Set license key if provided
        if license_key:
            dbr.BarcodeReader.init_license(license_key)
        else:
            # Use trial license
            print("Using trial license. For production use, please set your license key.")
    
    def scan_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Scan barcodes from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing barcode information
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Read barcodes from image
            text_results = self.reader.decode_file(image_path)
            
            results = []
            if text_results:
                for result in text_results:
                    barcode_info = {
                        'text': result.barcode_text,
                        'format': result.barcode_format_string,
                        'confidence': result.localization_result.confidence,
                        'location': {
                            'points': result.localization_result.localization_points
                        }
                    }
                    results.append(barcode_info)
            
            return results
            
        except Exception as e:
            print(f"Error scanning image {image_path}: {e}")
            return []
    
    def scan_webcam(self, camera_index: int = 0) -> None:
        """
        Scan barcodes from webcam feed.
        
        Args:
            camera_index: Index of the camera to use (default: 0)
        """
        print(f"Starting webcam scanner (camera {camera_index})...")
        print("Press 'q' to quit, 's' to save current frame, 'c' to capture and scan")
        
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            return
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Display frame
                cv2.imshow('Barcode Scanner - Press "c" to scan, "q" to quit', frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    print("Scanning current frame...")
                    # Save temporary frame for scanning
                    temp_path = "temp_frame.jpg"
                    cv2.imwrite(temp_path, frame)
                    
                    # Scan the frame
                    results = self.scan_image(temp_path)
                    
                    if results:
                        print(f"Found {len(results)} barcode(s):")
                        for i, result in enumerate(results, 1):
                            print(f"  {i}. {result['text']} ({result['format']})")
                    else:
                        print("No barcodes found in current frame")
                    
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                
                elif key == ord('s'):
                    # Save current frame
                    filename = f"captured_frame_{frame_count:04d}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Frame saved as {filename}")
                    frame_count += 1
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def scan_folder(self, folder_path: str, recursive: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan all images in a folder for barcodes.
        
        Args:
            folder_path: Path to the folder containing images
            recursive: Whether to scan subfolders recursively
            
        Returns:
            Dictionary mapping file paths to barcode results
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
        
        results = {}
        folder = Path(folder_path)
        
        # Get image files
        if recursive:
            image_files = [f for f in folder.rglob('*') if f.suffix.lower() in image_extensions]
        else:
            image_files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]
        
        print(f"Scanning {len(image_files)} image(s) in {folder_path}...")
        
        for image_file in image_files:
            print(f"Scanning: {image_file}")
            file_results = self.scan_image(str(image_file))
            results[str(image_file)] = file_results
            
            if file_results:
                print(f"  Found {len(file_results)} barcode(s)")
                for result in file_results:
                    print(f"    - {result['text']} ({result['format']})")
            else:
                print("  No barcodes found")
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]], file_path: Optional[str] = None) -> None:
        """
        Print barcode scan results in a formatted way.
        
        Args:
            results: List of barcode results
            file_path: Optional file path for context
        """
        if file_path:
            print(f"\nResults for: {file_path}")
            print("-" * 50)
        
        if not results:
            print("No barcodes found.")
            return
        
        print(f"Found {len(results)} barcode(s):")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"Barcode #{i}:")
            print(f"  Text: {result['text']}")
            print(f"  Format: {result['format']}")
            print(f"  Confidence: {result['confidence']}")
            
            # Print location points if available
            if 'location' in result and 'points' in result['location']:
                points = result['location']['points']
                print(f"  Location: {points}")
            print()
    
    def save_results_json(self, results: Dict[str, Any], output_file: str) -> None:
        """
        Save scan results to a JSON file.
        
        Args:
            results: Results dictionary to save
            output_file: Path to output JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """Main function to handle command line arguments and run the scanner."""
    
    parser = argparse.ArgumentParser(
        description="Command Line Barcode Scanner using Dynamsoft Barcode Reader SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python barcode_scanner.py --image sample.jpg
  python barcode_scanner.py --webcam
  python barcode_scanner.py --folder images/
  python barcode_scanner.py --image sample.jpg --output results.json
  python barcode_scanner.py --folder images/ --recursive --output scan_results.json
        """
    )
    
    # Main operation modes (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--image', '-i', 
                      help='Scan a single image file')
    group.add_argument('--webcam', '-w', action='store_true',
                      help='Scan from webcam feed')
    group.add_argument('--folder', '-f',
                      help='Scan all images in a folder')
    
    # Optional arguments
    parser.add_argument('--license', '-l',
                       help='Dynamsoft license key')
    parser.add_argument('--output', '-o',
                       help='Output JSON file to save results')
    parser.add_argument('--camera', '-c', type=int, default=0,
                       help='Camera index for webcam mode (default: 0)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Scan folder recursively (only with --folder)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Initialize scanner
    try:
        scanner = BarcodeScanner(license_key=args.license)
    except Exception as e:
        print(f"Error initializing scanner: {e}")
        return 1
    
    try:
        if args.image:
            # Scan single image
            print(f"Scanning image: {args.image}")
            results = scanner.scan_image(args.image)
            scanner.print_results(results, args.image)
            
            if args.output:
                output_data = {args.image: results}
                scanner.save_results_json(output_data, args.output)
        
        elif args.webcam:
            # Scan from webcam
            scanner.scan_webcam(args.camera)
        
        elif args.folder:
            # Scan folder
            results = scanner.scan_folder(args.folder, args.recursive)
            
            # Print summary
            total_barcodes = sum(len(file_results) for file_results in results.values())
            files_with_barcodes = sum(1 for file_results in results.values() if file_results)
            
            print(f"\nScan Summary:")
            print(f"Total files scanned: {len(results)}")
            print(f"Files with barcodes: {files_with_barcodes}")
            print(f"Total barcodes found: {total_barcodes}")
            
            if args.verbose:
                print("\nDetailed Results:")
                for file_path, file_results in results.items():
                    if file_results:
                        scanner.print_results(file_results, file_path)
            
            if args.output:
                scanner.save_results_json(results, args.output)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())