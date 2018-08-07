/*
*	DynamsoftBarcodeReader.h
*	Dynamsoft Barcode Reader 6.2 C/C++ API header file.
*
*	Copyright 2018 Dynamsoft Corporation. All rights reserved.
*/

#ifndef __DYNAMSOFT_BARCODE_READER_H__
#define __DYNAMSOFT_BARCODE_READER_H__

#if !defined(_WIN32) && !defined(_WIN64)
#define DBR_API __attribute__((visibility("default")))
typedef signed char BOOL;
typedef void* HANDLE;
#include <stddef.h>
#else
#ifdef DBR_EXPORTS
#define DBR_API __declspec(dllexport)
#else
#define DBR_API 
#endif
#include <windows.h>
#endif

//---------------------------------------------------------------------------
// DBR Version
//---------------------------------------------------------------------------

#define DBR_VERSION                  "6.2.0.605";

//---------------------------------------------------------------------------
// Error Code definition
//---------------------------------------------------------------------------

// Successful.
#define DBR_OK									0
// Unknown error.
#define DBRERR_UNKNOWN						-10000
// Not enough memory to perform the operation.
#define DBRERR_NO_MEMORY					-10001
// Null pointer.
#define DBRERR_NULL_POINTER					-10002	
// The license is invalid.
#define DBRERR_LICENSE_INVALID				-10003	
// The license has expired.
#define DBRERR_LICENSE_EXPIRED				-10004	
// The file is not found.
#define DBRERR_FILE_NOT_FOUND				-10005	
// The file type is not supported.
#define DBRERR_FILETYPE_NOT_SUPPORTED		-10006	
// The BPP(Bits per pixel) is not supported.
#define DBRERR_BPP_NOT_SUPPORTED			-10007	
// The index is invalid.
#define DBRERR_INDEX_INVALID				-10008
// The barcode format is invalid.
#define DBRERR_BARCODE_FORMAT_INVALID		-10009
// The input region value parameter is invalid.
#define DBRERR_CUSTOM_REGION_INVALID		-10010
// The maximum barcode number is invalid.
#define DBRERR_MAX_BARCODE_NUMBER_INVALID	-10011
// Failed to read the image.
#define DBRERR_IMAGE_READ_FAILED			-10012
// Failed to read the TIFF image.
#define DBRERR_TIFF_READ_FAILED				-10013
// The QR Code license is invalid.
#define DBRERR_QR_LICENSE_INVALID			-10016
// The 1D Barcode license is invalid.
#define DBRERR_1D_LICENSE_INVALID			-10017
// The DIB(Device-independent bitmaps) buffer is invalid.
#define DBRERR_DIB_BUFFER_INVALID			-10018
// The PDF417 license is invalid.
#define DBRERR_PDF417_LICENSE_INVALID		-10019
// The DATAMATRIX license is invalid.
#define DBRERR_DATAMATRIX_LICENSE_INVALID	-10020
// Failed to read the PDF file.
#define DBRERR_PDF_READ_FAILED				-10021
// The PDF DLL is missing.
#define	DBRERR_PDF_DLL_MISSING				-10022
// The page number is invalid.
#define DBRERR_PAGE_NUMBER_INVALID			-10023
// The custom size is invalid.
#define DBRERR_CUSTOM_SIZE_INVALID			-10024
// The custom module size is invalid.
#define DBRERR_CUSTOM_MODULESIZE_INVALID	-10025
// Recognition timeout.
#define DBRERR_RECOGNITION_TIMEOUT			-10026
// Failed to parse json string.
#define DBRERR_JSON_PARSE_FAILED			-10030
// The value type is invalid.
#define DBRERR_JSON_TYPE_INVALID			-10031
// The key is invalid.
#define DBRERR_JSON_KEY_INVALID				-10032
// The value is invalid or out of range.
#define DBRERR_JSON_VALUE_INVALID			-10033
// The mandatory key "Name" is missing.
#define DBRERR_JSON_NAME_KEY_MISSING		-10034
// The value of the key "Name" is duplicated.
#define DBRERR_JSON_NAME_VALUE_DUPLICATED	-10035
// The template name is invalid.
#define DBRERR_TEMPLATE_NAME_INVALID		-10036
// The name reference is invalid
#define DBRERR_JSON_NAME_REFERENCE_INVALID	-10037
//The parameter value is invalid or out of range.
#define DBRERR_PARAMETER_VALUE_INVALID      -10038
//The domain of your current site does not match the domain bound in the current product key.
#define DBRERR_DOMAIN_NOT_MATCHED           -10039

