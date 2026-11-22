from dynamsoft_barcode_reader_bundle import EnumErrorCode, LicenseManager


LICENSE_KEY = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ=="

_LICENSE_READY = False


def ensure_dbr_license():
    global _LICENSE_READY

    if _LICENSE_READY:
        return

    err, msg = LicenseManager.init_license(LICENSE_KEY)
    if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
        print(f"[DBR] License warning: {msg}")

    _LICENSE_READY = True