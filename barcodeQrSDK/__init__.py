"""
Dynamsoft Barcode SDK Wrapper

This module provides a simplified Python interface for the Dynamsoft Capture Vision Bundle
for barcode reading functionality. It wraps the low-level SDK APIs with more Pythonic
interfaces for both synchronous and asynchronous barcode detection.

Example:
    Basic usage for reading barcodes from an image file:
    
    import barcodeQrSDK
    
    # Initialize license (required)
    barcodeQrSDK.initLicense("YOUR_LICENSE_KEY")
    
    # Create reader instance
    reader = barcodeQrSDK.createInstance()
    
    # Decode barcodes from file
    results = reader.decodeFile("path/to/image.jpg")
    
    for barcode in results:
        print(f"Text: {barcode.text}, Format: {barcode.format}")
"""

from dynamsoft_capture_vision_bundle import (
    EnumImagePixelFormat,
    EnumErrorCode, 
    EnumPresetTemplate,
    CaptureVisionRouter,
    LicenseManager,
    ImageData,
    ImageSourceAdapter,
    CapturedResultReceiver,
    BarcodeReaderModule
)
import time
from typing import List, Tuple, Callable, Union, Optional, Any
import numpy as np

__version__ = BarcodeReaderModule.get_version()

class FrameFetcher(ImageSourceAdapter):
    """
    Custom image source adapter for handling frame-by-frame image processing.
    
    This class extends ImageSourceAdapter to provide continuous image fetching
    capability for real-time barcode detection scenarios like camera streams.
    """
    
    def has_next_image_to_fetch(self) -> bool:
        """
        Indicates whether there are more images to fetch.
        
        Returns:
            bool: Always returns True to enable continuous image fetching.
        """
        return True

    def add_frame(self, imageData: ImageData) -> None:
        """
        Adds a new image frame to the processing buffer.
        
        Args:
            imageData (ImageData): The image data to be added to the buffer
                                  for barcode detection processing.
        """
        self.add_image_to_buffer(imageData)


class MyCapturedResultReceiver(CapturedResultReceiver):
    """
    Custom result receiver for handling asynchronous barcode detection results.
    
    This class processes captured results from the SDK and converts them
    to BarcodeResult objects before passing to the user-defined listener.
    """
    
    def __init__(self, listener: Callable[[List['BarcodeResult']], None]) -> None:
        """
        Initialize the result receiver with a callback listener.
        
        Args:
            listener (callable): A callback function that will be called
                               with a list of BarcodeResult objects when
                               barcodes are detected.
        """
        super().__init__()
        self.listener = listener
    
    def on_captured_result_received(self, result: Any) -> None:
        """
        Called when barcode detection results are received.
        
        This method processes the raw SDK results and converts them
        to BarcodeResult objects before calling the listener.
        
        Args:
            result: The captured result from the SDK containing detected items.
        """
        items = result.get_items()
        output: List['BarcodeResult'] = []
        for item in items:
            barcode = BarcodeResult(item)
            output.append(barcode)
        
        self.listener(output) 

class BarcodeResult:
    """
    Represents a single detected barcode with its properties.
    
    This class provides access to barcode text, format, and location coordinates
    in a convenient Python object format.
    
    Attributes:
        text (str): The decoded text content of the barcode
        format (str): The barcode format (e.g., "QR_CODE", "CODE_128")
        x1, y1, x2, y2, x3, y3, x4, y4 (float): Corner coordinates of the barcode
                                                location as four corner points
    """
    
    def __init__(self, item: Any) -> None:
        """
        Initialize a BarcodeResult from an SDK barcode item.
        
        Args:
            item: The barcode item from the SDK containing detection results.
        """
        self.text: str = item.get_text()
        self.format: str = item.get_format_string()

        # Extract location coordinates (four corner points)
        location = item.get_location()
        x1 = location.points[0].x
        y1 = location.points[0].y
        x2 = location.points[1].x
        y2 = location.points[1].y
        x3 = location.points[2].x
        y3 = location.points[2].y
        x4 = location.points[3].x
        y4 = location.points[3].y

        self.x1: float = x1
        self.y1: float = y1
        self.x2: float = x2
        self.y2: float = y2
        self.x3: float = x3
        self.y3: float = y3
        self.x4: float = x4
        self.y4: float = y4