//The reserved info does not match the reserved info bound in the current product key.
//#define DBRERR_RESERVEDINFO_NOT_MATCHED    -10040

//---------------------------------------------------------------------------
// Enums
//---------------------------------------------------------------------------

// Describes the type of the barcode. 
// All the formats can be combined, such as BF_CODE_39 | BF_CODE_128.
typedef enum
{
	// All supported formats	
	BF_All = 234882047,
	// One-D
	BF_OneD = 0x3FF,
	// Code 39
	BF_CODE_39 = 0x1,
	// Code 128
	BF_CODE_128 = 0x2,
	// Code 93
	BF_CODE_93 = 0x4,
	// Codabar
	BF_CODABAR = 0x8,
	// Interleaved 2 of 5
	BF_ITF = 0x10,
	// EAN-13
	BF_EAN_13 = 0x20,
	// EAN-8
	BF_EAN_8 = 0x40,
	// UPC-A
	BF_UPC_A = 0x80,
	// UPC-E
	BF_UPC_E = 0x100,
	// Industrial 2 of 5
	BF_INDUSTRIAL_25 = 0x200,
	// PDF417
	BF_PDF417 = 0x2000000,
	// QRCode
	BF_QR_CODE = 0x4000000,
	// DataMatrix
	BF_DATAMATRIX = 0x8000000
}BarcodeFormat;

// Describes the image pixel format.
typedef enum
{
	//0:Black, 1:White
	IPF_Binary,			
	//0:White, 1:Black
	IPF_BinaryInverted,	
	//8bit gray
	IPF_GrayScaled,		
	//NV21
	IPF_NV21,			
	//16bit
	IPF_RGB_565,		
	//16bit
	IPF_RGB_555,		
	//24bit
	IPF_RGB_888,		
	//32bit
	IPF_ARGB_8888,		
}ImagePixelFormat;

// Describes the extended result type.
typedef enum
{
	// Specifies the standard text. This means the barcode value.
	EDT_StandardText,
	// Specifies the raw text. This means the text that includes start/stop characters, check digits, etc.
	EDT_RawText,
	// Specifies all the candidate text. This means all the standard text results decoded from the barcode.
	EDT_CandidateText,
	// Specifies the partial Text. This means part of the text result decoded from the barcode.
	EDT_PartialText
}ResultType;

// Describes the stage when the results are returned.
typedef enum
{
	// Prelocalized
	ETS_Prelocalized,
	// Localized
	ETS_Localized,
	// Recognized
	ETS_Recognized
}TerminateStage;

//---------------------------------------------------------------------------
// Structures
//---------------------------------------------------------------------------

#pragma pack(push)
#pragma pack(1)

// Stores the extended result including the format, the bytes, etc.
typedef struct tagSExtendedResult
{
	// Extended result type
	ResultType emResultType;

	// Barcode type
	BarcodeFormat emBarcodeFormat;
	
	// Barcode type as string
	const char* pszBarcodeFormatString;

	// The confidence of the result
	int iConfidence;

	// The content in a byte array
	unsigned char* pBytes;

	// The length of the byte array 
	int nBytesLength;
}SExtendedResult, *PSExtendedResult;

// Stores the localization result including the boundary, the angle, the page number, the region name, etc. 
typedef struct tagSLocalizationResult
{
	// The stage of localization result.
	TerminateStage emTerminateStage;
	
	// Barcode type. Only OneD/QRCode/PDF417/DataMatrix
	BarcodeFormat emBarcodeFormat;
	
	// Barcode type as string
	const char* pszBarcodeFormatString;

	// The X coordinate of the left-most point
	int iX1;
	
	// The Y coordinate of the left-most point
	int iY1;
	
	// The X coordinate of the second point in a clockwise direction
	int iX2;
	
	// The Y coordinate of the second point in a clockwise direction
	int iY2;
	
	// The X coordinate of the third point in a clockwise direction
	int iX3;
	
	// The Y coordinate of the third point in a clockwise direction
	int iY3;
	
	// The X coordinate of the fourth point in a clockwise direction
	int iX4;
	
	// The Y coordinate of the fourth point in a clockwise direction
	int iY4;
	
	// The angle of a barcode. Values range from 0 to 360.
	int iAngle;

	// The barcode module size (the minimum bar width in pixel)
	int iModuleSize;
	
	// The page number the barcode located in. The index is 0-based.
	int iPageNumber;

	// The region name the barcode located in.
	const char* pszRegionName;

	// The region name the barcode located in.
	const char* pszDocumentName;

	// The total extended result count
	int nResultsCount;

	// The extended result array
	PSExtendedResult* ppResults;
}SLocalizationResult, *PSLocalizationResult;

