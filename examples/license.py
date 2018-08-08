import sys

dbr_license = ''
if sys.platform == "linux" or sys.platform == "linux2":
    # linux
    dbr_license = 't0068NQAAAHSLeRGgQNNSj5KP8wyR7gqp3AHhmaB9JY4fMDis6J7Veox1d6OJwzJK+pBqRVRcgRhbH8v04cy+KZ6o28jthlw='
elif sys.platform == "darwin":
    # OS X
    pass
elif sys.platform == "win32":
    # Windows
    dbr_license = 't0068NQAAAFdeb4LWUdRVDmkg49LUtdiRPFIquQt7hDNyQLebOU5y7b9z4Is2mirRnansvZkWO9191n/va21Pmv+FzrmPKqs='
