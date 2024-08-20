from dbr import *

license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="
BarcodeReader.init_license(license_key)
reader = BarcodeReader()


def decode(filename, is_standard, special_character=None):
    try:
        text_results = reader.decode_file(filename)
        if text_results != None:
            for text_result in text_results:
                print('Barcode Format:')
                if is_standard:
                    print(text_result.barcode_format_string)
                else:
                    print(text_result.barcode_format_string_2 +
                          '. Start/Stop character is ' + special_character + '.')
                print('')
                print('Barcode Text:')
                print(text_result.barcode_text)
                print('')
                print('Localization Points:')
                print(text_result.localization_result.localization_points)
                print('------------------------------------------------')
                print('')
    except BarcodeReaderError as bre:
        print(bre)


def decode_non_standard(special_character, filename):
    json_file = None

    if special_character == '+':
        json_file = r"template_plus.json"

    if special_character == '-':
        json_file = r"template_minus.json"

    if json_file == None:
        return

    error = reader.init_runtime_settings_with_file(json_file)
    if error[0] != EnumErrorCode.DBR_OK:
        print(error[1])

    decode(filename, False, special_character)


def decode_standard(filename):
    decode(filename, True)


def main():
    decode_standard('code39_standard.PNG')
    decode_non_standard('+', 'code39_plus.PNG')
    decode_non_standard('-', 'code39_minus.PNG')


if __name__ == "__main__":
    main()