// Stores the localization result count and result array. 
typedef struct tagSLocalizationResultArray
{
	// The total localization result count
	int nResultsCount;

	// The localization result array
	PSLocalizationResult *ppResults;
} SLocalizationResultArray;

// Stores the text result including the format, the text, the bytes, the localization result etc. 
typedef struct tagSTextResult
{
	// The barcode format
	BarcodeFormat emBarcodeFormat;

	// Barcode type as string
	const char* pszBarcodeFormatString;
	
	// The barcode text, ends by '\0'
	const char* pszBarcodeText;

	// The barcode content in a byte array
	unsigned char* pBarcodeBytes;
	
	// The length of the byte array 
	int nBarcodeBytesLength;

	// The corresponding localization result
	SLocalizationResult* pLocalizationResult;
} STextResult, *PSTextResult;

// Stores the text result count and result in an array. 
typedef struct tagSTextResultArray
{
	// The total text result count
	int nResultsCount;

	// The text result array
	PSTextResult *ppResults;
} STextResultArray;


typedef enum 
{
	//RPM_Auto,
    RPM_Disable = 1,
    RPM_Enable = 2,
	//RPM_Unknown
}RegionPredetectionMode;

typedef enum 
{
	//TFM_Auto,
    TFM_Disable = 1,
    TFM_Enable = 2,
	//TFM_Unknown
}TextFilterMode;


typedef enum 
{
    BIM_DarkOnLight,
    BIM_LightOnDark,
	//BCM_Unknown
}BarcodeInvertMode;

typedef enum 
{
	CICM_Auto = 0,
	CICM_Grayscale = 1
}ColourImageConvertMode;

typedef struct tagPublicParameterSettings
{
    char mName[32];
    int mTimeout;
    int mPDFRasterDPI;
    TextFilterMode mTextFilterMode;
    RegionPredetectionMode mRegionPredetectionMode;
    char mLocalizationAlgorithmPriority[64];
    int mBarcodeFormatIds;
    int mMaxAlgorithmThreadCount;
    int mTextureDetectionSensitivity;
    int mDeblurLevel;
    int mAntiDamageLevel;
    int mMaxDimOfFullImageAsBarcodeZone;
    int mMaxBarcodesCount;
    BarcodeInvertMode mBarcodeInvertMode;
    int mScaleDownThreshold;
    int mGrayEqualizationSensitivity;
    int mEnableFillBinaryVacancy;
    ColourImageConvertMode mColourImageConvertMode;
	char mReserved[248]; //6.0 (the size is 256). 6.1  (the size is 256 - 4*2 = 248)
	int mExpectedBarcodesCount;
	int mBinarizationBlockSize;

}PublicParameterSettings;

#pragma pack(pop)

//---------------------------------------------------------------------------
// Functions
//---------------------------------------------------------------------------

