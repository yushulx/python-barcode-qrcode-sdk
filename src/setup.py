from distutils.core import setup, Extension
import sys
import os
import numpy
from distutils.command.install import install

# NumPy header file path.
numpy_include = os.path.join(os.path.dirname(
    numpy.__file__), "core", "include", "numpy")
print(numpy_include)

# Customization for different platforms
dbr_lib_dir = ''
dbr_dll = ''
dbr_include = ''
dbr_lib_name = 'DynamsoftBarcodeReader'

if sys.platform == "linux" or sys.platform == "linux2":
    # linux
    dbr_lib_dir = '/usr/lib'
elif sys.platform == "darwin":
    # OS X
    dbr_lib_dir = '/usr/lib'
    pass
elif sys.platform == "win32":
    # Windows
    dbr_lib_name = 'DBRx64'
    dbr_lib_dir = r'c:\Program Files (x86)\Dynamsoft\Barcode Reader 7.2.1\Components\C_C++\Lib'
    dbr_dll = r'c:\Program Files (x86)\Dynamsoft\Barcode Reader 7.2.1\Components\C_C++\Redist\x64'

module_dbr = Extension('dbr', sources=['dbr.c'], include_dirs=[
                       numpy_include], library_dirs=[dbr_lib_dir], libraries=[dbr_lib_name])


class CustomInstall(install):
    def run(self):
        install.run(self)
        if sys.platform == "win32":
            import shutil
            from distutils.sysconfig import get_python_lib
            src = dbr_dll
            dst = get_python_lib()

            if os.path.isdir(src):
                lst = os.listdir(src)
                for f in lst:
                    dll = os.path.join(src, f)
                    shutil.copy2(dll, dst)
            else:
                shutil.copy2(src, dst)


setup(name='dbr',
      version='7.2.1',
      description='Python barcode extension',
      author='Dynamsoft',
      author_email='support@dynamsoft.com',
      url='https://www.dynamsoft.com/Products/Dynamic-Barcode-Reader.aspx',
      license='https://www.dynamsoft.com/Products/barcode-reader-license-agreement.aspx',
      ext_modules=[module_dbr],
      long_description='Dynamsoft Barcode Reader is a software development toolkit which enables barcode recognition of Code 39, Code 129, QR Code, DataMatrix, PDF417 and Aztec.',
      platforms=['Windows', 'Linux', 'macOS'],
      cmdclass={'install': CustomInstall}
      )