class BarcodeReader:
    """
    Main barcode reader class providing both synchronous and asynchronous barcode detection.
    
    This class wraps the Dynamsoft Capture Vision SDK to provide an easy-to-use
    interface for barcode detection from various input sources including files,
    OpenCV matrices, raw bytes, and real-time streams.
    
    Example:
        reader = BarcodeReader()
        results = reader.decodeFile("barcode.jpg")
        for barcode in results:
            print(f"Found: {barcode.text} ({barcode.format})")
    """
    
    def __init__(self) -> None:
        """
        Initialize the barcode reader with default settings.
        
        Sets up the Capture Vision Router with barcode reading template
        and prepares the instance for both sync and async operations.
        """
        cvr_instance = CaptureVisionRouter()
        error_code, settings, error_message = cvr_instance.output_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
        cvr_instance.init_settings(settings)
        self.fetcher: FrameFetcher = FrameFetcher()
        cvr_instance.set_input(self.fetcher)
        self.cvr_instance: CaptureVisionRouter = cvr_instance
        self.receiver: Optional[MyCapturedResultReceiver] = None
    
    def getParameters(self) -> str:
        """
        Get the current detection parameters/settings.
        
        Returns:
            str: JSON string containing the current barcode detection settings
                 that can be modified and passed back to setParameters().
        """
        error_code, settings, error_message = self.cvr_instance.output_settings(EnumPresetTemplate.PT_READ_BARCODES.value)
        return settings
    
    def setParameters(self, params: str) -> Tuple[int, str]:
        """
        Set custom detection parameters/settings.
        
        Args:
            params (str): JSON string containing barcode detection settings.
                         Can be obtained from getParameters() and modified.
        
        Returns:
            tuple: (error_code, error_message) indicating success or failure.
        """
        error_code, error_message = self.cvr_instance.init_settings(params)
        return error_code, error_message

    def addAsyncListener(self, listener: Callable[[List[BarcodeResult]], None]) -> None:
        """
        Start asynchronous barcode detection with a callback listener.
        
        This enables real-time barcode detection where results are delivered
        via the callback function as they are detected.
        
        Args:
            listener (callable): Function to call with detected barcodes.
                               Receives a list of BarcodeResult objects.
        
        Example:
            def on_barcode_detected(barcodes):
                for barcode in barcodes:
                    print(f"Detected: {barcode.text}")
            
            reader.addAsyncListener(on_barcode_detected)
            # Now feed frames using decodeMatAsync() or decodeBytesAsync()
        """
        self.receiver = MyCapturedResultReceiver(listener)
        self.cvr_instance.add_result_receiver(self.receiver)
        error_code, error_message = self.cvr_instance.start_capturing('')

    def clearAsyncListener(self) -> None:
        """
        Stop asynchronous barcode detection and remove the listener.
        
        This stops the real-time detection process and cleans up resources.
        Call this when you're done with async detection.
        """
        if self.receiver is not None:
            self.cvr_instance.remove_result_receiver(self.receiver)
            self.receiver = None
        self.cvr_instance.stop_capturing()
        
    def decode(self, input: Union[str, ImageData]) -> List[BarcodeResult]:
        """
        Core decode method that handles various input types.
        
        Args:
            input: Can be a file path (str), ImageData object, or other
                  supported input format for barcode detection.
        
        Returns:
            list: List of BarcodeResult objects representing detected barcodes.
                 Empty list if no barcodes found or error occurred.
        """
        result = self.cvr_instance.capture(input, '')

        output: List[BarcodeResult] = []

        if result.get_error_code() != EnumErrorCode.EC_OK:
            print("Error:", result.get_error_code(),
                    result.get_error_string())
        else:
            items = result.get_items()
            for item in items:
                barcode = BarcodeResult(item)
                output.append(barcode)
        
        return output
    
    def decodeFile(self, file_path: str) -> List[BarcodeResult]:
        """
        Decode barcodes from an image file.
        
        Args:
            file_path (str): Path to the image file. Supports common formats
                           like JPEG, PNG, BMP, TIFF, etc.
        
        Returns:
            list: List of BarcodeResult objects for all detected barcodes.
        
        Example:
            results = reader.decodeFile("path/to/barcode.jpg")
            if results:
                print(f"Found {len(results)} barcodes")
        """
        return self.decode(file_path)
    
    def decodeMat(self, mat: np.ndarray) -> List[BarcodeResult]:
        """
        Decode barcodes from an OpenCV image matrix.
        
        Args:
            mat (numpy.ndarray): OpenCV image matrix (BGR or grayscale).
                               Typically obtained from cv2.imread() or camera capture.
        
        Returns:
            list: List of BarcodeResult objects for all detected barcodes.
        
        Example:
            import cv2
            image = cv2.imread("barcode.jpg")
            results = reader.decodeMat(image)
        """
        return self.decode(convertMat2ImageData(mat))

    def decodeBytes(self, bytes: bytes, width: int, height: int, stride: int, pixel_format: EnumImagePixelFormat) -> List[BarcodeResult]:
        """
        Decode barcodes from raw image bytes.
        
        Args:
            bytes: Raw image data as bytes
            width (int): Image width in pixels
            height (int): Image height in pixels  
            stride (int): Number of bytes per row (usually width * channels)
            pixel_format: EnumImagePixelFormat value (e.g., IPF_RGB_888)
        
        Returns:
            list: List of BarcodeResult objects for all detected barcodes.
        
        Example:
            # For RGB image
            results = reader.decodeBytes(
                image_bytes, 640, 480, 1920, 
                EnumImagePixelFormat.IPF_RGB_888
            )
        """
        imagedata = ImageData(bytes, width, height, stride, pixel_format)
        return self.decode(imagedata)

    def decodeMatAsync(self, mat: np.ndarray) -> None:
        """
        Add an OpenCV matrix to the async processing queue.
        
        Use this with addAsyncListener() for real-time barcode detection.
        The detection results will be delivered via the async listener callback.
        
        Args:
            mat (numpy.ndarray): OpenCV image matrix to process asynchronously.
        
        Example:
            reader.addAsyncListener(my_callback)
            while True:
                frame = camera.read()
                reader.decodeMatAsync(frame)
        """
        self.fetcher.add_frame(convertMat2ImageData(mat))

    def decodeBytesAsync(self, bytes: bytes, width: int, height: int, stride: int, pixel_format: EnumImagePixelFormat) -> None:
        """
        Add raw image bytes to the async processing queue.
        
        Use this with addAsyncListener() for real-time barcode detection
        from raw image data sources.
        
        Args:
            bytes: Raw image data as bytes
            width (int): Image width in pixels
            height (int): Image height in pixels
            stride (int): Number of bytes per row
            pixel_format: EnumImagePixelFormat value
        """
        imagedata = ImageData(bytes, width, height, stride, pixel_format)
        self.fetcher.add_frame(imagedata)


