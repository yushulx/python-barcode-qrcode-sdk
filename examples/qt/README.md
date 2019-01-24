The sample demonstrates how to create a Python barcode app with Qt.

## Python
v3.7

## Installation
Qt for Python:

```
pip install pyside2
```

Download the [source code of Python barcode extension](https://github.com/dynamsoft-dbr/python/tree/master/src). Build and install it:

```
python setup.py build install
```

## License
Get a [30-day trial license](https://www.dynamsoft.com/CustomerPortal/Portal/Triallicense.aspx) for free.

## Usage
Edit `barcode-reader.py` to update the license:

```python
dbr.initLicense("Your License")
```

Set the default path for opening image files:

```python
QFileDialog.getOpenFileName(self, 'Open file',
                                               'E:\\Program Files (x86)\\Dynamsoft\\Barcode Reader 6.4.1\\Images', "Barcode images (*)")
```

Run the app:

```
python barcode-reader.py
```

<kbd><img src="https://www.codepool.biz/wp-content/uploads/2019/01/qt-python-barcode-reader.PNG" width="75%">