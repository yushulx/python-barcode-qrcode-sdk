from setuptools.command import build_ext
from setuptools import setup, Extension
import sys
import os
import io
from setuptools.command.install import install
import platform
import shutil
from pathlib import Path

dbr_lib_dir = ''
dbr_include = ''
dbr_lib_name = 'DynamsoftBarcodeReader'

if sys.platform == "linux" or sys.platform == "linux2":
        # linux
        if platform.uname()[4] == 'AMD64' or platform.uname()[4] == 'x86_64':
                dbr_lib_dir = 'lib/linux'
        elif platform.uname()[4] == 'aarch64':
                dbr_lib_dir = 'lib/aarch64'
        else:
                dbr_lib_dir = 'lib/arm32'
elif sys.platform == "darwin":
    # OS X
    if platform.uname()[4] == 'arm64':
        dbr_lib_dir = 'lib/macos_arm64'
    else:
        dbr_lib_dir = 'lib/macos'
elif sys.platform == "win32":
    # Windows
    dbr_lib_name = 'DBRx64'
    dbr_lib_dir = 'lib/win'

if sys.platform == "linux" or sys.platform == "linux2":
    ext_args = dict(
        library_dirs = [dbr_lib_dir],
        extra_compile_args = ['-std=c++11'],
        extra_link_args = ["-Wl,-rpath=$ORIGIN"],
        libraries = [dbr_lib_name],
        include_dirs=['include']
    )
elif sys.platform == "darwin":
    ext_args = dict(
        library_dirs = [dbr_lib_dir],
        extra_compile_args = ['-std=c++11'],
        extra_link_args = ["-Wl,-rpath,@loader_path"],
        libraries = [dbr_lib_name],
        include_dirs=['include']
    )

long_description = io.open("README.md", encoding="utf-8").read()

if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
        module_barcodeQrSDK = Extension('barcodeQrSDK', ['src/barcodeQrSDK.cpp'], **ext_args)
else:
	module_barcodeQrSDK = Extension('barcodeQrSDK',
                        sources = ['src/barcodeQrSDK.cpp'],
                        include_dirs=['include'], library_dirs=[dbr_lib_dir], libraries=[dbr_lib_name])


def copylibs(src, dst):
        if os.path.isdir(src):
                filelist = os.listdir(src)
                for file in filelist:
                        libpath = os.path.join(src, file)
                        shutil.copy2(libpath, dst)
        else:
                shutil.copy2(src, dst)

class CustomBuildExt(build_ext.build_ext):
        def run(self):
                build_ext.build_ext.run(self)
                dst =  os.path.join(self.build_lib, "barcodeQrSDK")
                copylibs(dbr_lib_dir, dst)
                filelist = os.listdir(self.build_lib)
                for file in filelist:
                    filePath = os.path.join(self.build_lib, file)
                    if not os.path.isdir(file):
                        copylibs(filePath, dst)
                        # delete file for wheel package
                        os.remove(filePath)

class CustomBuildExtDev(build_ext.build_ext):
        def run(self):
                build_ext.build_ext.run(self)
                dev_folder = os.path.join(Path(__file__).parent, 'barcodeQrSDK')
                copylibs(dbr_lib_dir, dev_folder)
                filelist = os.listdir(self.build_lib)
                for file in filelist:
                    filePath = os.path.join(self.build_lib, file)
                    if not os.path.isdir(file):
                        copylibs(filePath, dev_folder)

class CustomInstall(install):
    def run(self):
        install.run(self)

setup (name = 'barcode-qr-code-sdk',
            version = '9.5.0',
            description = 'Barcode and QR code scanning SDK for Python',
            long_description=long_description,
            long_description_content_type="text/markdown",
            author='yushulx',
            url='https://github.com/yushulx/python-barcode-qrcode-sdk',
            license='MIT',
            packages=['barcodeQrSDK'],
        ext_modules = [module_barcodeQrSDK],
        # options={'build':{'build_lib':'./barcodeQrSDK'}},
        classifiers=[
                "Development Status :: 5 - Production/Stable",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "Intended Audience :: Education",
                "Intended Audience :: Information Technology",
                "Intended Audience :: Science/Research",
                "License :: OSI Approved :: MIT License",
                "Operating System :: Microsoft :: Windows",
                "Operating System :: MacOS",
                "Operating System :: POSIX :: Linux",
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
            install_requires=['opencv-python'],
            entry_points={
                'console_scripts': ['scanbarcode=barcodeQrSDK.scripts:scanbarcode']
            },
            cmdclass={
                    'install': CustomInstall,
                    'build_ext': CustomBuildExt,
                    'develop': CustomBuildExtDev},
        )
