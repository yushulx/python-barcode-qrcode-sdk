
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
            f.write("QR code image would be here if qrcode library was available\n")
            f.write("Install with: pip install qrcode[pil]\n")
        print("Created placeholder file instead")
