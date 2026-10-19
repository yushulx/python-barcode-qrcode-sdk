from django.http import HttpResponse, request
from django import template
from django.shortcuts import render
import os

from .models import Image

import json
from dynamsoft_capture_vision_bundle import *

# Apply for a trial license: https://www.dynamsoft.com/customer/license/trialLicense/?product=dcv&package=cross-platform
error_code, error_message = LicenseManager.init_license(
    "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==")
if error_code != EnumErrorCode.EC_OK and error_code != EnumErrorCode.EC_LICENSE_CACHE_USED:
    print("License initialization failed: ErrorCode:",
          error_code, ", ErrorString:", error_message)


def index(request):
    return render(request, 'scanbarcode/index.html')


def upload(request):
    out = "No barcode found"
    if request.method == 'POST':
        filePath = handle_uploaded_file(
            request.FILES['RemoteFile'], str(request.FILES['RemoteFile']))
        cvr_instance = CaptureVisionRouter()
        result = cvr_instance.capture(
            filePath, EnumPresetTemplate.PT_READ_BARCODES.value)

        items = result.get_items()

        if len(items) > 0:
            out = ''
            for item in items:
                out += "Barcode Format : " + item.get_format_string() + "\n"
                out += "Barcode Text : " + item.get_text() + "\n"
                out += "------------------------------------------------------------\n"

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
