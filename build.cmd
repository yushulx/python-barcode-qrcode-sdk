cd src
python setup.py build

copy ..\bin\*.* ..\wheel\dbr\
cd build\lib.win-*\
copy *.* ..\..\..\wheel\dbr\
cd ..\..\..\wheel\

python setup.py bdist_wheel