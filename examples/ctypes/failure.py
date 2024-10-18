import os
import platform
from ctypes import *

system = platform.system()


class SamplingImageData(Structure):
    _fields_ = [
        ("bytes", POINTER(c_ubyte)),
        ("width", c_int),
        ("height", c_int)
    ]


class LocalizationResult(Structure):
    _fields_ = [
        ("terminatePhase", c_int),
        ("barcodeFormat", c_int),
        ("barcodeFormatString", c_char_p),
        ("barcodeFormat_2", c_int),
        ("barcodeFormatString_2", c_char_p),
        ("x1", c_int),
        ("y1", c_int),
        ("x2", c_int),
        ("y2", c_int),
        ("x3", c_int),
        ("y3", c_int),
        ("x4", c_int),
        ("y4", c_int),
        ("angle", c_int),
        ("moduleSize", c_int),
        ("pageNumber", c_int),
        ("regionName", c_char_p),
        ("documentName", c_char_p),
        ("resultCoordinateType", c_int),
        ("accompanyingTextBytes", c_char_p),
        ("accompanyingTextBytesLength", c_int),
        ("confidence", c_int),
        ("transformationMatrix", c_double * 9),
        ("reserved", c_char * 52)
    ]


class ExtendedResult(Structure):
    _fields_ = [
        ("resultType", c_int),
        ("barcodeFormat", c_int),
        ("barcodeFormatString", c_char_p),
        ("barcodeFormat_2", c_int),
        ("barcodeFormatString_2", c_char_p),
        ("confidence", c_int),
        ("bytes", POINTER(c_ubyte)),
        ("bytesLength", c_int),
        ("accompanyingTextBytes", POINTER(c_ubyte)),
        ("accompanyingTextBytesLength", c_int),
        ("deformation", c_int),
        ("detailedResult", c_void_p),
        ("samplingImage", SamplingImageData),
        ("clarity", c_int),
        ("reserved", c_char * 40)
    ]


class TextResult(Structure):
    _fields_ = [
        ("barcodeFormat", c_int),
        ("barcodeFormatString", c_char_p),
        ("barcodeFormat_2", c_int),
        ("barcodeFormatString_2", c_char_p),
        ("barcodeText", c_char_p),
        ("barcodeBytes", POINTER(c_ubyte)),
        ("barcodeBytesLength", c_int),
        ("localizationResult", POINTER(LocalizationResult)),
        ("detailedResult", c_void_p),
        ("resultsCount", c_int),
        ("results", POINTER(POINTER(ExtendedResult))),
        ("exception", c_char_p),
        ("isDPM", c_int),
        ("isMirrored", c_int),
        ("reserved", c_char * 44)
    ]


class TextResultArray(Structure):
    _fields_ = [
        ("resultsCount", c_int),
        ("results", POINTER(POINTER(TextResult)))
    ]


dbr = None
if 'Windows' in system:
    dll_path = license_dll_path = os.path.join(os.path.abspath(
        '.'), r'..\..\lib\win\DynamsoftBarcodeReaderx64.dll')

    # os.environ['path'] += ';' + dll_path
    # print(os.environ['path'])
    dbr = windll.LoadLibrary(dll_path)
else:
    dbr = CDLL(os.path.join(os.path.abspath('.'),
                            '../../lib/linux/libDynamsoftBarcodeReader.so'))

# DBR_InitLicense
DBR_InitLicense = dbr.DBR_InitLicense
DBR_InitLicense.argtypes = [c_char_p, c_char_p, c_int]
DBR_InitLicense.restype = c_int

license_key = b"DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
error_msg_buffer = create_string_buffer(256)
error_msg_buffer_len = len(error_msg_buffer)
# https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
ret = DBR_InitLicense(license_key, error_msg_buffer, error_msg_buffer_len)
print('initLicense: {}'.format(ret))

# DBR_CreateInstance
DBR_CreateInstance = dbr.DBR_CreateInstance
DBR_CreateInstance.restype = c_void_p
instance = dbr.DBR_CreateInstance()

# DBR_DecodeFile
DBR_DecodeFile = dbr.DBR_DecodeFile
DBR_DecodeFile.argtypes = [c_void_p, c_char_p, c_char_p]
DBR_DecodeFile.restype = c_int
ret = DBR_DecodeFile(instance, c_char_p(
    'test.png'.encode('utf-8')), c_char_p(''.encode('utf-8')))
print('DBR_DecodeFile: {}'.format(ret))

####################################################################################
# Failed to get barcode detection results
# DBR_GetAllTextResults
pResults = POINTER(TextResultArray)()
DBR_GetAllTextResults = dbr.DBR_GetAllTextResults
DBR_GetAllTextResults.argtypes = [c_void_p, POINTER(POINTER(TextResultArray))]
DBR_GetAllTextResults.restype = c_int


ret = DBR_GetAllTextResults(instance, byref(pResults))
print('DBR_GetAllTextResults: {}'.format(ret))

if ret != 0 or pResults.contents.resultsCount == 0:
    print("No barcode found.")
else:
    print(f"Total barcode(s) found: {pResults.contents.resultsCount}")
    for i in range(pResults.contents.resultsCount):
        result = pResults.contents.results[i]
        print(result)
        print(f"Barcode {i+1}:")
        # crash
        # print(result.contents)
        # print(f"  Type: {result.contents.barcodeFormatString.decode('utf-8')}")
        # print(f"  Text: {result.contents.barcodeText.decode('utf-8')}")

# DBR_FreeTextResults
DBR_FreeTextResults = dbr.DBR_FreeTextResults
DBR_FreeTextResults.argtypes = [POINTER(POINTER(TextResultArray))]
DBR_FreeTextResults.restype = None

if bool(pResults):
    DBR_FreeTextResults(byref(pResults))

####################################################################################

# DBR_DestroyInstance
DBR_DestroyInstance = dbr.DBR_DestroyInstance
DBR_DestroyInstance.argtypes = [c_void_p]
DBR_DestroyInstance(instance)
