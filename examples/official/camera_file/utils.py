from dynamsoft_barcode_reader_bundle import *
import numpy as np


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


