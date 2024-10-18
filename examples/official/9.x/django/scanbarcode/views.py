from django.http import HttpResponse, request
from django import template
from django.shortcuts import render
import os

from .models import Image

from dbr import *
import json

# Apply for a trial license: https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
BarcodeReader.init_license(
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
reader = BarcodeReader()


def index(request):
    return render(request, 'scanbarcode/index.html')


def upload(request):
    out = "No barcode found"
    if request.method == 'POST':
        filePath = handle_uploaded_file(
            request.FILES['RemoteFile'], str(request.FILES['RemoteFile']))
        try:
            text_results = reader.decode_file(filePath)
            if text_results != None:
                out = ''
                for text_result in text_results:
                    out += "Barcode Format : " + text_result.barcode_format_string + "\n"
                    out += "Barcode Text : " + text_result.barcode_text + "\n"
                    out += "------------------------------------------------------------\n"
        except BarcodeReaderError as bre:
            print(bre)
            return HttpResponse(out)

        return HttpResponse(out)
        # image = Image()
        # image.name = request.FILES['RemoteFile'].name
        # image.data = request.FILES['RemoteFile']
        # image.save()
        # return HttpResponse("Successful")

    return HttpResponse(out)


def handle_uploaded_file(file, filename):
    if not os.path.exists('upload/'):
        os.mkdir('upload/')

    filePath = 'upload/' + filename
    with open(filePath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

        return filePath