def initLicense(licenseKey: str) -> Tuple[int, str]:
    """
    Initialize the Dynamsoft license for barcode detection.
    
    This must be called before creating any BarcodeReader instances.
    The license key enables the SDK functionality.
    
    Args:
        licenseKey (str): Your Dynamsoft license key. Use "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==" for trial.
    
    Returns:
        tuple: (error_code, error_message) indicating license initialization result.
    
    Example:
        error_code, error_msg = initLicense("YOUR_LICENSE_KEY")
        if error_code != 0:
            print(f"License error: {error_msg}")
    """
    errorCode, errorMsg = LicenseManager.init_license(licenseKey)
    return errorCode, errorMsg

def createInstance() -> BarcodeReader:
    """
    Create a new BarcodeReader instance.
    
    This is the preferred way to create a barcode reader. Make sure to
    call initLicense() first.
    
    Returns:
        BarcodeReader: A new barcode reader instance ready for use.
    
    Example:
        initLicense("YOUR_LICENSE_KEY")
        reader = createInstance()
        results = reader.decodeFile("barcode.jpg")
    """
    return BarcodeReader()

def convertMat2ImageData(mat: np.ndarray) -> ImageData:
    """
    Convert an OpenCV matrix to Dynamsoft ImageData format.
    
    This utility function handles the conversion between OpenCV's numpy
    array format and the SDK's ImageData format, including proper
    pixel format detection for RGB and grayscale images.
    
    Args:
        mat (numpy.ndarray): OpenCV image matrix (RGB, BGR, or grayscale).
    
    Returns:
        ImageData: Converted image data ready for SDK processing.
    
    Note:
        - 3-channel images are treated as RGB_888
        - Single-channel images are treated as grayscale
        - The function automatically determines stride and pixel format
    """
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

def wrapImageData(width: int, height: int, stride: int, pixel_format: EnumImagePixelFormat, bytes: bytes) -> ImageData:
    """
    Create an ImageData object from raw image parameters.
    
    This utility function creates a properly formatted ImageData object
    from raw image specifications and byte data.
    
    Args:
        width (int): Image width in pixels
        height (int): Image height in pixels
        stride (int): Number of bytes per image row
        pixel_format: EnumImagePixelFormat specifying the pixel layout
        bytes: Raw image data as bytes
    
    Returns:
        ImageData: Formatted image data ready for SDK processing.
    
    Example:
        image_data = wrapImageData(
            640, 480, 1920, 
            EnumImagePixelFormat.IPF_RGB_888, 
            raw_bytes
        )
    """
    imagedata = ImageData(bytes, width, height, stride, pixel_format)
    return imagedata
