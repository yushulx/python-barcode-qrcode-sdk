import sys

license = ''
if sys.platform == "linux" or sys.platform == "linux2":
    # linux
    license = 't0068NQAAAJUlQ1oDc6zPWxOAQWn7kD9EGtgZFIqK/k3ULJC5ccG9Xe/lpVOxod82bm6nXxqQXUpC1zjRXU514mWw9XLE1JM='
elif sys.platform == "darwin":
    # OS X
    license = 't0068NQAAAKrcxSxZwCY7qwBNDJJXAG3rFcJZTDsCdTHB2TlI0f1DvBg34MazLhAqhf6D2iE60OnWk9imYMc0inxb9OXWcrY='
elif sys.platform == "win32":
    # Windows
    license = 't0068NQAAAJwEbwJjt0+DiC2gJpQN4VQUhYTBmazlOU0RgWzDins2JUhtO6TK2Kj/Ck9+z5FlwuHn0KLK1NvkXYvThosPYog='

barcodeTypes = 0x3FF | 0x2000000 | 0x4000000 | 0x8000000 | 0x10000000  # 1D, PDF417, QRCODE, DataMatrix, Aztec Code