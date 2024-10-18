from dynamsoft_capture_vision_bundle import *
import numpy as np


def convertImageData2Mat(normalized_image):
    ba = bytearray(normalized_image.get_bytes())
    width = normalized_image.get_width()
    height = normalized_image.get_height()

    channels = 3
    if normalized_image.get_image_pixel_format() == EnumImagePixelFormat.IPF_BINARY:
        channels = 1
        all = []
        skip = normalized_image.stride * 8 - width

        index = 0
        n = 1
        for byte in ba:

            byteCount = 7
            while byteCount >= 0:
                b = (byte & (1 << byteCount)) >> byteCount

                if index < normalized_image.stride * 8 * n - skip:
                    if b == 1:
                        all.append(255)
                    else:
                        all.append(0)

                byteCount -= 1
                index += 1

            if index == normalized_image.stride * 8 * n:
                n += 1

        mat = np.array(all, dtype=np.uint8).reshape(height, width, channels)
        return mat

    elif normalized_image.get_image_pixel_format() == EnumImagePixelFormat.IPF_GRAYSCALED:
        channels = 1

    mat = np.array(ba, dtype=np.uint8).reshape(height, width, channels)

    return mat


def convertMat2ImageData(mat):
    if len(mat.shape) == 3:
        height, width, channels = mat.shape
        pixel_format = EnumImagePixelFormat.IPF_RGB_888
    else:
        height, width = mat.shape
        channels = 1
        pixel_format = EnumImagePixelFormat.IPF_GRAYSCALED

    stride = width * channels
    imagedata = ImageData(mat.tobytes(), width, height, stride, pixel_format)
    return imagedata


class MRZResult:
    def __init__(self, item: ParsedResultItem):
        self.doc_type = item.get_code_type()
        self.raw_text = []
        self.doc_id = None
        self.surname = None
        self.given_name = None
        self.nationality = None
        self.issuer = None
        self.gender = None
        self.date_of_birth = None
        self.date_of_expiry = None
        if self.doc_type == "MRTD_TD3_PASSPORT":
            if item.get_field_value("passportNumber") != None and item.get_field_validation_status("passportNumber") != EnumValidationStatus.VS_FAILED:
                self.doc_id = item.get_field_value("passportNumber")
            elif item.get_field_value("documentNumber") != None and item.get_field_validation_status("documentNumber") != EnumValidationStatus.VS_FAILED:
                self.doc_id = item.get_field_value("documentNumber")

        line = item.get_field_value("line1")
        if line is not None:
            if item.get_field_validation_status("line1") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)
        line = item.get_field_value("line2")
        if line is not None:
            if item.get_field_validation_status("line2") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)
        line = item.get_field_value("line3")
        if line is not None:
            if item.get_field_validation_status("line3") == EnumValidationStatus.VS_FAILED:
                line += ", Validation Failed"
            self.raw_text.append(line)

        if item.get_field_value("nationality") != None and item.get_field_validation_status("nationality") != EnumValidationStatus.VS_FAILED:
            self.nationality = item.get_field_value("nationality")
        if item.get_field_value("issuingState") != None and item.get_field_validation_status("issuingState") != EnumValidationStatus.VS_FAILED:
            self.issuer = item.get_field_value("issuingState")
        if item.get_field_value("dateOfBirth") != None and item.get_field_validation_status("dateOfBirth") != EnumValidationStatus.VS_FAILED:
            self.date_of_birth = item.get_field_value("dateOfBirth")
        if item.get_field_value("dateOfExpiry") != None and item.get_field_validation_status("dateOfExpiry") != EnumValidationStatus.VS_FAILED:
            self.date_of_expiry = item.get_field_value("dateOfExpiry")
        if item.get_field_value("sex") != None and item.get_field_validation_status("sex") != EnumValidationStatus.VS_FAILED:
            self.gender = item.get_field_value("sex")
        if item.get_field_value("primaryIdentifier") != None and item.get_field_validation_status("primaryIdentifier") != EnumValidationStatus.VS_FAILED:
            self.surname = item.get_field_value("primaryIdentifier")
        if item.get_field_value("secondaryIdentifier") != None and item.get_field_validation_status("secondaryIdentifier") != EnumValidationStatus.VS_FAILED:
            self.given_name = item.get_field_value("secondaryIdentifier")

    def to_string(self):
        msg = (f"Raw Text:\n")
        for index, line in enumerate(self.raw_text):
            msg += (f"\tLine {index + 1}: {line}\n")
        msg += (f"Parsed Information:\n"
                f"\tDocumentType: {self.doc_type or ''}\n"
                f"\tDocumentID: {self.doc_id or ''}\n"
                f"\tSurname: {self.surname or ''}\n"
                f"\tGivenName: {self.given_name or ''}\n"
                f"\tNationality: {self.nationality or ''}\n"
                f"\tIssuingCountryorOrganization: {self.issuer or ''}\n"
                f"\tGender: {self.gender or ''}\n"
                f"\tDateofBirth(YYMMDD): {self.date_of_birth or ''}\n"
                f"\tExpirationDate(YYMMDD): {self.date_of_expiry or ''}\n")
        return msg


def print_results(result: ParsedResult) -> None:
    tag = result.get_original_image_tag()
    if isinstance(tag, FileImageTag):
        print("File:", tag.get_file_path())
    if result.get_error_code() != EnumErrorCode.EC_OK:
        print("Error:", result.get_error_string())
    else:
        items = result.get_items()
        print("Parsed", len(items), "MRZ Zones.")
        for item in items:
            mrz_result = MRZResult(item)
            print(mrz_result.to_string())
