from distutils.core import setup, Extension
import sys
import os
import io
import numpy
from distutils.command.install import install

numpy_include = os.path.join(os.path.dirname(
    numpy.__file__), "core", "include", "numpy")

dbr_lib_dir = ''
dbr_dll = ''
dbr_include = ''
dbr_lib_name = 'DynamsoftBarcodeReader'

if sys.platform == "linux" or sys.platform == "linux2":
    # linux
    dbr_lib_dir = 'lib/linux'
elif sys.platform == "darwin":
    # OS X
    dbr_lib_dir = 'lib/macos'
    pass
elif sys.platform == "win32":
    # Windows
    dbr_lib_name = 'DBRx64'
    dbr_lib_dir = 'lib/win'
    dbr_dll = 'lib/win'

long_description = io.open("README.md", encoding="utf-8").read()
module_barcodeQrSDK = Extension('barcodeQrSDK',
                        sources = ['src/barcodeQrSDK.cpp'],
                        include_dirs=[
                       numpy_include, 'include'], library_dirs=[dbr_lib_dir], libraries=[dbr_lib_name])

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

setup (name = 'barcode-qr-code-sdk',
            version = '1.0.0',
            description = 'Barcode and QR code scanning SDK for Python',
            long_description=long_description,
            long_description_content_type="text/markdown",
            author='yushulx',
            url='https://github.com/yushulx/python-barcode-qrcode-sdk',
            license='MIT',
        ext_modules = [module_barcodeQrSDK],
        options={'build':{'build_lib':'./barcodeQrSDK'}},
        classifiers=[
                "Development Status :: 5 - Production/Stable",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "Intended Audience :: Education",
                "Intended Audience :: Information Technology",
                "Intended Audience :: Science/Research",
                "License :: OSI Approved :: MIT License",
                "Operating System :: Microsoft :: Windows",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3 :: Only",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: C++",
                "Programming Language :: Python :: Implementation :: CPython",
                "Topic :: Scientific/Engineering",
                "Topic :: Software Development",
            ],
            cmdclass={
                    'install': CustomInstall}
        )
