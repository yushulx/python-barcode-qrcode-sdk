"""
Test Data Generator
This module generates synthetic test images with barcodes at various angles and configurations.
"""

import os
import random
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple
from pathlib import Path
import barcode
from barcode import Code128, Code39, EAN13, EAN8, ITF
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import qrcode


class BarcodeGenerator:
    """Generate individual barcode images."""
    
    def __init__(self, output_dir: str = "generated_barcodes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Barcode generators mapping
        self.generators = {
            'CODE128': Code128,
            'CODE39': Code39,
            'EAN13': EAN13,
            'EAN8': EAN8,
            'ITF': ITF,
            'CODABAR': None,  # Not supported in python-barcode
            'QR_CODE': qrcode,  # QR code supported
            'DATA_MATRIX': None,  # Would need pytmx library
            'PDF_417': None,  # Would need pdf417gen library
            'AZTEC': None,  # Would need aztec library
        }
    
    def generate_barcode(self, data: str, barcode_type: str = 'CODE128', 
                        width: int = 300, height: int = 150) -> str:
        """
        Generate a single barcode image with proper data format.
        
        Args:
            data: The data to encode in the barcode
            barcode_type: Type of barcode to generate
            width: Width of the generated barcode
            height: Height of the generated barcode
            
        Returns:
            Path to the generated barcode image
        """
        if barcode_type not in self.generators:
            raise ValueError(f"Unsupported barcode type: {barcode_type}")
        
        if self.generators[barcode_type] is None:
            # For unsupported types, create a placeholder
            return self._create_placeholder_barcode(data, barcode_type, width, height)
        
        # Handle QR code separately
        if barcode_type == 'QR_CODE':
            return self._generate_qr_code(data, width, height)
        
        try:
            # Format data according to barcode type
            if barcode_type == 'EAN13':
                # EAN13 requires exactly 12 digits - it calculates the 13th check digit
                numeric_data = ''.join(filter(str.isdigit, data))[:12].ljust(12, '0')
                data = numeric_data
            elif barcode_type == 'EAN8':
                # EAN8 requires exactly 7 digits - it calculates the 8th check digit  
                numeric_data = ''.join(filter(str.isdigit, data))[:7].ljust(7, '0')
                data = numeric_data
            elif barcode_type == 'ITF':
                # ITF requires even number of digits
                numeric_data = ''.join(filter(str.isdigit, data))[:14].ljust(14, '0')
                data = numeric_data
            elif barcode_type in ['CODE39', 'CODE128']:
                # Ensure valid alphanumeric format
                data = ''.join(c for c in data if c.isalnum() or c in ['-', '$', '%', '+', '/', '.', ' '])[:15]
            
            barcode_class = self.generators[barcode_type]
            writer = ImageWriter()
            writer.set_options({
                'module_width': width / (len(data) * 10),  # Approximate module width
                'module_height': height,
                'quiet_zone': 6.5,
                'font_size': 10,
                'text_distance': 5.0,
                'background': 'white',
                'foreground': 'black'
            })
            
            # Generate barcode
            barcode_instance = barcode_class(data, writer=writer)
            filename = f"{barcode_type}_{data.replace('/', '_')}_{random.randint(1000, 9999)}.png"
            filepath = self.output_dir / filename
            
            barcode_instance.write(str(filepath))
            return str(filepath)
            
        except Exception as e:
            print(f"Error generating {barcode_type} barcode: {e}")
            print(f"Attempting with data: '{data}'")
            return self._create_placeholder_barcode(data, barcode_type, width, height)
    
    def _generate_qr_code(self, data: str, width: int, height: int) -> str:
        """Generate QR code image - always square."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # QR codes must be square - use max dimension to ensure quality
        size = max(width, height)
        img = img.resize((size, size), Image.LANCZOS)
        
        filename = f"QR_CODE_{data.replace('/', '_')}_{random.randint(1000, 9999)}.png"
        filepath = self.output_dir / filename
        img.save(str(filepath))
        return str(filepath)
    
    def _create_placeholder_barcode(self, data: str, barcode_type: str, 
                                  width: int, height: int) -> str:
        """Create a placeholder barcode image for unsupported types."""
        # Create a simple barcode-like image (grayscale for compatibility)
        import cv2
        image = np.ones((height, width), dtype=np.uint8) * 255  # White background
        
        # Draw barcode-like pattern
        num_lines = len(data) * 3
        line_width = width // num_lines if num_lines > 0 else width // 10
        
        for i in range(0, width, line_width * 2):
            color = 0 if (i // (line_width * 2)) % 2 == 0 else 255  # Black/white
            end_x = min(i + line_width, width)
            image[0:height, i:end_x] = color
        
        # Add text (basic implementation)
        # For simplicity, we'll just save the barcode pattern
        
        filename = f"{barcode_type}_{data.replace('/', '_')}_placeholder.png"
        filepath = self.output_dir / filename
        cv2.imwrite(str(filepath), image)
        return str(filepath)


class TestDataGenerator:
    """Generate comprehensive test datasets for barcode benchmarking."""
    
    def __init__(self, output_dir: str = "generated_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Use temp directory for barcode generation (will be cleaned up)
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.barcode_generator = BarcodeGenerator(self.temp_dir)
        
        # Test categories
        self.categories = {
            'single_barcode': self.output_dir / "single_barcode",
            'angled_barcodes': self.output_dir / "angled_barcodes", 
            'multiple_barcodes': self.output_dir / "multiple_barcodes",
            'challenging_conditions': self.output_dir / "challenging_conditions"
        }
        
        for category_dir in self.categories.values():
            category_dir.mkdir(exist_ok=True)
    
    def generate_test_dataset(self, num_samples: int = 50, distribution: Dict[str, float] = None) -> Dict[str, int]:
        """Generate a complete test dataset with various scenarios.
        
        Args:
            num_samples: Total number of images desired.
            distribution: Optional ratio distribution across categories. Keys:
                'single', 'angled', 'multiple', 'challenging'. Values are floats summing ~1.0.
                If None, defaults to {'single':0.4,'angled':0.3,'multiple':0.2,'challenging':0.1}.
        Returns:
            Dictionary of actual counts generated per category.
        """
        if num_samples <= 0:
            print("No samples requested; nothing to generate.")
            return {k: 0 for k in ['single','angled','multiple','challenging']}

        if distribution is None:
            distribution = {'single':0.4,'angled':0.3,'multiple':0.2,'challenging':0.1}
        # Normalize distribution if it doesn't sum to 1.
        total_ratio = sum(distribution.values())
        if total_ratio <= 0:
            distribution = {'single':0.4,'angled':0.3,'multiple':0.2,'challenging':0.1}
            total_ratio = 1.0
        normalized = {k: v/total_ratio for k,v in distribution.items()}

        # Compute counts (allocate remainder to 'challenging').
        single_count = int(num_samples * normalized.get('single',0))
        angled_count = int(num_samples * normalized.get('angled',0))
        multiple_count = int(num_samples * normalized.get('multiple',0))
        allocated = single_count + angled_count + multiple_count
        challenging_count = max(0, num_samples - allocated)

        print("Generating comprehensive test dataset...")
        print(f"Requested total: {num_samples}")
        print(f"Distribution (normalized): {normalized}")
        print(f"Planned counts -> single: {single_count}, angled: {angled_count}, multiple: {multiple_count}, challenging: {challenging_count}")

        self._generate_single_barcodes(single_count)
        self._generate_angled_barcodes(angled_count)
        self._generate_multiple_barcodes(multiple_count)
        self._generate_challenging_conditions(challenging_count)

        actual = {
            'single': single_count,
            'angled': angled_count,
            'multiple': multiple_count,
            'challenging': challenging_count
        }
        total_actual = sum(actual.values())
        print(f"Test dataset generated in: {self.output_dir} (total images: {total_actual})")
        if total_actual != num_samples:
            print(f"Note: Total ({total_actual}) differs from requested ({num_samples}) due to integer rounding of distribution ratios.")
        return actual
    
    def _generate_single_barcodes(self, count: int):
        """Generate single barcode images with various types."""
        print(f"Generating {count} single barcode images...")
        
        barcode_types = ['CODE128', 'CODE39', 'EAN13', 'EAN8', 'ITF', 'QR_CODE']
        
        for i in range(count):
            barcode_type = barcode_types[i % len(barcode_types)]
            
            # Generate proper data for each barcode type
            if barcode_type == 'EAN13':
                # EAN13 uses 12 digits + 1 check digit (auto-calculated)
                data = f"{123456789012 + i:012d}"
            elif barcode_type == 'EAN8':
                # EAN8 uses 7 digits + 1 check digit (auto-calculated)
                data = f"{1234567 + i:07d}"
            elif barcode_type == 'ITF':
                data = f"{12345678901234 + i:014d}"
            elif barcode_type == 'CODE39':
                data = f"CODE{i:04d}"
            elif barcode_type == 'QR_CODE':
                data = f"https://example.com/qr/{i:06d}"
            else:  # CODE128
                data = f"BARCODE{i:06d}"
            
            try:
                # Generate barcode (QR codes get square dimensions)
                if barcode_type == 'QR_CODE':
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type, width=300, height=300)
                else:
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type)
                
                # Create test image
                image = self._create_single_barcode_test_image(barcode_path, barcode_type, data)
                
                # Save test image
                filename = f"single_{i:03d}_{barcode_type}.png"
                filepath = self.categories['single_barcode'] / filename
                cv2.imwrite(str(filepath), image)
                
                # Create metadata file
                metadata = {
                    'test_id': f"single_{i:03d}",
                    'image_path': str(filepath),
                    'barcode_data': [data],
                    'barcode_types': [barcode_type],
                    'rotation_angle': 0,
                    'barcode_count': 1,
                    'test_type': 'single',
                    'difficulty': 'easy'
                }
                with open(filepath.with_suffix('.json'), 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error generating single barcode {i}: {e}")
                continue
    
    def _generate_angled_barcodes(self, count: int):
        """Generate barcode images at various rotation angles - KEY FOCUS."""
        print(f"Generating {count} angled barcode images...")
        
        barcode_types = ['CODE128', 'CODE39', 'EAN13', 'QR_CODE']  # Added QR_CODE
        angles = [15, 30, 45, 60, 75]  # Various rotation angles
        
        for i in range(count):
            barcode_type = barcode_types[i % len(barcode_types)]
            angle = angles[i % len(angles)]
            
            # Generate proper data for each barcode type
            if barcode_type == 'EAN13':
                # EAN13 uses 12 digits + 1 check digit (auto-calculated)
                data = f"{200000000000 + i:012d}"
            elif barcode_type == 'CODE39':
                data = f"ANGLED{i:03d}"
            elif barcode_type == 'QR_CODE':
                data = f"https://example.com/angled/{angle}/{i:04d}"
            else:  # CODE128
                data = f"ANGLE{angle:02d}{i:04d}"
            
            try:
                # Generate barcode (QR codes get square dimensions)
                if barcode_type == 'QR_CODE':
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type, width=300, height=300)
                else:
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type)
                
                # Create test image with rotation
                image = self._create_angled_barcode_test_image(barcode_path, barcode_type, data, angle)
                
                # Save test image
                filename = f"angled_{i:03d}_angle{angle}.png"
                filepath = self.categories['angled_barcodes'] / filename
                cv2.imwrite(str(filepath), image)
                
                # Create metadata file
                metadata = {
                    'test_id': f"angled_{i:03d}",
                    'image_path': str(filepath),
                    'barcode_data': [data],
                    'barcode_types': [barcode_type],
                    'rotation_angle': angle,
                    'barcode_count': 1,
                    'test_type': 'angled',
                    'difficulty': 'medium',
                    'focus_area': 'angled_barcode_performance'
                }
                with open(filepath.with_suffix('.json'), 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error generating angled barcode {i}: {e}")
                continue
    
    def _generate_multiple_barcodes(self, count: int):
        """Generate images with multiple barcodes - KEY FOCUS."""
        print(f"Generating {count} multiple barcode images...")
        
        barcode_types = ['CODE128', 'CODE39', 'EAN13', 'EAN8', 'QR_CODE']
        barcode_counts = [2, 5, 10, 15]  # Various numbers of barcodes
        
        for i in range(count):
            num_barcodes = barcode_counts[i % len(barcode_counts)]
            
            # Generate multiple barcodes
            barcode_data = []
            barcode_files = []
            barcode_types_list = []
            
            for j in range(num_barcodes):
                barcode_type = barcode_types[j % len(barcode_types)]
                barcode_types_list.append(barcode_type)
                
                # Generate proper data for each barcode type (avoid underscores)
                if barcode_type == 'EAN13':
                    # EAN13 uses 12 digits + 1 check digit (auto-calculated)
                    data = f"{300000000000 + (i * 100 + j):012d}"
                elif barcode_type == 'EAN8':
                    # EAN8 uses 7 digits + 1 check digit (auto-calculated)
                    data = f"{3000000 + (i * 100 + j):07d}"
                elif barcode_type == 'CODE39':
                    data = f"MULTI{i:02d}{j:02d}"
                elif barcode_type == 'QR_CODE':
                    data = f"https://example.com/multi/{i:03d}/{j:02d}"
                else:  # CODE128
                    data = f"MULTI{i:03d}{j:02d}"
                
                barcode_data.append(data)
                
                try:
                    # Generate individual barcode (QR codes get square dimensions)
                    if barcode_type == 'QR_CODE':
                        barcode_path = self.barcode_generator.generate_barcode(data, barcode_type, width=250, height=250)
                    else:
                        barcode_path = self.barcode_generator.generate_barcode(data, barcode_type)
                    barcode_files.append(barcode_path)
                except Exception as e:
                    print(f"Error generating barcode {j} for multiple test {i}: {e}")
                    continue
            
            if len(barcode_files) == 0:
                print(f"Skipping multiple test {i} due to barcode generation errors")
                continue
            
            try:
                # Create test image with multiple barcodes
                image = self._create_multiple_barcode_test_image(barcode_files, barcode_data, len(barcode_files))
                
                # Save test image
                filename = f"multiple_{i:03d}_count{len(barcode_files)}.png"
                filepath = self.categories['multiple_barcodes'] / filename
                cv2.imwrite(str(filepath), image)
                
                # Create metadata file
                metadata = {
                    'test_id': f"multiple_{i:03d}",
                    'image_path': str(filepath),
                    'barcode_data': barcode_data[:len(barcode_files)],
                    'barcode_types': barcode_types_list[:len(barcode_files)],
                    'rotation_angle': 0,
                    'test_type': 'multiple',
                    'difficulty': 'hard',
                    'barcode_count': len(barcode_files),
                    'focus_area': 'multiple_barcode_performance'
                }
                with open(filepath.with_suffix('.json'), 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error creating multiple barcode test image {i}: {e}")
                continue
    
    def _generate_challenging_conditions(self, count: int):
        """Generate images with challenging conditions (noise, low contrast, etc.)."""
        print(f"Generating {count} challenging condition images...")
        if count <= 0:
            return

        # Base barcode types to start from (1D heavy + occasional 2D placeholder)
        base_types = ['CODE128', 'CODE39', 'EAN13', 'EAN8', 'ITF', 'QR_CODE']
        degradations_available = [
            'gaussian_noise', 'salt_pepper_noise', 'motion_blur', 'gaussian_blur',
            'low_contrast', 'low_brightness', 'high_brightness', 'occlusion',
            'perspective_warp', 'low_resolution', 'partial_cutoff', 'background_clutter',
            'color_inversion', 'channel_dropout', 'shadows', 'reflections', 'torn_edges'
        ]

        for i in range(count):
            barcode_type = base_types[i % len(base_types)]
            # Create base data
            if barcode_type == 'EAN13':
                data = f"{9000000000000 + i:013d}"
            elif barcode_type == 'EAN8':
                data = f"{90000000 + i:08d}"
            elif barcode_type == 'ITF':
                data = f"{90000000000000 + i:014d}"
            elif barcode_type == 'CODE39':
                data = f"CHAL{i:04d}"
            elif barcode_type == 'QR_CODE':
                data = f"https://example.com/challenging/{i:05d}"
            else:  # CODE128
                data = f"CHALLENGE{i:05d}"

            try:
                # Generate barcode (QR codes get square dimensions)
                if barcode_type == 'QR_CODE':
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type, width=300, height=300)
                else:
                    barcode_path = self.barcode_generator.generate_barcode(data, barcode_type)
                base_img = cv2.imread(barcode_path)
                if base_img is None:
                    # Fallback blank
                    base_img = np.ones((150, 300, 3), dtype=np.uint8) * 255
                elif len(base_img.shape) == 2:
                    base_img = cv2.cvtColor(base_img, cv2.COLOR_GRAY2BGR)

                # Put barcode on neutral canvas first
                canvas_h, canvas_w = 800, 600
                canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 240
                bh, bw = base_img.shape[:2]
                scale = min((canvas_w*0.6)/bw, (canvas_h*0.6)/bh)
                resized = cv2.resize(base_img, (int(bw*scale), int(bh*scale)))
                rh, rw = resized.shape[:2]
                cx = (canvas_w - rw)//2
                cy = (canvas_h - rh)//2
                canvas[cy:cy+rh, cx:cx+rw] = resized

                # Decide severity level to keep barcodes visible but challenging
                severe = random.random() < 0.3  # 30% chance of more severe scenario
                if severe:
                    num_degrades = random.randint(3,5)
                else:
                    num_degrades = random.randint(2,3)
                chosen = random.sample(degradations_available, num_degrades)
                degraded = canvas.copy()
                metadata_degrades = {}

                for degr in chosen:
                    if degr == 'gaussian_noise':
                        std = random.uniform(10 if severe else 5, 25 if severe else 15)
                        noise = np.random.normal(0, std, degraded.shape).astype(np.float32)
                        degraded = np.clip(degraded.astype(np.float32) + noise, 0, 255).astype(np.uint8)
                        metadata_degrades[degr] = {'std': round(std,2)}
                    elif degr == 'salt_pepper_noise':
                        amount = random.uniform(0.01 if severe else 0.005, 0.05 if severe else 0.02)
                        sp_img = degraded.copy()
                        num_pixels = int(amount * degraded.shape[0] * degraded.shape[1])
                        # Salt
                        coords = (np.random.randint(0, degraded.shape[0], num_pixels),
                                  np.random.randint(0, degraded.shape[1], num_pixels))
                        sp_img[coords] = 255
                        # Pepper
                        coords = (np.random.randint(0, degraded.shape[0], num_pixels),
                                  np.random.randint(0, degraded.shape[1], num_pixels))
                        sp_img[coords] = 0
                        degraded = sp_img
                        metadata_degrades[degr] = {'amount': round(amount,3)}
                    elif degr == 'motion_blur':
                        k_choices = [5,7,9,11,13,15]
                        k = random.choice(k_choices[2:] if severe else k_choices[:3])
                        kernel = np.zeros((k, k), dtype=np.float32)
                        direction = random.choice(['horizontal','vertical','diag_down','diag_up'])
                        if direction == 'horizontal':
                            kernel[k//2,:] = 1.0 / k
                        else:
                            if direction == 'vertical':
                                kernel[:,k//2] = 1.0 / k
                            elif direction == 'diag_down':
                                for d_i in range(k):
                                    kernel[d_i,d_i] = 1.0 / k
                            else:  # diag_up
                                for d_i in range(k):
                                    kernel[d_i,k-1-d_i] = 1.0 / k
                        degraded = cv2.filter2D(degraded, -1, kernel)
                        metadata_degrades[degr] = {'kernel_size': k, 'direction': direction}
                    elif degr == 'gaussian_blur':
                        k = random.choice([5,7,9,11] if severe else [3,5,7])
                        degraded = cv2.GaussianBlur(degraded, (k,k), 0)
                        metadata_degrades[degr] = {'kernel_size': k}
                    elif degr == 'low_contrast':
                        alpha = random.uniform(0.5 if severe else 0.6, 0.7 if severe else 0.8)
                        beta = random.uniform(-20 if severe else -10, 10 if severe else 20)
                        degraded = cv2.convertScaleAbs(degraded, alpha=alpha, beta=beta)
                        metadata_degrades[degr] = {'alpha': round(alpha,2), 'beta': round(beta,2)}
                    elif degr == 'low_brightness':
                        beta = random.uniform(-60 if severe else -40, -30 if severe else -20)
                        degraded = cv2.convertScaleAbs(degraded, alpha=1.0, beta=beta)
                        metadata_degrades[degr] = {'beta': round(beta,2)}
                    elif degr == 'high_brightness':
                        beta = random.uniform(30 if severe else 20, 60 if severe else 40)
                        degraded = cv2.convertScaleAbs(degraded, alpha=1.0, beta=beta)
                        metadata_degrades[degr] = {'beta': round(beta,2)}
                    elif degr == 'occlusion':
                        occ_w = random.randint(int(rw*0.15) if severe else int(rw*0.1), int(rw*0.35) if severe else int(rw*0.25))
                        occ_h = random.randint(int(rh*0.15) if severe else int(rh*0.1), int(rh*0.35) if severe else int(rh*0.25))
                        ox = random.randint(cx, cx+rw-occ_w)
                        oy = random.randint(cy, cy+rh-occ_h)
                        color = random.randint(0,255)
                        degraded[oy:oy+occ_h, ox:ox+occ_w] = color
                        metadata_degrades[degr] = {'rect': [ox, oy, occ_w, occ_h], 'color': color}
                    elif degr == 'perspective_warp':
                        h, w = degraded.shape[:2]
                        margin = 60 if severe else 80
                        pts1 = np.float32([[margin,margin],[w-margin,margin],[margin,h-margin],[w-margin,h-margin]])
                        pts2 = pts1 + np.random.randint(-40 if severe else -20, 40 if severe else 20, pts1.shape).astype(np.float32)
                        M = cv2.getPerspectiveTransform(pts1, pts2)
                        degraded = cv2.warpPerspective(degraded, M, (w,h), borderMode=cv2.BORDER_REPLICATE)
                        metadata_degrades[degr] = {'distortion': True}
                    elif degr == 'low_resolution':
                        h, w = degraded.shape[:2]
                        scale = random.uniform(0.4 if severe else 0.5, 0.6 if severe else 0.7)
                        small = cv2.resize(degraded, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
                        degraded = cv2.resize(small, (w,h), interpolation=cv2.INTER_NEAREST)
                        metadata_degrades[degr] = {'scale_down': round(scale,2)}
                    elif degr == 'partial_cutoff':
                        h, w = degraded.shape[:2]
                        side = random.choice(['top','bottom','left','right'])
                        frac = random.uniform(0.08 if severe else 0.05, 0.18 if severe else 0.12)
                        if side == 'top':
                            degraded[0:int(h*frac),:] = 240
                        elif side == 'bottom':
                            degraded[int(h*(1-frac)):h,:] = 240
                        elif side == 'left':
                            degraded[:,0:int(w*frac)] = 240
                        else:
                            degraded[:,int(w*(1-frac)):w] = 240
                        metadata_degrades[degr] = {'side': side, 'fraction': round(frac,3)}
                    elif degr == 'background_clutter':
                        # Add random colored rectangles behind barcode area
                        clutter_img = degraded.copy()
                        for _ in range(random.randint(5 if severe else 3,10 if severe else 6)):
                            x1 = random.randint(0, clutter_img.shape[1]-10)
                            y1 = random.randint(0, clutter_img.shape[0]-10)
                            x2 = min(clutter_img.shape[1], x1 + random.randint(20,80))
                            y2 = min(clutter_img.shape[0], y1 + random.randint(20,80))
                            color = [random.randint(0,255) for _ in range(3)]
                            cv2.rectangle(clutter_img, (x1,y1), (x2,y2), color, -1)
                        # Blend clutter with degraded
                        alpha = random.uniform(0.2 if severe else 0.15,0.4 if severe else 0.3)
                        degraded = cv2.addWeighted(clutter_img, alpha, degraded, 1-alpha, 0)
                        metadata_degrades[degr] = {'blend_alpha': round(alpha,2)}
                    elif degr == 'color_inversion':
                        degraded = 255 - degraded
                        metadata_degrades[degr] = {'inverted': True}
                    elif degr == 'channel_dropout':
                        # Zero out one channel or two
                        channels = [0,1,2]
                        drop_ct = 2 if severe and random.random() < 0.4 else 1
                        drop = random.sample(channels, drop_ct)
                        for ch in drop:
                            degraded[:,:,ch] = 0
                        metadata_degrades[degr] = {'dropped_channels': drop}
                    elif degr == 'crumpling':
                        # Simulate crumpled paper with mesh displacement
                        h, w = degraded.shape[:2]
                        intensity = random.uniform(8 if severe else 3, 15 if severe else 10)
                        # Create displacement map
                        map_x = np.zeros((h, w), dtype=np.float32)
                        map_y = np.zeros((h, w), dtype=np.float32)
                        for y in range(h):
                            for x in range(w):
                                map_x[y, x] = x + intensity * np.sin(y / 10.0) * np.cos(x / 10.0)
                                map_y[y, x] = y + intensity * np.cos(y / 15.0) * np.sin(x / 15.0)
                        degraded = cv2.remap(degraded, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                        metadata_degrades[degr] = {'intensity': round(intensity,2)}
                    elif degr == 'cylindrical_warp':
                        # Simulate barcode on curved surface (bottle/can)
                        h, w = degraded.shape[:2]
                        curvature = random.uniform(0.0001 if severe else 0.00005, 0.0003 if severe else 0.0002)
                        map_x = np.zeros((h, w), dtype=np.float32)
                        map_y = np.zeros((h, w), dtype=np.float32)
                        for y in range(h):
                            for x in range(w):
                                offset_x = curvature * ((x - w/2)**2)
                                map_x[y, x] = x
                                map_y[y, x] = y + offset_x
                        degraded = cv2.remap(degraded, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                        metadata_degrades[degr] = {'curvature': round(curvature,6)}
                    elif degr == 'shadows':
                        # Add non-uniform shadow gradient
                        h, w = degraded.shape[:2]
                        shadow_type = random.choice(['linear', 'radial'])
                        if shadow_type == 'linear':
                            # Linear gradient from one side
                            side = random.choice(['left', 'right', 'top', 'bottom'])
                            gradient = np.zeros((h, w), dtype=np.float32)
                            if side == 'left':
                                for x in range(w):
                                    gradient[:, x] = x / w
                            elif side == 'right':
                                for x in range(w):
                                    gradient[:, x] = 1 - (x / w)
                            elif side == 'top':
                                for y in range(h):
                                    gradient[y, :] = y / h
                            else:  # bottom
                                for y in range(h):
                                    gradient[y, :] = 1 - (y / h)
                            darkness = random.uniform(0.6 if severe else 0.7, 0.8 if severe else 0.85)
                            shadow_mask = (gradient * (1 - darkness) + darkness)
                        else:  # radial
                            cx, cy = random.randint(int(w*0.2), int(w*0.8)), random.randint(int(h*0.2), int(h*0.8))
                            max_dist = np.sqrt(w**2 + h**2)
                            gradient = np.zeros((h, w), dtype=np.float32)
                            for y in range(h):
                                for x in range(w):
                                    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                                    gradient[y, x] = min(dist / max_dist, 1.0)
                            darkness = random.uniform(0.6 if severe else 0.7, 0.8 if severe else 0.85)
                            shadow_mask = (gradient * (1 - darkness) + darkness)
                        shadow_mask = np.stack([shadow_mask]*3, axis=2)
                        degraded = np.clip(degraded.astype(np.float32) * shadow_mask, 0, 255).astype(np.uint8)
                        metadata_degrades[degr] = {'type': shadow_type, 'darkness': round(darkness,2)}
                    elif degr == 'reflections':
                        # Add specular reflection spots (glossy surface)
                        h, w = degraded.shape[:2]
                        num_spots = random.randint(1 if severe else 1, 3 if severe else 2)
                        for _ in range(num_spots):
                            cx = random.randint(int(w*0.2), int(w*0.8))
                            cy = random.randint(int(h*0.2), int(h*0.8))
                            radius = random.randint(20 if severe else 15, 40 if severe else 30)
                            intensity = random.uniform(100 if severe else 80, 180 if severe else 150)
                            # Create circular gradient
                            for y in range(max(0, cy-radius), min(h, cy+radius)):
                                for x in range(max(0, cx-radius), min(w, cx+radius)):
                                    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                                    if dist < radius:
                                        blend = (1 - dist/radius) * (intensity / 255.0)
                                        degraded[y, x] = np.clip(degraded[y, x].astype(np.float32) * (1 - blend*0.5) + blend * 255, 0, 255).astype(np.uint8)
                        metadata_degrades[degr] = {'num_spots': num_spots}
                    elif degr == 'torn_edges':
                        # Simulate torn/ripped edges with irregular mask
                        h, w = degraded.shape[:2]
                        edge = random.choice(['top', 'bottom', 'left', 'right'])
                        tear_depth = random.randint(int(h*0.05) if severe else int(h*0.03), int(h*0.12) if severe else int(h*0.08))
                        mask = np.ones((h, w), dtype=np.uint8) * 255
                        if edge == 'top':
                            for x in range(w):
                                tear_y = tear_depth + random.randint(-15, 15)
                                mask[0:tear_y, x] = 0
                        elif edge == 'bottom':
                            for x in range(w):
                                tear_y = h - tear_depth + random.randint(-15, 15)
                                mask[tear_y:h, x] = 0
                        elif edge == 'left':
                            for y in range(h):
                                tear_x = tear_depth + random.randint(-15, 15)
                                mask[y, 0:tear_x] = 0
                        else:  # right
                            for y in range(h):
                                tear_x = w - tear_depth + random.randint(-15, 15)
                                mask[y, tear_x:w] = 0
                        # Apply mask (set torn areas to background)
                        mask_3ch = np.stack([mask]*3, axis=2)
                        degraded = np.where(mask_3ch > 0, degraded, 240).astype(np.uint8)
                        metadata_degrades[degr] = {'edge': edge, 'tear_depth': tear_depth}

                # Save image
                filename = f"challenging_{i:03d}.png"
                filepath = self.categories['challenging_conditions'] / filename
                cv2.imwrite(str(filepath), degraded)

                # Metadata
                metadata = {
                    'test_id': f"challenging_{i:03d}",
                    'image_path': str(filepath),
                    'barcode_data': [data],
                    'barcode_types': [barcode_type],
                    'rotation_angle': 0,
                    'barcode_count': 1,
                    'test_type': 'challenging',
                    'difficulty': 'extreme' if severe else 'hard',
                    'degradations': metadata_degrades,
                    'degradations_list': chosen
                }
                with open(filepath.with_suffix('.json'), 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error generating challenging barcode {i}: {e}")
                continue
    
    def _create_single_barcode_test_image(self, barcode_path: str, barcode_type: str, data: str) -> np.ndarray:
        """Create a test image with a single barcode."""
        # Load barcode
        barcode_img = cv2.imread(barcode_path)
        if barcode_img is None:
            # Create placeholder
            barcode_img = np.ones((150, 300, 3), dtype=np.uint8) * 255
        elif len(barcode_img.shape) == 2:  # Grayscale image
            # Convert to 3-channel for consistency
            barcode_img = cv2.cvtColor(barcode_img, cv2.COLOR_GRAY2BGR)
        
        # Create background image (3-channel for color compatibility)
        canvas_width = 800
        canvas_height = 600
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 240
        
        # Place barcode on canvas
        barcode_h, barcode_w = barcode_img.shape[:2]
        
        # Center the barcode on the canvas
        x = (canvas_width - barcode_w) // 2
        y = (canvas_height - barcode_h) // 2
        
        # Ensure the barcode fits within the canvas
        if x < 0 or y < 0 or x + barcode_w > canvas_width or y + barcode_h > canvas_height:
            print(f"Warning: Barcode doesn't fit on canvas. Barcode size: {barcode_w}x{barcode_h}, Canvas size: {canvas_width}x{canvas_height}")
            # Adjust barcode size to fit
            scale = min(canvas_width * 0.8 / barcode_w, canvas_height * 0.8 / barcode_h)
            new_w = int(barcode_w * scale)
            new_h = int(barcode_h * scale)
            barcode_img = cv2.resize(barcode_img, (new_w, new_h))
            barcode_h, barcode_w = new_h, new_w
            x = (canvas_width - barcode_w) // 2
            y = (canvas_height - barcode_h) // 2
        
        canvas[y:y+barcode_h, x:x+barcode_w] = barcode_img
        
        return canvas
    
    def _create_angled_barcode_test_image(self, barcode_path: str, barcode_type: str, data: str, angle: float) -> np.ndarray:
        """Create a test image with a rotated barcode - KEY FEATURE."""
        # Load barcode
        barcode_img = cv2.imread(barcode_path)
        if barcode_img is None:
            barcode_img = np.ones((150, 300, 3), dtype=np.uint8) * 255
        elif len(barcode_img.shape) == 2:  # Grayscale image
            # Convert to 3-channel for consistency
            barcode_img = cv2.cvtColor(barcode_img, cv2.COLOR_GRAY2BGR)
        
        # Create background (3-channel for color compatibility)
        canvas_width = 800
        canvas_height = 600
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 240
        
        # Rotate barcode
        center = (barcode_img.shape[1] // 2, barcode_img.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate the bounding box of the rotated image to avoid clipping
        cos = abs(rotation_matrix[0, 0])
        sin = abs(rotation_matrix[0, 1])
        
        # Compute new bounding dimensions
        new_w = int((barcode_img.shape[0] * sin) + (barcode_img.shape[1] * cos))
        new_h = int((barcode_img.shape[0] * cos) + (barcode_img.shape[1] * sin))
        
        # Adjust the rotation matrix to account for the new dimensions
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]
        
        # Perform rotation with expanded canvas to avoid clipping
        rotated_barcode = cv2.warpAffine(barcode_img, rotation_matrix, (new_w, new_h),
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=(240, 240, 240))
        
        # Get the actual dimensions of rotated image
        rot_h, rot_w = rotated_barcode.shape[:2]
        
        # Ensure the rotated barcode fits on the canvas
        available_w = canvas_width - 40  # Leave 20px margins
        available_h = canvas_height - 40
        
        if rot_w > available_w or rot_h > available_h:
            # Scale down if too large
            scale = min(available_w / rot_w, available_h / rot_h)
            new_w = int(rot_w * scale)
            new_h = int(rot_h * scale)
            rotated_barcode = cv2.resize(rotated_barcode, (new_w, new_h))
            rot_w, rot_h = new_w, new_h
        
        # Calculate position (center it on canvas)
        x = (canvas_width - rot_w) // 2
        y = (canvas_height - rot_h) // 2
        
        # Ensure we don't go out of bounds
        x = max(0, min(x, canvas_width - rot_w))
        y = max(0, min(y, canvas_height - rot_h))
        
        # Place rotated barcode on canvas
        canvas[y:y+rot_h, x:x+rot_w] = rotated_barcode
        
        return canvas
    
    def _create_multiple_barcode_test_image(self, barcode_files: List[str], barcode_data: List[str], count: int) -> np.ndarray:
        """Create a test image with multiple barcodes - KEY FEATURE."""
        # Create larger canvas for multiple barcodes (3-channel for color compatibility)
        canvas_width = 1600
        canvas_height = 1200
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 240
        
        # Calculate grid layout
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        
        cell_width = canvas_width // cols
        cell_height = canvas_height // rows
        
        # Calculate maximum barcode dimensions (leave margins)
        max_barcode_w = int(cell_width * 0.7)
        max_barcode_h = int(cell_height * 0.7)  # Use same ratio for consistency
        
        for i in range(count):
            row = i // cols
            col = i % cols
            
            if i < len(barcode_files):
                # Load barcode
                barcode_img = cv2.imread(barcode_files[i])
                if barcode_img is not None:
                    # Handle grayscale/3-channel conversion
                    if len(barcode_img.shape) == 2:  # Grayscale
                        barcode_img = cv2.cvtColor(barcode_img, cv2.COLOR_GRAY2BGR)
                    
                    # Get original dimensions
                    orig_h, orig_w = barcode_img.shape[:2]
                    
                    # Check if this is a square barcode (QR code) - exact square
                    is_square = (orig_h == orig_w)
                    
                    if is_square:
                        # For square barcodes (QR codes), use smaller cell dimension to stay square
                        target_size = min(max_barcode_w, max_barcode_h)
                        barcode_img = cv2.resize(barcode_img, (target_size, target_size))
                        actual_w, actual_h = target_size, target_size
                    else:
                        # For rectangular barcodes, fit within max dimensions while preserving aspect ratio
                        scale = min(max_barcode_w / orig_w, max_barcode_h / orig_h)
                        new_w = int(orig_w * scale)
                        new_h = int(orig_h * scale)
                        barcode_img = cv2.resize(barcode_img, (new_w, new_h))
                        actual_w, actual_h = new_w, new_h
                    
                    # Calculate position (center in cell)
                    x = col * cell_width + (cell_width - actual_w) // 2
                    y = row * cell_height + (cell_height - actual_h) // 2
                    
                    # Ensure positions are within canvas bounds
                    if x + actual_w <= canvas_width and y + actual_h <= canvas_height:
                        # Place barcode on canvas
                        canvas[y:y+actual_h, x:x+actual_w] = barcode_img
                    else:
                        # Skip if it doesn't fit
                        print(f"Warning: Barcode {i} doesn't fit at position ({x}, {y})")
        
        return canvas
    
    def _generate_sample_data(self, count: int) -> List[str]:
        """Generate sample data for barcodes with proper formats."""
        samples = []
        barcode_requirements = {
            'EAN13': lambda x: f"{x % 1000000000000:013d}",  # 13 digits
            'EAN8': lambda x: f"{x % 100000000:08d}",        # 8 digits  
            'ITF': lambda x: f"{x % 100000000000000:14d}",   # 14 digits (even number)
            'UPC-A': lambda x: f"{x % 100000000000:012d}",   # 12 digits
            'UPC-E': lambda x: f"{x % 10000000:08d}",        # 8 digits
            'CODE39': lambda x: f"CODE-{x % 9999:04d}",      # Alphanumeric
            'CODE128': lambda x: f"CODE{x % 999999:06d}",    # Alphanumeric
            'QR_CODE': lambda x: f"https://example.com/item/{x:06d}",  # URL
        }
        
        for i in range(count):
            barcode_type = random.choice(list(barcode_requirements.keys()))
            data = barcode_requirements[barcode_type](i)
            samples.append(data)
        
        return samples