#ifdef __cplusplus
extern "C" {
#endif
	// Creates an instance of Dynamsoft Barcode Reader. 
	// @return Return an instance of Dynamsoft Barcode Reader. If failed, return NULL.
	DBR_API void*  DBR_CreateInstance();

	// Destroys an instance of Dynamsoft Barcode Reader. 
	// @param [in] hBarcode Handle of the barcode reader instance.
	DBR_API void DBR_DestroyInstance(void*  hBarcode);

	// Reads license key and activate the SDK. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszLicense The license keys.
	// @return Returns error code. Returns 0 if the function completed successfully.
	DBR_API int  DBR_InitLicense(void*  hBarcode, const char* pszLicense);

	// Set up a license server.
	// @param [in] hBarcode Handle of the barcode reader instance.
	// @param [in] pszServerUrl The license server.
	// @param [in] pszPublicKey The public key. 
	// @return  Returns error code. Return 0 if the function completed successfully.
	DBR_API int  DBR_SetLicenseServer(void* hBarcode,const char* pszServerUrl,const char* pszPublicKey);

	// Load paramter settings from JSON file. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszFilePath The settings file path.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommending length is 256. . The error message would be copy to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of allocated buffer.
	// @return Returns error code. Returns 0 if the function completed successfully.
	DBR_API int  DBR_LoadSettingsFromFile(void* hBarcode, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	// Load paramter settings from JSON string. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszFileText The settings file content.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommending length is 256. . The error message would be copy to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of allocated buffer.
	// @return Returns error code. Returns 0 if the function completed successfully.	
	DBR_API int  DBR_LoadSettings(void* hBarcode, const char* pszFileContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	// Append parameter template from a JSON file. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszFilePath The settings file path.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommending length is 256. . The error message would be copy to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of allocated buffer.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_AppendParameterTemplateFromFile(void* hBarcode, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	// Append parameter template from a JSON string. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszFileContent The settings file content.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommending length is 256. . The error message would be copy to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of allocated buffer.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_AppendParameterTemplate(void* hBarcode, const char* pszFileContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	// Get count of parameter template. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @return Returns the count of parameter template.
	DBR_API int  DBR_GetParameterTemplateCount(void* hBarcode);

	// Get paramter template name by index. 
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] iIndex The index of parameter template array.
	// @param [in/out] szNameBuffer The buffer is allocated by caller and the recommending length is 256. The template name would be copy to the buffer. 
	// @param [in] nNameBufferLen The length of allocated buffer. 
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_GetParameterTemplateName(void* hBarcode, int iIndex, char szNameBuffer[], int nNameBufferLen);

	// Decodes barcodes in the specified image file.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszFileName A string defining the file name.
	// @param [in] pszTemplateName The template name.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_DecodeFile(void*  hBarcode, const char* pszFileName, const char* pszTemplateName);
	
	// Decodes barcode from an image file in memory.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pFileBytes The image file bytes in memory.
	// @param [in] nFileSize The length of the file bytes in memory.
	// @param [in] pszTemplateName The template name.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_DecodeFileInMemory(void*  hBarcode, unsigned char* pFileBytes, int nFileSize, const char* pszTemplateName);
	
	// Decodes barcodes from the memory buffer containing image pixels in defined format.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pBufferBytes The array of bytes which contain the image data.
	// @param [in] iWidth The width of the image in pixels.
	// @param [in] iHeight The height of the image in pixels.
	// @param [in] iStride The stride of the image (also called scan width).
	// @param [in] format The image pixel format used in the image byte array.
	// @param [in] pszTemplateName The template name.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_DecodeBuffer(void*  hBarcode, unsigned char* pBufferBytes, int iWidth, int iHeight, int iStride, ImagePixelFormat format, const char* pszTemplateName);
	
	// Decodes barcode from an image file encoded as a base64 string.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] pszBase64String A base64 encoded string that represents an image.
	// @param [in] pszTemplateName The template name.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_DecodeBase64String(void*  hBarcode, const char* pszBase64String, const char* pszTemplateName);
	
	// Decodes barcode from a handle of device-independent bitmap (DIB).
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [in] hDIB Handle of the device-independent bitmap.
	// @param [in] pszTemplateName The template name.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int  DBR_DecodeDIB(void*  hBarcode, HANDLE  hDIB, const char* pszTemplateName);

	// Gets all recognized barcode results.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [out] ppResults Barcode results returned by last calling function DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB. The ppResults is allocated by SDK and should be freed by calling function DBR_FreeTextResults.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int DBR_GetAllTextResults(void* hBarcode, STextResultArray **ppResults);
	
	// Gets all localization barcode results. It contains all recognized barcodes and unrecognized barcodes.
	// @param [in] hBarcode Handle of the barcode reader instance. 
	// @param [out] ppResults Barcode results returned by last calling function DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB. The ppResults is allocated by SDK and should be freed by calling function DBR_FreeLocalizationResults.
	// @return Returns error code. Returns 0 if the function completed successfully, otherwise call DBR_GetErrorString to get detail message.
	DBR_API int DBR_GetAllLocalizationResults(void* hBarcode, SLocalizationResultArray **ppResults);

	// Frees memory allocated for text results.
	// @param [in] ppResults Text results.
	DBR_API void  DBR_FreeTextResults(STextResultArray **ppResults);

	// Frees memory allocated for localization results.
	// @param [in] ppResults Localization results.
	DBR_API void  DBR_FreeLocalizationResults(SLocalizationResultArray **ppResults);

	// Returns the error info string.
	// @param [in] iErrorCode The error code.	
	// @return The error message.	
	DBR_API const char* DBR_GetErrorString(int iErrorCode);

	// Returns the version info string for the SDK.
	// @return The version info string.
	DBR_API const char* DBR_GetVersion();

	//Gets the template settings with a struct.
	//@param [in] hBarcode Handle of the barcode reader instance. 
	//@param [in] pszTemplateName The name of the template.
	//@param [in/out] pSettings The struct of template settings. 
	DBR_API int DBR_GetTemplateSettings(void* hBarcode,const char*pszTemplateName, PublicParameterSettings *pSettings);

	//Sets the template settings with a struct.
	//@param [in] hbarcode Handle of the barcode reader instance.
	//@param [in] pszTemplateName The name of the template.
	//@param [in] pSettings The struct of template settings.
	//@param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended lenth is 256.The error message will be copied to the buffer.
	//@param [in] nErrorMsgBufferLen The length of the allocated buffer.
	DBR_API int DBR_SetTemplateSettings(void* hBarcode,const char*pszTemplateName,PublicParameterSettings *pSettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);

#ifdef __cplusplus
}
#endif

//---------------------------------------------------------------------------
// Class
//---------------------------------------------------------------------------

#ifdef __cplusplus

class BarcodeReaderInner;

// Defines a class that provides functions for working with extracting barcode data.
class DBR_API CBarcodeReader
{
private:
	BarcodeReaderInner* m_pBarcodeReader;

public:
	CBarcodeReader();
	~CBarcodeReader();

	// Reads license key and activate the SDK. 
	// @param [in] pszLicense The license keys.
	// @return Returns the error code. Returns It will return 0 if the function completesed successfully.
	int InitLicense(const char* pLicense);

	// @param [in] hBarcode Handle of the barcode reader instance.
	// @param [in] pszServerUrl The license server.
	// @param [in] pszPublicKey The public key. 
	// @return  Returns error code. Return 0 if the function completed successfully.
	int SetLicenseServer(const char* pszServerUrl,const char* pszPublicKey);

	// Loads parameter settings from a JSON file. 
	// @param [in] pszFilePath The path of the settings file.The settings file path.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommending recommended length is 256. The error message would will be copiedy to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	// @return Returns the error code. It will return 0 if the function completes successfully.
	int  LoadSettingsFromFile(const char* pszFilePath, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	// Loads parameter settings from a JSON string. 
	// @param [in] pszFileText A JSON string that represents the content of the settingsThe settings file content.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length is 256. The error message will be copied to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	// @return Returns the error code. It will return 0 if the function completes successfully.
	int  LoadSettings(const char* pszFileContent, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	// Appends the parameter template from a JSON file. 
	// @param [in] pszFilePath The path of the settings file	
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length is 256. The error message will be copied to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	// @return Returns the error code. It will return 0 if the function completes successfully.
	int  AppendParameterTemplateFromFile(const char* pszFilePath, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);
	
	// Appends the parameter template from a JSON string. 
	// @param [in] pszFileContent The settings file content.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length is 256. The error message will be copied to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	// @return Returns the error code. It will return 0 if the function completes successfully.
	int  AppendParameterTemplate(const char* pszFileContent, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	// Unload the parameter template in a specified name. 
	// @param [in] pszTemplateName The name of the template.
	// @param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length is 256. The error message will be copied to the buffer. 
	// @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	// @return Returns the error code. It will return 0 if the function completes successfully.
	//int  UnloadParameterTemplate(const char* pszTemplateName, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);


	// Gets the count of the parameter templates. 
	// @return Returns the count of parameter template.
	int  GetParameterTemplateCount();

	// Gets the parameter template name by index. 
	// @param [in] iIndex The index of the parameter template array.
	// @param [in/out] szNameBuffer The buffer is allocated by caller and the recommended length is 256. The template name will be copied to the buffer. 
	// @param [in] nNameBufferLen The length of allocated buffer. 
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  GetParameterTemplateName(int iIndex, char szNameBuffer[], int nNameBufferLen);

	// Decodes barcodes in a specified image file.
	// @param [in] pszFileName A string defining the file name.
	// @param [in] pszTemplateName The template name.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  DecodeFile(const char* pszFileName, const char* pszTemplateName = "");

	// Decodes barcodes from an image file in memory.
	// @param [in] pFileBytes The image file bytes in memory.
	// @param [in] nFileSize The length of the file bytes in memory.
	// @param [in] pszTemplateName The template name.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  DecodeFileInMemory(unsigned char* pFileBytes, int nFileSize, const char* pszTemplateName = "");

	// Decodes barcodes from the memory buffer containing image pixels in defined format.
	// @param [in] pBufferBytes The array of bytes which contain the image data.
	// @param [in] iWidth The width of the image in pixels.
	// @param [in] iHeight The height of the image in pixels.
	// @param [in] iStride The stride of the image (also called scan width).
	// @param [in] format The image pixel format used in the image byte array.
	// @param [in] pszTemplateName The template name.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  DecodeBuffer(unsigned char* pBufferBytes, int iWidth, int iHeight, int iStride, ImagePixelFormat format, const char* pszTemplateName = "");

	// Decodes barcode from an image file encoded as a base64 string.
	// @param [in] pszBase64String A base64 encoded string that represents an image.
	// @param [in] pszTemplateName The template name.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  DecodeBase64String(const char* pszBase64String, const char* pszTemplateName = "");

	// Decodes barcode from a handle of device-independent bitmap (DIB).
	// @param [in] hDIB Handle of the device-independent bitmap.
	// @param [in] pszTemplateName The template name.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int  DecodeDIB(HANDLE  hDIB, const char* pszTemplateName = "");

	// Gets all recognized barcode results.
	// @param [out] ppResults Barcode results returned by the last called function DecodeFile/DecodeFileInMemory/DecodeBuffer/DecodeBase64String/DecodeDIB. The ppResults is allocated by our SDK and should be freed by calling the function FreeTextResults.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int GetAllTextResults(STextResultArray **ppResults);

	// Gets all localization barcode results. It contains all recognized barcodes and unrecognized barcodes.
	// @param [out] ppResults Barcode results returned by the last called function DecodeFile/DecodeFileInMemory/DecodeBuffer/DecodeBase64String/DecodeDIB. The ppResults is allocated by our SDK and should be freed by calling the function FreeLocalizationResults.
	// @return Returns the error code. It will return 0 if the function completes successfully. Otherwise, please call GetErrorString to get a more detailed message.
	int GetAllLocalizationResults(SLocalizationResultArray **ppResults);

	// Frees memory allocated for text results.
	// @param [in] ppResults Text results.
	static void FreeTextResults(STextResultArray **ppResults);

	// Frees memory allocated for localization results.
	// @param [in] ppResults Localization results.
	static void FreeLocalizationResults(SLocalizationResultArray **ppResults);

	// Returns the error info string.
	// @param [in] iErrorCode The error code.	
	// @return The error message.	
	static const char* GetErrorString(int iErrorCode);

	// Returns the version info string for the SDK.
	// @return The version info string.
	static const char* GetVersion();

	//Gets the template settings with a struct.
	//@param [in] pszTemplateName The name of the template.
	//@param [in/out] pSettings The struct of template settings. 
	int GetTemplateSettings(const char* pszTemplateName,PublicParameterSettings *psettings);
	
	//Sets the template settings with a struct.
	//@param [in] pszTemplateName The name of the template.
	//@param [in] pSettings The struct of template settings.
	//@param [in/out] szErrorMsgBuffer The buffer is allocated by caller and the recommended lenth is 256.The error message will be copied to the buffer.
	//@param [in] nErrorMsgBufferLen The length of the allocated buffer.
	int SetTemplateSettings(const char* pszTemplateName,PublicParameterSettings *psettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);

private:
	CBarcodeReader(const CBarcodeReader& r);
	CBarcodeReader& operator = (const CBarcodeReader& r);

};

#endif

#endif