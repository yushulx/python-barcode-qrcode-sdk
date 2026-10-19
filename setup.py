from setuptools import setup
import io

long_description = io.open("README.md", encoding="utf-8").read()

setup(name='barcode-qr-code-sdk',
      version='11.6.4000',
      description='Barcode and QR code scanning SDK for Python',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='yushulx',
      url='https://github.com/yushulx/python-barcode-qrcode-sdk',
      license='MIT',
      packages=['barcodeQrSDK'],
      classifiers=[
           "Development Status :: 5 - Production/Stable",
           "Environment :: Console",
           "Intended Audience :: Developers",
          "Intended Audience :: Education",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: MacOS",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3 :: Only",
          "Programming Language :: Python :: 3.10",
          "Programming Language :: Python :: 3.11",
          "Programming Language :: Python :: 3.12",
          "Programming Language :: Python :: 3.13",
          "Programming Language :: Python :: 3.14",
          "Topic :: Scientific/Engineering",
          "Topic :: Software Development",
      ],
      install_requires=['opencv-python', 'dynamsoft-capture-vision-bundle==3.6.4000'],
      python_requires='>=3.10',
      entry_points={
          'console_scripts': ['scanbarcode=barcodeQrSDK.scripts:scanbarcode']
      },
      )
