import os
import platform
from ctypes import *
import threading


class ResultInfo(Structure):
    _fields_ = [("format", c_char_p), ("text", c_char_p)]


class ResultList(Structure):
    _fields_ = [("size", c_int), ("pResultInfo", POINTER(POINTER(ResultInfo)))]


system = platform.system()

dbr = None
bridge = None
if 'Windows' in system:
    dll_path = license_dll_path = os.path.join(os.path.abspath(
        '.'), r'..\..\lib\win\DynamsoftBarcodeReaderx64.dll')

    dbr = windll.LoadLibrary(dll_path)

    bridge = windll.LoadLibrary(os.path.join(
        os.path.abspath('.'), r'bridge\build\Debug\bridge.dll'))
else:
    dbr = CDLL(os.path.join(os.path.abspath('.'),
                            '../../lib/linux/libDynamsoftBarcodeReader.so'))
    bridge = CDLL(os.path.join(os.path.abspath(
        '.'), 'bridge/build/libbridge.so'))

# DBR_InitLicense
DBR_InitLicense = dbr.DBR_InitLicense
DBR_InitLicense.argtypes = [c_char_p, c_char_p, c_int]
DBR_InitLicense.restype = c_int

license_key = b"DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
error_msg_buffer = create_string_buffer(256)
error_msg_buffer_len = len(error_msg_buffer)
# https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
ret = DBR_InitLicense(license_key, error_msg_buffer, error_msg_buffer_len)

# DBR_CreateInstance
DBR_CreateInstance = dbr.DBR_CreateInstance
DBR_CreateInstance.restype = c_void_p
instance = dbr.DBR_CreateInstance()

######################################################################
# Call decoding method in native thread.


@CFUNCTYPE(None, POINTER(ResultList))
def callback(address):
    data = cast(address, POINTER(ResultList))
    size = data.contents.size
    results = data.contents.pResultInfo
    for i in range(size):
        result = results[i]
        print('Format: %s' % result.contents.format.decode('utf-8'))
        print('Text: %s' % result.contents.text.decode('utf-8'))

    dbr_free_results = bridge.dbr_free_results
    dbr_free_results.argtypes = [c_void_p]
    if bool(address):
        dbr_free_results(address)
        DBR_DestroyInstance = dbr.DBR_DestroyInstance
        DBR_DestroyInstance.argtypes = [c_void_p]
        DBR_DestroyInstance(instance)
    return 0


def run():
    print("Python thread" + str(threading.current_thread()))
    bridge.registerCallback(callback)
    thread_decode = bridge.thread_decode
    thread_decode.argtypes = [c_void_p, c_void_p]
    thread_decode(instance, c_char_p('test.png'.encode('utf-8')))


t = threading.Thread(target=run)
t.start()
t.join()
