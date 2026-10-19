from dynamsoft_capture_vision_bundle import *
import numpy as np
import cv2

# Try to import RapidOCR for passport VIZ text recognition
try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
    print("✅ RapidOCR available for passport text recognition")
except ImportError as e:
    RAPIDOCR_AVAILABLE = False
    print(f"⚠️ RapidOCR not available. Error: {e}")
    print("Install with: pip install rapidocr_onnxruntime")


class PassportOCR:
    """
    OCR utility class for recognizing text in the Visual Inspection Zone (VIZ)
    of passports - the human-readable text above the MRZ.
    Uses RapidOCR (PaddleOCR via ONNX Runtime) for accurate text detection.
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Singleton pattern to reuse the OCR engine."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.engine = None
        self.available = False
        
        if RAPIDOCR_AVAILABLE:
            try:
                self.engine = RapidOCR()
                self.available = True
                print("✅ PassportOCR engine initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize RapidOCR: {e}")
        
        self._initialized = True
    
    def recognize_text(self, image, mrz_location=None):
        """
        Recognize text in the passport image, optionally excluding the MRZ zone.
        
        Args:
            image: OpenCV image (BGR format) or path to image file
            mrz_location: Optional tuple of (y_start, y_end) to exclude MRZ zone
                         If provided, only text ABOVE this region will be returned
        
        Returns:
            list: List of OCRResult objects containing:
                  - text: The recognized text
                  - confidence: Confidence score (0-1)
                  - bbox: Bounding box [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        """
        if not self.available or self.engine is None:
            return []
        
        try:
            # Run OCR
            result, elapse = self.engine(image)
            
            if result is None:
                return []
            
            ocr_results = []
            for item in result:
                bbox = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text = item[1]
                confidence = item[2]
                
                # Filter out MRZ zone if location provided
                if mrz_location is not None:
                    mrz_y_start, mrz_y_end = mrz_location
                    # Get the top Y coordinate of this text box
                    text_y = min(point[1] for point in bbox)
                    
                    # Skip if text is in or below the MRZ zone
                    if text_y >= mrz_y_start * 0.95:  # 5% margin
                        continue
                
                ocr_results.append(OCRResult(
                    text=text,
                    confidence=confidence,
                    bbox=bbox
                ))
            
            return ocr_results
            
        except Exception as e:
            print(f"❌ OCR error: {e}")
            return []
    
    def recognize_viz_region(self, image, mrz_items=None):
        """
        Recognize text specifically in the VIZ (Visual Inspection Zone) of a passport.
        Automatically excludes the MRZ zone based on detected MRZ items.
        
        Args:
            image: OpenCV image (BGR format)
            mrz_items: List of MRZ detection items with get_location() method
        
        Returns:
            list: List of OCRResult objects for text in the VIZ
        """
        if not self.available:
            return []
        
        # Determine MRZ zone location from detected items
        mrz_location = None
        if mrz_items:
            try:
                min_y = float('inf')
                max_y = 0
                
                for item in mrz_items:
                    if hasattr(item, 'get_location'):
                        location = item.get_location()
                        for point in location.points:
                            min_y = min(min_y, point.y)
                            max_y = max(max_y, point.y)
                
                if min_y < float('inf'):
                    mrz_location = (min_y, max_y)
            except Exception as e:
                print(f"⚠️ Could not determine MRZ location: {e}")
        
        return self.recognize_text(image, mrz_location)


class OCRResult:
    """Container for OCR recognition results."""
    
    def __init__(self, text, confidence, bbox):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    def get_center(self):
        """Get the center point of the bounding box."""
        x_coords = [p[0] for p in self.bbox]
        y_coords = [p[1] for p in self.bbox]
        return (sum(x_coords) / 4, sum(y_coords) / 4)
    
    def get_top_y(self):
        """Get the top Y coordinate of the bounding box."""
        return min(p[1] for p in self.bbox)
    
    def __repr__(self):
        return f"OCRResult(text='{self.text[:20]}...', conf={self.confidence:.2f})"


# Global OCR instance (lazy initialization)
_passport_ocr = None

def get_passport_ocr():
    """Get or create the global PassportOCR instance."""
    global _passport_ocr
    if _passport_ocr is None:
        _passport_ocr = PassportOCR()
    return _passport_ocr


def convertImageData2Mat(normalized_image):
    ba = bytearray(normalized_image.get_bytes())
    width = normalized_image.get_width()
    height = normalized_image.get_height()

    channels = 3
    if normalized_image.get_image_pixel_format() == EnumImagePixelFormat.IPF_BINARY:
        channels = 1
        all = []
        skip = normalized_image.stride * 8 - width

        index = 0
        n = 1
        for byte in ba:

            byteCount = 7
            while byteCount >= 0:
                b = (byte & (1 << byteCount)) >> byteCount

                if index < normalized_image.stride * 8 * n - skip:
                    if b == 1:
                        all.append(255)
                    else:
                        all.append(0)

                byteCount -= 1
                index += 1

            if index == normalized_image.stride * 8 * n:
                n += 1

        mat = np.array(all, dtype=np.uint8).reshape(height, width, channels)
        return mat

    elif normalized_image.get_image_pixel_format() == EnumImagePixelFormat.IPF_GRAYSCALED:
        channels = 1

    mat = np.array(ba, dtype=np.uint8).reshape(height, width, channels)

    return mat


def convertMat2ImageData(mat):
    if len(mat.shape) == 3:
        height, width, channels = mat.shape
        pixel_format = EnumImagePixelFormat.IPF_RGB_888
    else:
        height, width = mat.shape
        channels = 1
        pixel_format = EnumImagePixelFormat.IPF_GRAYSCALED

    stride = width * channels
    imagedata = ImageData(mat.tobytes(), width, height, stride, pixel_format)
    return imagedata


class MRZResult:
    def __init__(self, item: ParsedResultItem):
        self.doc_type = item.get_code_type()
        self.raw_text = []
        self.doc_id = None
        self.surname = None
        self.given_name = None
        self.nationality = None
        self.issuer = None
        self.gender = None
        self.date_of_birth = None
        self.date_of_expiry = None
        if self.doc_type == "MRTD_TD3_PASSPORT":
            if item.get_field_value("passportNumber") != None and item.get_field_validation_status("passportNumber") != EnumValidationStatus.VS_FAILED:
                self.doc_id = item.get_field_value("passportNumber")
            elif item.get_field_value("documentNumber") != None and item.get_field_validation_status("documentNumber") != EnumValidationStatus.VS_FAILED:
                self.doc_id = item.get_field_value("documentNumber")

        line = item.get_field_value("line1")
        if line is not None:
            if item.get_field_validation_status("line1") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)
        line = item.get_field_value("line2")
        if line is not None:
            if item.get_field_validation_status("line2") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)
        line = item.get_field_value("line3")
        if line is not None:
            if item.get_field_validation_status("line3") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)

        if item.get_field_value("nationality") != None and item.get_field_validation_status("nationality") != EnumValidationStatus.VS_FAILED:
            self.nationality = item.get_field_value("nationality")
        if item.get_field_value("issuingState") != None and item.get_field_validation_status("issuingState") != EnumValidationStatus.VS_FAILED:
            self.issuer = item.get_field_value("issuingState")
        if item.get_field_value("dateOfBirth") != None and item.get_field_validation_status("dateOfBirth") != EnumValidationStatus.VS_FAILED:
            self.date_of_birth = item.get_field_value("dateOfBirth")
        if item.get_field_value("dateOfExpiry") != None and item.get_field_validation_status("dateOfExpiry") != EnumValidationStatus.VS_FAILED:
            self.date_of_expiry = item.get_field_value("dateOfExpiry")
        if item.get_field_value("sex") != None and item.get_field_validation_status("sex") != EnumValidationStatus.VS_FAILED:
            self.gender = item.get_field_value("sex")
        if item.get_field_value("primaryIdentifier") != None and item.get_field_validation_status("primaryIdentifier") != EnumValidationStatus.VS_FAILED:
            self.surname = item.get_field_value("primaryIdentifier")
        if item.get_field_value("secondaryIdentifier") != None and item.get_field_validation_status("secondaryIdentifier") != EnumValidationStatus.VS_FAILED:
            self.given_name = item.get_field_value("secondaryIdentifier")

    def to_string(self):
        msg = (f"Raw Text:\n")
        for index, line in enumerate(self.raw_text):
            msg += (f"\tLine {index + 1}: {line}\n")
        msg += (f"Parsed Information:\n"
                f"\tDocumentType: {self.doc_type or ''}\n"
                f"\tDocumentID: {self.doc_id or ''}\n"
                f"\tSurname: {self.surname or ''}\n"
                f"\tGivenName: {self.given_name or ''}\n"
                f"\tNationality: {self.nationality or ''}\n"
                f"\tIssuingCountryorOrganization: {self.issuer or ''}\n"
                f"\tGender: {self.gender or ''}\n"
                f"\tDateofBirth(YYMMDD): {self.date_of_birth or ''}\n"
                f"\tExpirationDate(YYMMDD): {self.date_of_expiry or ''}\n")
        return msg


def print_results(result: ParsedResult) -> None:
    tag = result.get_original_image_tag()
    if isinstance(tag, FileImageTag):
        print("File:", tag.get_file_path())
    if result.get_error_code() != EnumErrorCode.EC_OK:
        print("Error:", result.get_error_string())
    else:
        items = result.get_items()
        print("Parsed", len(items), "MRZ Zones.")
        for item in items:
            mrz_result = MRZResult(item)
            print(mrz_result.to_string())
