#!/usr/bin/env python3
"""
Test script for the barcode scanner

This script helps test the barcode scanner functionality and ensures
all dependencies are properly installed.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    
    print("Checking dependencies...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    else:
        print("✅ Python version is compatible")
    
    # Check required modules
    required_modules = [
        ('cv2', 'opencv-python'),
        ('dbr', 'dynamsoft-barcode-reader')
    ]
    
    missing_modules = []
    
    for module, package in required_modules:
        try:
            __import__(module)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            missing_modules.append(package)
    
    if missing_modules:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    
    return True

def test_help():
    """Test if the help command works."""
    
    print("\n" + "="*50)
    print("Testing help command...")
    print("="*50)
    
    try:
        result = subprocess.run([
            sys.executable, 'barcode_scanner.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Help command works")
            print("\nHelp output preview:")
            print("-" * 30)
            # Show first few lines of help
            lines = result.stdout.split('\n')[:10]
            for line in lines:
                print(line)
            print("...")
            return True
        else:
            print("❌ Help command failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running help command: {e}")
        return False

def create_sample_files():
    """Create sample files for testing."""
    
    print("\n" + "="*50)
    print("Creating sample files...")
    print("="*50)
    
    # Create sample folder structure
    sample_dir = Path("sample_images")
    sample_dir.mkdir(exist_ok=True)
    
    # Create a simple test script that generates a QR code
    test_qr_script = """
import qrcode
from PIL import Image
import os

def create_sample_qr_code():
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('Hello, Barcode Scanner!')
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save('sample_images/test_qr.png')
    print("Created test_qr.png")

if __name__ == "__main__":
    try:
        create_sample_qr_code()
    except ImportError:
        print("qrcode library not available. Install with: pip install qrcode[pil]")
        # Create a placeholder file instead
        with open('sample_images/placeholder.txt', 'w') as f:
            f.write("QR code image would be here if qrcode library was available\\n")
            f.write("Install with: pip install qrcode[pil]\\n")
        print("Created placeholder file instead")
"""
    
    # Save the QR code generator script
    with open("generate_test_qr.py", "w") as f:
        f.write(test_qr_script)
    
    print("✅ Created generate_test_qr.py")
    print("✅ Created sample_images directory")
    
    # Try to generate a test QR code
    try:
        result = subprocess.run([
            sys.executable, 'generate_test_qr.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Generated sample QR code")
        else:
            print("ℹ️  Could not generate sample QR code (qrcode library may not be available)")
    except Exception as e:
        print(f"ℹ️  Could not generate sample QR code: {e}")

def run_basic_tests():
    """Run basic functionality tests."""
    
    print("\n" + "="*50)
    print("Running basic tests...")
    print("="*50)
    
    # Test 1: Check if script runs without arguments (should show error)
    try:
        result = subprocess.run([
            sys.executable, 'barcode_scanner.py'
        ], capture_output=True, text=True, timeout=10)
        
        # Should fail because no arguments provided
        if result.returncode != 0:
            print("✅ Correctly shows error when no arguments provided")
        else:
            print("❌ Should show error when no arguments provided")
    except Exception as e:
        print(f"❌ Error testing argument handling: {e}")
    
    # Test 2: Test with non-existent image (should show error)
    try:
        result = subprocess.run([
            sys.executable, 'barcode_scanner.py', '--image', 'nonexistent.jpg'
        ], capture_output=True, text=True, timeout=10)
        
        if "not found" in result.stderr.lower() or "error" in result.stderr.lower():
            print("✅ Correctly handles non-existent image file")
        else:
            print("❌ Should show error for non-existent file")
    except Exception as e:
        print(f"❌ Error testing non-existent file: {e}")
    
    # Test 3: Test folder scanning with empty folder
    empty_dir = Path("empty_test_folder")
    empty_dir.mkdir(exist_ok=True)
    
    try:
        result = subprocess.run([
            sys.executable, 'barcode_scanner.py', '--folder', str(empty_dir)
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ Handles empty folder correctly")
        else:
            print(f"❌ Error with empty folder: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing empty folder: {e}")
    finally:
        # Clean up
        try:
            empty_dir.rmdir()
        except:
            pass

def main():
    """Main test function."""
    
    print("Barcode Scanner Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('barcode_scanner.py'):
        print("❌ barcode_scanner.py not found in current directory")
        print("Please run this test from the directory containing barcode_scanner.py")
        return 1
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Dependencies
    total_tests += 1
    if check_dependencies():
        tests_passed += 1
    
    # Test 2: Help command
    total_tests += 1
    if test_help():
        tests_passed += 1
    
    # Test 3: Create sample files
    create_sample_files()
    
    # Test 4: Basic functionality
    run_basic_tests()
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Tests completed: {total_tests}")
    print(f"Tests passed: {tests_passed}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The barcode scanner should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the installation and dependencies.")
    
    print("\nNext steps:")
    print("1. Install any missing dependencies shown above")
    print("2. Try scanning the generated test QR code:")
    print("   python barcode_scanner.py --image sample_images/test_qr.png")
    print("3. Test webcam functionality:")
    print("   python barcode_scanner.py --webcam")
    
    return 0 if tests_passed == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())