import sys

license = ''
if sys.platform == "linux" or sys.platform == "linux2":
    # linux
    license = 't0068NQAAAIY/7KegDlZn7YiPdAj0cbA11n2CwuCEWnk2KYla55ozdfmoasjRIpHhl0EUZmko/zxfxFLH3FpLw694uihoCVM='
elif sys.platform == "darwin":
    # OS X
    pass
elif sys.platform == "win32":
    # Windows
    license = 't0068NQAAAGWe/zXkYmggvyFrd8PmfjplKakH67Upt9HvuRDIBAV6MZ4uODuL1ZUgSEAOygejsfwj6XRKI5iD1tLKZBRGo2c='

barcodeTypes = 0x3FF | 0x2000000 | 0x4000000 | 0x8000000 | 0x10000000  # 1D, PDF417, QRCODE, DataMatrix, Aztec Code