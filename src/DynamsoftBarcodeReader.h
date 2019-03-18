/**
*
* @mainpage
*
* @section Introduction
* Dynamsoft's Barcode Reader SDK enables you to efficiently embed barcode reading functionality in your application using just a few lines of code. This can save you from months of added development time and extra costs.
* With the Barcode Reader SDK, you can decode barcodes from various image file formats (bmp, jpg, png, gif, tiff and pdf) as well as device-independent bitmap (DIB) which has just been obtained from cameras and scanners, etc.
* The SDK has the multiple editions available include Windows, JavaScript, Moblie, Linux, Raspberry Pi and Mac. This document contains detailed API references for windows edition (both C/C++, .NET and Java).
*
* @section mp1 Barcode Reading Features
* - Reads barcodes within a specified area of a selected image.
* - Reads multiple barcodes in one image.
* - Can read blurred and damaged barcodes.
* - Detects barcode at any orientation and rotation angle.
*
* @section mp2 Supported Barcode Type
* - 1D barcodes: Code39, Code93, Code128, Codabar, ITF, EAN13, EAN8, UPCA, UPCE, INDUSTRIAL 2 OF 5.
* - 2D barcodes: QRCode, PDF417, DATAMATRIX, AZTEC.
*
* @section mp3 Barcode Reading Results
* - Barcode angle
* - Barcode type
* - Barcode count
* - Barcode data as byte array
* - Barcode value as stringF
* - Barcode bounding rectangle
* - Confidence
* - Coordinate of four corners
* - Module size
* - Page number
* - Terminated stage
*
* @section mp4 Supported Image Source Types
* - Bmp, jpg, png, tiff and pdf image files; multi-page tiff and pdf are also supported
* - Windows DIB and .NET bitmap
* - Black/white, grayscale or color
*
* @section mp5 Contents
* @subsection sbs1 .Net APIs
*   - Class
*		-# [Barcode Reader](@ref Dynamsoft.Barcode.BarcodeReader)
*		-# [Barcode Reader Exception](@ref Dynamsoft.Barcode.BarcodeReaderException)
*		-# [Text Result](@ref Dynamsoft.Barcode.TextResult)
*		-# [Extended Result](@ref Dynamsoft.Barcode.ExtendedResult)
*		-# [Localization Result](@ref Dynamsoft.Barcode.LocalizationResult)
*
*	- Enumerations
*		-# [Enum Barcode Format](@ref Dynamsoft.Barcode.EnumBarcodeFormat)
*		-# [Enum Conflict Mode](@ref Dynamsoft.Barcode.EnumConflictMode)
*		-# [Enum Error Code](@ref Dynamsoft.Barcode.EnumErrorCode)
*		-# [Enum Image Pixel Format](@ref Dynamsoft.Barcode.EnumImagePixelFormat)
*		-# [Enum Result Type](@ref Dynamsoft.Barcode.EnumResultType)
*		-# [Enum Terminate Stage](@ref Dynamsoft.Barcode.EnumTerminateStage)
*
*	- Struct
*		-# [Public Runtime Settings](@ref PublicRuntimeSettings)
*
* @subsection sbs2 C/C++ APIs
*	- [Error Code](@ref ErrorCode)
*
*	- Enumerations
*		-# [Barcode Format](@ref BarcodeFormat)
*		-# [Conflict Mode](@ref ConflictMode)
*		-# [Image Pixel Format](@ref ImagePixelFormat)
*		-# [Result Type](@ref ResultType)
*		-# [Terminate Stage](@ref TerminateStage)
*
*	- Struct
*		-# [Extended Result](@ref SExtendedResult)
*		-# [Localization Result](@ref SLocalizationResult)
*		-# [Localization Result Array](@ref SLocalizationResultArray)
*		-# [Text Result](@ref STextResult)
*		-# [Text Result Array](@ref STextResultArray)
*		-# [Public Runtime Settings](@ref PublicParametersSetting)
*
*	- [C Functions](@ref CFunctions)
*
*	- [CBarcodeReader Class](@ref CBarcodeReader)
*
* @subsection sbs3 JAVA APIs
*	- Class
*		-# [Public Runtime Settings](@ref com.dynamsoft.barcode.PublicRuntimeSettings)
*		-# [Barcode Reader](@ref com.dynamsoft.barcode.BarcodeReader)
*		-# [Barcode Reader Exception](@ref com.dynamsoft.barcode.BarcodeReaderException)
*		-# [Extended Result](@ref com.dynamsoft.barcode.ExtendedResult)
*		-# [Localization Result](@ref com.dynamsoft.barcode.LocalizationResult)
*		-# [Point](@ref com.dynamsoft.barcode.Point)
*		-# [Text Result](@ref com.dynamsoft.barcode.TextResult)
*
*	- Enumerations
*		-# [Enum Barcode Format](@ref com.dynamsoft.barcode.EnumBarcodeFormat)
*		-# [Enum Conflict Mode](@ref com.dynamsoft.barcode.EnumConflictMode)
*		-# [Enum Error Code](@ref com.dynamsoft.barcode.EnumErrorCode)
*		-# [Enum Image Pixel Format](@ref com.dynamsoft.barcode.EnumImagePixelFormat)
*		-# [Enum Result Type](@ref com.dynamsoft.barcode.EnumResultType)
*		-# [Enum Terminate Stage](@ref com.dynamsoft.barcode.EnumTerminateStage)
*
*/


/*
*	@file DynamsoftBarcodeReader.h
*	
*	Dynamsoft Barcode Reader C/C++ API header file.
*	Copyright 2018 Dynamsoft Corporation. All rights reserved.
*	
*	@author Dynamsoft
*	@date 19/09/2018
*/

#ifndef __DYNAMSOFT_BARCODE_READER_H__
#define __DYNAMSOFT_BARCODE_READER_H__

#if !defined(_WIN32) && !defined(_WIN64)
#define DBR_API __attribute__((visibility("default")))
#ifdef __APPLE__
#else
typedef signed char BOOL;
#endif
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

/**
* @defgroup CandCPlus C/C++ APIs
* @{
* Dynamsoft Barcode Reaeder 6.5 - C/C++ APIs Description.
*/
#define DBR_VERSION                  "6.5.1225"

/**
 * @defgroup ErrorCode ErrorCode
 * @{
 */

#define DBR_OK									 0 
 /**< Successful. */

#define DBRERR_UNKNOWN						-10000 
 /**< Unknown error. */

#define DBRERR_NO_MEMORY					-10001 
 /**< Not enough memory to perform the operation. */

#define DBRERR_NULL_POINTER					-10002 
 /**< Null pointer. */

#define DBRERR_LICENSE_INVALID				-10003 
 /**< The license is invalid. */

#define DBRERR_LICENSE_EXPIRED				-10004 
 /**< The license has expired. */

#define DBRERR_FILE_NOT_FOUND				-10005 
 /**< The file is not found. */

#define DBRERR_FILETYPE_NOT_SUPPORTED		-10006 
 /**< The file type is not supported. */

#define DBRERR_BPP_NOT_SUPPORTED			-10007 
 /**< The BPP(Bits per pixel) is not supported. */

#define DBRERR_INDEX_INVALID				-10008 
 /**< The index is invalid. */

#define DBRERR_BARCODE_FORMAT_INVALID		-10009 
 /**< The barcode format is invalid. */

#define DBRERR_CUSTOM_REGION_INVALID		-10010 
 /**< The input region value parameter is invalid. */

#define DBRERR_MAX_BARCODE_NUMBER_INVALID	-10011 
 /**< The maximum barcode number is invalid. */

#define DBRERR_IMAGE_READ_FAILED			-10012
 /**< Failed to read the image. */

#define DBRERR_TIFF_READ_FAILED				-10013
 /**< Failed to read the TIFF image. */

#define DBRERR_QR_LICENSE_INVALID			-10016
 /**< The QR Code license is invalid. */

#define DBRERR_1D_LICENSE_INVALID			-10017
 /**< The 1D Barcode license is invalid. */

#define DBRERR_DIB_BUFFER_INVALID			-10018
 /**< The DIB(Device-independent bitmaps) buffer is invalid. */

#define DBRERR_PDF417_LICENSE_INVALID		-10019
 /**< The PDF417 license is invalid. */

#define DBRERR_DATAMATRIX_LICENSE_INVALID	-10020
 /**< The DATAMATRIX license is invalid. */

#define DBRERR_PDF_READ_FAILED				-10021
 /**< Failed to read the PDF file. */

#define	DBRERR_PDF_DLL_MISSING				-10022
 /**< The PDF DLL is missing. */

#define DBRERR_PAGE_NUMBER_INVALID			-10023
 /**< The page number is invalid. */

#define DBRERR_CUSTOM_SIZE_INVALID			-10024
 /**< The custom size is invalid. */

#define DBRERR_CUSTOM_MODULESIZE_INVALID	-10025
 /**< The custom module size is invalid. */

#define DBRERR_RECOGNITION_TIMEOUT			-10026
 /**< Recognition timeout. */

#define DBRERR_JSON_PARSE_FAILED			-10030
 /**< Failed to parse json string. */

#define DBRERR_JSON_TYPE_INVALID			-10031
 /**< The value type is invalid. */

#define DBRERR_JSON_KEY_INVALID				-10032
 /**< The key is invalid. */

#define DBRERR_JSON_VALUE_INVALID			-10033
 /**< The value is invalid or out of range. */

#define DBRERR_JSON_NAME_KEY_MISSING		-10034
 /**< The mandatory key "Name" is missing. */

#define DBRERR_JSON_NAME_VALUE_DUPLICATED	-10035
 /**< The value of the key "Name" is duplicated. */

#define DBRERR_TEMPLATE_NAME_INVALID		-10036
 /**< The template name is invalid. */

#define DBRERR_JSON_NAME_REFERENCE_INVALID	-10037
 /**< The name reference is invalid. */

#define DBRERR_PARAMETER_VALUE_INVALID      -10038
 /**<The parameter value is invalid or out of range. */

#define DBRERR_DOMAIN_NOT_MATCHED           -10039
 /**<The domain of your current site does not match the domain bound in the current product key. */

#define DBRERR_RESERVEDINFO_NOT_MATCHED     -10040 
 /**<The reserved info does not match the reserved info bound in the current product key. */

#define DBRERR_AZTEC_LICENSE_INVALID        -10041 
/**< The AZTEC license is invalid. */

#define	DBRERR_LICENSE_DLL_MISSING		    -10042
/**< The License DLL is missing. */

#define DBRERR_LICENSEKEY_NOT_MATCHED       -10043
/**< The license key is not match the license content. */

#define DBRERR_REQUESTED_FAILED             -10044
/**< Failed to request the license content. */

#define DBRERR_LICENSE_INIT_FAILED          -10045
/**< Failed to init the license. */

/**
 * @}
 */

/**
* @defgroup Enum Enumerations
* @{
*/

/**
 * @enum BarcodeFormat
 * 
 * Describes the type of the barcode. All the formats can be combined, such as BF_CODE_39 | BF_CODE_128.
 */
typedef enum
{
	BF_All = 503317503,
	/**< All supported formats */
	
	BF_OneD = 0x3FF,
	/**< One-D */
	
	BF_CODE_39 = 0x1,
	/**< Code 39 */
	
	BF_CODE_128 = 0x2,
	/**< Code 128 */
	
	BF_CODE_93 = 0x4,
	/**< Code 93 */
	
	BF_CODABAR = 0x8,
	/**< Codabar */
	
	BF_ITF = 0x10,
	/**< ITF */
	
	BF_EAN_13 = 0x20,
	/**< EAN-13 */
	
	BF_EAN_8 = 0x40,
	/**< EAN-8 */
	
	BF_UPC_A = 0x80,
	/**< UPC-A */
	
	BF_UPC_E = 0x100,
	/**< UPC-E */
	
	BF_INDUSTRIAL_25 = 0x200,
	/**< Industrial 2 of 5 */
	
	BF_PDF417 = 0x2000000,
	/**< PDF417 */
	
	BF_QR_CODE = 0x4000000,
	/**< QRCode */
	
	BF_DATAMATRIX = 0x8000000,
	/**< DataMatrix */
	
	BF_AZTEC = 0x10000000
	/**< AZTEC */
}BarcodeFormat;



/** Describes the image pixel format. */
typedef enum
{
	IPF_Binary,	
	/**< 0:Black, 1:White */
	IPF_BinaryInverted,			
	/**< 0:White, 1:Black */
	IPF_GrayScaled,	
	/**< 8bit gray */	
	IPF_NV21,	
	/**< NV21 */		
	IPF_RGB_565,
	/**< 16bit */
	IPF_RGB_555,		
	/**< 16bit */
	IPF_RGB_888,		
	/**< 24bit */
	IPF_ARGB_8888		
	/**< 32bit */		
}ImagePixelFormat;



/** Describes the extended result type. */
typedef enum
{
	EDT_StandardText,
	/**< Specifies the standard text. This means the barcode value. */
	
	EDT_RawText,
	/**< Specifies the raw text. This means the text that includes start/stop characters, check digits, etc. */
	
	EDT_CandidateText,
	/**< Specifies all the candidate text. This means all the standard text results decoded from the barcode. */
	
	EDT_PartialText
	/**< Specifies the partial Text. This means part of the text result decoded from the barcode. */
}ResultType;



/** Describes the stage when the results are returned. */
typedef enum
{
	ETS_Prelocalized,
	/**< Prelocalized */
	
	ETS_Localized,
	/**< Localized */
	
	ETS_Recognized
	/**< Recognized */
}TerminateStage;


/** Describes the options for setting parameters value. Detailed info can be found in PublicRuntimeSettings. */
typedef enum
{
	ECM_Ignore = 1,
	/**< Ignore new settings and inherit from previous settings. */

	ECM_Overwrite = 2
	/**< overwrite and replace by new settings. */
}ConflictMode;

/**
 * @}
 */

//---------------------------------------------------------------------------
// Structures
//---------------------------------------------------------------------------

#pragma pack(push)
#pragma pack(1)

/**
* @defgroup Struct Struct
* @{
* @defgroup SExtendedResult SExtendedResult
* @{
*/
/**
 * Stores the extended result including the format, the bytes, etc.
 * 
 */

typedef struct tagSExtendedResult
{
	ResultType emResultType;
	/**< Extended result type */

	BarcodeFormat emBarcodeFormat;
	/**< Barcode type */
	
	const char* pszBarcodeFormatString;
	/**< Barcode type as string */

	int iConfidence;
	/**< The confidence of the result */

	unsigned char* pBytes;
	/**< The content in a byte array */

	int nBytesLength;
	/**< The length of the byte array */
}SExtendedResult, *PSExtendedResult;
/**
* @}
* @defgroup SLocalizationResult SLocalizationResult
* @{
*/


/**
 * Stores the localization result including the boundary, the angle, the page number, the region
 * name, etc.
 *
 */

typedef struct tagSLocalizationResult
{
	TerminateStage emTerminateStage;
	/**< The stage of localization result. */
	
	BarcodeFormat emBarcodeFormat;
	/**< Barcode type. */
	
	const char* pszBarcodeFormatString;
	/**< Barcode type as string */

	int iX1;
	/**< The X coordinate of the left-most point */
	
	int iY1;
	/**< The Y coordinate of the left-most point */
	
	int iX2;
	/**< The X coordinate of the second point in a clockwise direction */
	
	int iY2;
	/**< The Y coordinate of the second point in a clockwise direction */
	
	int iX3;
	/**< The X coordinate of the third point in a clockwise direction */
	
	int iY3;
	/**< The Y coordinate of the third point in a clockwise direction */
	
	int iX4;
	/**< The X coordinate of the fourth point in a clockwise direction */
	
	int iY4;
	/**< The Y coordinate of the fourth point in a clockwise direction */
	
	int iAngle;
	/**< The angle of a barcode. Values range from 0 to 360. */

	int iModuleSize;
	/**< The barcode module size (the minimum bar width in pixel) */
	
	int iPageNumber;
	/**< The page number the barcode located in. The index is 0-based. */

	const char* pszRegionName;
	/**< The region name the barcode located in. */

	const char* pszDocumentName;
	/**< The document name. */

	int nResultsCount;
	/**< The total extended result count */

	PSExtendedResult* ppResults;
	/**< The extended result array */
}SLocalizationResult, *PSLocalizationResult;
/**
* @}
* @defgroup SLocalizationResultArray SLocalizationResultArray
* @{
*/


/**
 * Stores the localization result count and result array.
 */

typedef struct tagSLocalizationResultArray
{
	int nResultsCount;
	/**< The total localization result count */

	PSLocalizationResult *ppResults;
	/**< The localization result array */
}SLocalizationResultArray;
/**
* @}
* @defgroup STextResult STextResult
* @{
*/

/**
 * Stores the text result including the format, the text, the bytes, the localization result etc.
 *
 */

typedef struct tagSTextResult
{

	BarcodeFormat emBarcodeFormat;
	/**< The barcode format */

	const char* pszBarcodeFormatString;
	/**< Barcode type as string */
	
	const char* pszBarcodeText;
	/**< The barcode text, ends by '\0' */

	unsigned char* pBarcodeBytes;
	/**< The barcode content in a byte array */
	
	int nBarcodeBytesLength;
	/**< The length of the byte array */

	SLocalizationResult* pLocalizationResult;
	/**< The corresponding localization result */
}STextResult, *PSTextResult;
/**
* @}
* @defgroup STextResultArray STextResultArray
* @{
*/


/**
 * Stores the text result count and result in an array.
 *
 */

typedef struct tagSTextResultArray
{
	int nResultsCount;
	/**< The total text result count */

	PSTextResult *ppResults;
	/**< The text result array */
}STextResultArray;
/**
* @}
*/


/**
* @defgroup PublicParametersSetting PublicRuntimeSettings
* @{
*/

/** Whether to enable region predetection mode. */
typedef enum 
{
    RPM_Disable = 1,
	/**< Disable region pre-detection */

    RPM_Enable = 2,
	/**< Enable region pre-detection */
}RegionPredetectionMode;


/** Whether to enable text filter mode. */
typedef enum 
{
    TFM_Disable = 1,
	/**< Disable text filter */

    TFM_Enable = 2,
	/**< Enable text filter */
}TextFilterMode;


/** Values that represent barcode invert modes */
typedef enum 
{
    BIM_DarkOnLight,
	/**< Dark barcode region on light background. */

    BIM_LightOnDark,
	/**< Light barcode region on dark background. */
}BarcodeInvertMode;


/** Values that represent colour image convert modes */
typedef enum 
{
	CICM_Auto,
	/**< Process input image as its original colour space. */
	
	CICM_Grayscale
	/**< Process input image with gray scale. */
}ColourImageConvertMode;



/**
 * @defgroup camptiableStruct PublicRuntimeSettings Struct
 * @{
 */
 

/**
 *
 * Defines a struct to configure the barcode reading runtime settings. 
 * These settings are used to control the barcode recognition process such as which barcode types are to be decoded.
 * 
 * The value of public parameters in runtime settings need to be set according to a specified rules if there are conflicts between different templates. The rules will been shown below:
 * 
 * @par Parameters Assignment Rules:
 * - Set as maximal value: mTimeout, mPDFRasterDPI, mMaxAlgorithmThreadCount, mDeblurLevel, mAntiDamageLevel, mMaxDimOfFullImageAsBarcodeZone, mMaxBarcodesCount, mScaleDownThreshold, mExpectedBarcodesCount.  
 *   
 * - Set as union (merged or sum): mBarcodeFormatIds.  
 *   
 * - Based on ConflictMode (ignore or overwrite): mTextFilterMode, mRegionPredetectionMode, mLocalizationAlgorithmPriority, mTextureDetectionSensitivity, mBarcodeInvertMode, mGrayEqualizationSensitivity, mEnableFillBinaryVacancy, mColourImageConvertMode, mBinarizationBlockSize.
 * 
 * 
 * @par References
 * More information about public parameters and template file can be found in file DBR_Developer's_Guide.pdf.
 *
 */
typedef struct tagPublicRuntimeSettings
{	 
    int mTimeout;
	/**< Sets the maximum amount of time (in milliseconds) it should spend searching for a barcode per page. It does not include the time taken to load an image (Tiff, PNG, etc.) from disk into memory. 
	 *
	 * @par Value range:
	 * 	    [0,7ffffff]
	 * @par Default value:
	 * 	    10000
	 * @par Remarks:
	 *	    If you want to stop reading barcodes after a specified amount of time, you can use this parameter to set a timeout.
	 */


    int mPDFRasterDPI;
	/**< Sets the output image resolution. When you are trying to decode a PDF file using the DecodeFile method, the library will convert the PDF file to image(s) first, then perform barcode recognition.
	 * 
	 * @par Value range:
	 * 		[100,600]
	 * @par Default value:
	 * 		300
	 * @par Remarks:
	 *		To ensure your barcodes in the PDF files are readable, please set the resolution to at least 300 dpi.
	 */


    TextFilterMode mTextFilterMode;
	/**< Sets whether to filter text before barcode localization.
	 *  
	 * @par Value range:
	 * 		TFM_Disable, TFM_Enable
	 * @par Default value:
	 *		TFM_Enable
	 * @par Remarks:
	 *		If the barcode image contains a lot of text, you can set this property to "TFM_Enable" to speed up the localization process.
	 * @sa TextFilterMode
	 *
	 */

		
    RegionPredetectionMode mRegionPredetectionMode;
	/**< Sets whether to pre-detect barcode regions before accurate localization. 
	 *
	 * @par Value range:
	 * 		RPM_Disable, RPM_Enable
	 * @par Default value:
	 * 		RPM_Disable
	 * @par Remarks:
	 *		If the image is large and the barcode on the image is very small, it is recommended to set this property to "RPM_Enable" to speed up the localization process and recognition accuracy.
	 *		If this property is set to "RPM_Enable", also set mColourImageConvertMode to "CICM_Auto" and mScaleDownThreshold to 0x7fffffff for best performance.
	 * @sa RegionPredetectionMode mColourImageConvertMode mScaleDownThreshold
	 */


    char mLocalizationAlgorithmPriority[64];
	/**< Sets the priority of localization algorithms to decide the ordering of the following four localization algorithms.
	 *
	 * @par Default values:
	 * 		""
	 * @par Optional localization algorithms:
	 * 		"ConnectedBlocks", "Statistics", "Lines", "FullImageAsBarcodeZone"
	 * @par Remarks:
	 * 		- Default value: The library will automatically use optimized localization priority, i.e. ConnectedBlocks -> Statistics -> Lines -> FullImageAsBarcodeZone, which is also the recommended order.    
	 * 	
	 * 		- ConnectedBlocks: Localizes barcodes by searching connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlocks to the highest priority.    
	 * 	
	 * 		- Statistics: Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix.    
	 * 	
	 * 		- Lines: Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes.     
	 * 	
	 * 		- FullImageAsBarcodeZone: Disables localization. In this mode, it will directly localize barcodes on the full image without localization. If there is nothing other than the barcode in the image, it is recommended to use this mode. 
	 * 		
	 */


    int mBarcodeFormatIds;
	/**< Sets which types of barcode to read. Barcode types can be combined. Notice that one barcode reader can support more than one barcode format, i.e. the barcode format can be combined like BF_CODE_39 | BF_CODE_128.
	 * 
	 * @par Remarks:
	 *		If you already know the barcode type(s) before performing barcode reading, specifying the barcode type(s) to be read will speed up the recognition process.
	 * @sa BarcodeFormat
	 */


    int mMaxAlgorithmThreadCount;
	/**< Sets how many image processing algorithm threads will be used to decode barcodes.
	 * 
	 * @par Value range:
	 * 		[1,4]
	 * @par Default value:
	 * 		4
	 * @par Remarks:
	 *		By default, our library concurrently runs four different threads used for decoding barcodes. For some devices (e.g. Raspberry Pi) that only uses one core, you can set it to 1 for best speed.
	 *		If you create BarcodeReader instances in multiple threads, please set this property to 1 in case our algorithm threads affect your application.	
	 */


    int mTextureDetectionSensitivity;
	/**< Sets the value of sensitivity for texture detection. 
	 * 
	 * @par Value range:
	 * 		[0,9]
	 * @par Default value:
	 * 		5
	 * @par Remarks:
	 *		If you have an image with texture on it , you can set this property to a larger value. If texture is detected, we will smooth the image to help localize the barcode.
	 *		If there is no texture on the image, the value should be set to 0 to disable texture detection; If there is texture on the image, you can set this value to 9 to activate texture detection.
	 */


    int mDeblurLevel;
	/**< Sets the degree of blurriness of the barcode.
	 *
     * @par Value range:
     * 		[0,9]
     * @par Default value:
     * 		9
	 * @par Remarks:
	 *		If you have a blurry image, you can set this property to a larger value. The higher value you set, the library will spend more time decoding images which may slow down the overall recognition process.
	 */

	

    int mAntiDamageLevel;
	/**< Sets the degree of anti-damage of the barcode, which decides how many localization algorithms will be used for locating the barcode area.
	 *
     * @par Value range:
     * 		[0,9]
     * @par Default Value:
     * 		9
	 * @par Remarks:
	 * 		- 0 <= N <= 3: one localization algorithm will be used.  
	 * 		
	 * 		- 4 <= N <= 5: two localization algorithms will be used.   
	 * 	
	 * 		- 6 <= N <= 7: three localization algorithms will be used.
	 * 	
	 * 		- 8 <= N <= 9: four(i.e. all) localization algorithms will be used. 
	 *
	 * 		If you have a damaged image, you can set this property to a larger value and use it with ExpectedBarcodesCount. 
	 *		If the ExpectedBarcodesCount is set to 0 or 1, it's suggested to set AntiDamageLevel to 9 to ensure best decoding efficiency; otherwise, the value of AntiDamageLevel is suggested to be set to 7. For more information about our localization algorithms, please check AlgorithmPriority. 
	 *
	 * @sa mExpectedBarcodesCount
	 */



    int mMaxDimOfFullImageAsBarcodeZone;
	/**< Sets the maximum image dimension (in pixels) to localize barcode on the full image. If the image dimension is smaller than the given value, the library will localize barcode on the full image. Otherwise, "FullImageAsBarcodeZone" mode will not be enabled.
	 * 
	 * @par Value range:
	 * 		[262144,0x7fffffff]
	 * @par Default value:
	 * 		262144
	 * @par Remarks:
	 *		If you have an image whose content is barcode only, you can set this property to a smaller value to decode the whole image. 
	 *		If the "FullImageAsBarcodeZone" mode is enabled, the barcode result will be more accurate but will cost more time.
	 * @sa mLocalizationAlgorithmPriority
	 */



    int mMaxBarcodesCount;
	/**< Sets the maximum number of barcodes to read. This will limit the number of barcodes returned by library.
	 * 
	 * @par Value range:
	 * 		[1,0x7fffffff]
	 * @par Default value:
	 * 		0x7fffffff
	 * @par Remarks:
	 *		If you want to limit the numbers of barcodes, you can set it to the corresponding value. It will stop localization and decoding once the maximum number is reached.
	 */

	 

    BarcodeInvertMode mBarcodeInvertMode;
	/**< Sets the barcode invert mode which decides whether to invert colour before binarization. 
	 *
     * @par Value range:
     * 		BIM_DarkOnLight, BIM_LightOnDark
     * @par Default value:
     * 		BIM_DarkOnLight
	 * @par Remarks:
	 *		This mode is designed to fit the scenarios with a light barcode located on a dark background. For example, a white QR on a sheet of black paper. 
	 *		If the value is BIM_DarkOnLight, it will work better for dark barcodes on a light background; If the value is BIM_LightOnDark, it will work better for light barcodes on a dark background. 
     * @sa BarcodeInvertMode
	 */



    int mScaleDownThreshold;
	/**< Sets the threshold value an image can be scaled down to. If the shorter edge size is larger than the given value, the library will calculate the required height and width of the barcode image and shrink the image to that size before localization. Otherwise, it will perform barcode localization on the original image.
	 *
	 * @par Value range:
	 * 		[512,0x7fffffff]
	 * @par Default value:
	 * 		2300
	 * @par Remarks:
	 *		If you have an image whose shorter edge size is larger than the given value and the barcode is a small part on it, you can set this value to be larger than the shorter edge of this image.
	 *		If you have an image whose shorter edge size is larger than the given value and the barcode is clear and big, you can set this value to a smaller one than the default value.
	 */



    int mGrayEqualizationSensitivity;
	/**< Sets the sensitivity used for gray equalization. May cause adverse effect on images with a high level ofcontrast. The higher the value, the more likely gray equalization will be activated.
	 *
	 * @par Value range:
	 * 		[0,9]
	 * @par Default value:
	 * 		0
	 * @par Remarks:
	 *		If you have an image with a low level of contrast,  you can set the property to a larger value. If the value is set to 0, gray equalization will be disabled. If the value is set to 9, gray equalization will be activated.
	 *		For better accuracy for images with low camparison, set this property to 9. 
     */



    int mEnableFillBinaryVacancy;
	/**< Sets whether to enable fill binary vacancy. 
	 *
	 * @par Value range:
	 * 		0, 1 (0 - disable, 1 - enable)
	 * @par Default value:
	 * 		1
	 * @par Remarks:
	 *		For barcodes with a large module size there might be a vacant area in the position detection pattern after binarization which may result in a decoding failure. Setting this to true will fill in the vacant area with black and may help to decode it successfully.
	 *		Better accuracy for images with a large module size. 
	 */		



    ColourImageConvertMode mColourImageConvertMode;
	/**< Sets whether to convert colour images to grayscale before processing.
	 *
	 * @par Value range:
	 * 		CICM_Auto, CICM_Grayscale
	 * @par Default value:
	 * 		CICM_Auto
	 * @par Remarks:
	 *		If you need to decode the barcode in the region pre-detection mode, it works better with the value CICM_Auto. There are no effects to the results. It will pass the original image for if you set it to CICM_Auto and the gray-scale image if you set it otherwise. 
	 * @sa ColourImageConvertMode 
	 */



	int mExpectedBarcodesCount;
	/**< Sets the expected number of barcodes to read for each image (or each region of the image if you specified barcode regions).
	 * 
	 * @par Value range:
	 * 		[0,0x7fffffff]
	 * @par Default value:
	 * 		0
	 * @par Remarks:
	 * 		- 0: means Unknown and it will find at least one barcode.  
	 * 		
	 * 		- 1: try to find one barcode. If one barcode is found, the library will stop the localization process and perform barcode decoding.    
	 * 	
	 * 		- n: try to find n barcodes. If the library only finds m (m<n) barcode, it will try different algorithms till n barcodes are found or all algorithms are used.   
	 *
	 * 		The value of ExpectedBarcodesCount must be less than or equal to the value of MaxBarcodesCount. To ensure the best performance, the value of AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	 *		When AntiDamageLevel is larger than 7, the bigger ExpectedBarcodesCount you set, the more localization algorithms will be used which leads to a higher accuracy with slower performance. 
	 * @sa mMaxBarcodesCount mAntiDamageLevel
     */



	int mBinarizationBlockSize;
	/**< Sets the block size for the process of binarization. Block size refers to the size of a pixel neighborhood used to calculate a threshold value for the pixel.
	 * 
	 * @par Value range:
	 * 		[0,1000]
	 * @par Default:
	 * 		0
	 * @par Remarks:
	 * 		- 0: the block size used for binarization will be set to a value which is calculated automatically.
	 * 		
	 * 		- N:    
	 * 		 - 1 <= N <= 3: the block size used for binarization will be set to 3.  
	 * 		 - N > 3: the block size used for binarization will be set to N.
	 *
	 *		An appropriate value for mBinarizationBlockSize can help generate a high quality binary image to increase the accuracy of barcode localization. 
	 */	


	char mReserved[248];
	/**< Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.*/

}PublicRuntimeSettings;


/**
 * This struct used for ensuring compatibility with earlier versions. It is functionally equivalent to PublicRuntimeSettings. 
 * 
 * @deprecated tagPublicParameterSettings PublicParameterSettings 
 * 
 * @sa tagPublicRuntimeSettings PublicRuntimeSettings
 *
 */
typedef struct tagPublicParameterSettings
{
	char mName[32];
	/**< Stores the name of the struct, which is mainly help users to distinguish different version rather than practical use in the library.
	* @deprecated mName
	*
	*/

	int mTimeout;
	/**< Sets the maximum amount of time (in milliseconds) it should spend searching for a barcode per page. It does not include the time taken to load an image (Tiff, PNG, etc.) from disk into memory.
	*
	* @par Value range:
	* 	    [0,7ffffff]
	* @par Default value:
	* 	    10000
	* @par Remarks:
	*	    If you want to stop reading barcodes after a specified amount of time, you can use this parameter to set a timeout.
	*/


	int mPDFRasterDPI;
	/**< Sets the output image resolution. When you are trying to decode a PDF file using the DecodeFile method, the library will convert the PDF file to image(s) first, then perform barcode recognition.
	*
	* @par Value range:
	* 		[100,600]
	* @par Default value:
	* 		300
	* @par Remarks:
	*		To ensure your barcodes in the PDF files are readable, please set the resolution to at least 300 dpi.
	*/


	TextFilterMode mTextFilterMode;
	/**< Sets whether to filter text before barcode localization.
	*
	* @par Value range:
	* 		TFM_Disable, TFM_Enable
	* @par Default value:
	*		TFM_Enable
	* @par Remarks:
	*		If the barcode image contains a lot of text, you can set this property to "TFM_Enable" to speed up the localization process.
	* @sa TextFilterMode
	*
	*/


	RegionPredetectionMode mRegionPredetectionMode;
	/**< Sets whether to pre-detect barcode regions before accurate localization.
	*
	* @par Value range:
	* 		RPM_Disable, RPM_Enable
	* @par Default value:
	* 		RPM_Disable
	* @par Remarks:
	*		If the image is large and the barcode on the image is very small, it is recommended to set this property to "RPM_Enable" to speed up the localization process and recognition accuracy.
	*		If this property is set to "RPM_Enable", also set mColourImageConvertMode to "CICM_Auto" and mScaleDownThreshold to 0x7fffffff for best performance.
	* @sa RegionPredetectionMode mColourImageConvertMode mScaleDownThreshold
	*/


	char mLocalizationAlgorithmPriority[64];
	/**< Sets the priority of localization algorithms to decide the ordering of the following four localization algorithms.
	*
	* @par Default values:
	* 		""
	* @par Optional localization algorithms:
	* 		"ConnectedBlocks", "Statistics", "Lines", "FullImageAsBarcodeZone"
	* @par Remarks:
	* 		- Default value: The library will automatically use optimized localization priority, i.e. ConnectedBlocks -> Statistics -> Lines -> FullImageAsBarcodeZone, which is also the recommended order.
	*
	* 		- ConnectedBlocks: Localizes barcodes by searching connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlocks to the highest priority.
	*
	* 		- Statistics: Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix.
	*
	* 		- Lines: Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes.
	*
	* 		- FullImageAsBarcodeZone: Disables localization. In this mode, it will directly localize barcodes on the full image without localization. If there is nothing other than the barcode in the image, it is recommended to use this mode.
	*
	*/


	int mBarcodeFormatIds;
	/**< Sets which types of barcode to read. Barcode types can be combined. Notice that one barcode reader can support more than one barcode format, i.e. the barcode format can be combined like BF_CODE_39 | BF_CODE_128.
	*
	* @par Remarks:
	*		If you already know the barcode type(s) before performing barcode reading, specifying the barcode type(s) to be read will speed up the recognition process.
	* @sa BarcodeFormat
	*/


	int mMaxAlgorithmThreadCount;
	/**< Sets how many image processing algorithm threads will be used to decode barcodes.
	*
	* @par Value range:
	* 		[1,4]
	* @par Default value:
	* 		4
	* @par Remarks:
	*		By default, our library concurrently runs four different threads used for decoding barcodes. For some devices (e.g. Raspberry Pi) that only uses one core, you can set it to 1 for best speed.
	*		If you create BarcodeReader instances in multiple threads, please set this property to 1 in case our algorithm threads affect your application.
	*/


	int mTextureDetectionSensitivity;
	/**< Sets the value of sensitivity for texture detection.
	*
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		5
	* @par Remarks:
	*		If you have an image with texture on it , you can set this property to a larger value. If texture is detected, we will smooth the image to help localize the barcode.
	*		If there is no texture on the image, the value should be set to 0 to disable texture detection; If there is texture on the image, you can set this value to 9 to activate texture detection.
	*/


	int mDeblurLevel;
	/**< Sets the degree of blurriness of the barcode.
	*
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		9
	* @par Remarks:
	*		If you have a blurry image, you can set this property to a larger value. The higher value you set, the library will spend more time decoding images which may slow down the overall recognition process.
	*/



	int mAntiDamageLevel;
	/**< Sets the degree of anti-damage of the barcode, which decides how many localization algorithms will be used for locating the barcode area.
	*
	* @par Value range:
	* 		[0,9]
	* @par Default Value:
	* 		9
	* @par Remarks:
	* 		- 0 <= N <= 3: one localization algorithm will be used.
	*
	* 		- 4 <= N <= 5: two localization algorithms will be used.
	*
	* 		- 6 <= N <= 7: three localization algorithms will be used.
	*
	* 		- 8 <= N <= 9: four(i.e. all) localization algorithms will be used.
	*
	* 		If you have a damaged image, you can set this property to a larger value and use it with ExpectedBarcodesCount.
	*		If the ExpectedBarcodesCount is set to 0 or 1, it's suggested to set AntiDamageLevel to 9 to ensure best decoding efficiency; otherwise, the value of AntiDamageLevel is suggested to be set to 7. For more information about our localization algorithms, please check AlgorithmPriority.
	*
	* @sa mExpectedBarcodesCount
	*/



	int mMaxDimOfFullImageAsBarcodeZone;
	/**< Sets the maximum image dimension (in pixels) to localize barcode on the full image. If the image dimension is smaller than the given value, the library will localize barcode on the full image. Otherwise, "FullImageAsBarcodeZone" mode will not be enabled.
	*
	* @par Value range:
	* 		[262144,0x7fffffff]
	* @par Default value:
	* 		262144
	* @par Remarks:
	*		If you have an image whose content is barcode only, you can set this property to a smaller value to decode the whole image.
	*		If the "FullImageAsBarcodeZone" mode is enabled, the barcode result will be more accurate but will cost more time.
	* @sa mLocalizationAlgorithmPriority
	*/



	int mMaxBarcodesCount;
	/**< Sets the maximum number of barcodes to read. This will limit the number of barcodes returned by library.
	*
	* @par Value range:
	* 		[1,0x7fffffff]
	* @par Default value:
	* 		0x7fffffff
	* @par Remarks:
	*		If you want to limit the numbers of barcodes, you can set it to the corresponding value. It will stop localization and decoding once the maximum number is reached.
	*/



	BarcodeInvertMode mBarcodeInvertMode;
	/**< Sets the barcode invert mode which decides whether to invert colour before binarization.
	*
	* @par Value range:
	* 		BIM_DarkOnLight, BIM_LightOnDark
	* @par Default value:
	* 		BIM_DarkOnLight
	* @par Remarks:
	*		This mode is designed to fit the scenarios with a light barcode located on a dark background. For example, a white QR on a sheet of black paper.
	*		If the value is BIM_DarkOnLight, it will work better for dark barcodes on a light background; If the value is BIM_LightOnDark, it will work better for light barcodes on a dark background.
	* @sa BarcodeInvertMode
	*/



	int mScaleDownThreshold;
	/**< Sets the threshold value an image can be scaled down to. If the shorter edge size is larger than the given value, the library will calculate the required height and width of the barcode image and shrink the image to that size before localization. Otherwise, it will perform barcode localization on the original image.
	*
	* @par Value range:
	* 		[512,0x7fffffff]
	* @par Default value:
	* 		2300
	* @par Remarks:
	*		If you have an image whose shorter edge size is larger than the given value and the barcode is a small part on it, you can set this value to be larger than the shorter edge of this image.
	*		If you have an image whose shorter edge size is larger than the given value and the barcode is clear and big, you can set this value to a smaller one than the default value.
	*/



	int mGrayEqualizationSensitivity;
	/**< Sets the sensitivity used for gray equalization. May cause adverse effect on images with a high level ofcontrast. The higher the value, the more likely gray equalization will be activated.
	*
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		0
	* @par Remarks:
	*		If you have an image with a low level of contrast,  you can set the property to a larger value. If the value is set to 0, gray equalization will be disabled. If the value is set to 9, gray equalization will be activated.
	*		For better accuracy for images with low camparison, set this property to 9.
	*/



	int mEnableFillBinaryVacancy;
	/**< Sets whether to enable fill binary vacancy.
	*
	* @par Value range:
	* 		0, 1 (0 - disable, 1 - enable)
	* @par Default value:
	* 		1
	* @par Remarks:
	*		For barcodes with a large module size there might be a vacant area in the position detection pattern after binarization which may result in a decoding failure. Setting this to true will fill in the vacant area with black and may help to decode it successfully.
	*		Better accuracy for images with a large module size.
	*/



	ColourImageConvertMode mColourImageConvertMode;
	/**< Sets whether to convert colour images to grayscale before processing.
	*
	* @par Value range:
	* 		CICM_Auto, CICM_Grayscale
	* @par Default value:
	* 		CICM_Auto
	* @par Remarks:
	*		If you need to decode the barcode in the region pre-detection mode, it works better with the value CICM_Auto. There are no effects to the results. It will pass the original image for if you set it to CICM_Auto and the gray-scale image if you set it otherwise.
	* @sa ColourImageConvertMode
	*/



	int mExpectedBarcodesCount;
	/**< Sets the expected number of barcodes to read for each image (or each region of the image if you specified barcode regions).
	*
	* @par Value range:
	* 		[0,0x7fffffff]
	* @par Default value:
	* 		0
	* @par Remarks:
	* 		- 0: means Unknown and it will find at least one barcode.
	*
	* 		- 1: try to find one barcode. If one barcode is found, the library will stop the localization process and perform barcode decoding.
	*
	* 		- n: try to find n barcodes. If the library only finds m (m<n) barcode, it will try different algorithms till n barcodes are found or all algorithms are used.
	*
	* 		The value of ExpectedBarcodesCount must be less than or equal to the value of MaxBarcodesCount. To ensure the best performance, the value of AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	*		When AntiDamageLevel is larger than 7, the bigger ExpectedBarcodesCount you set, the more localization algorithms will be used which leads to a higher accuracy with slower performance.
	* @sa mMaxBarcodesCount mAntiDamageLevel
	*/



	int mBinarizationBlockSize;
	/**< Sets the block size for the process of binarization. Block size refers to the size of a pixel neighborhood used to calculate a threshold value for the pixel.
	*
	* @par Value range:
	* 		[0,1000]
	* @par Default:
	* 		0
	* @par Remarks:
	* 		- 0: the block size used for binarization will be set to a value which is calculated automatically.
	*
	* 		- N:
	* 		 - 1 <= N <= 3: the block size used for binarization will be set to 3.
	* 		 - N > 3: the block size used for binarization will be set to N.
	*
	*		An appropriate value for mBinarizationBlockSize can help generate a high quality binary image to increase the accuracy of barcode localization.
	*/


	char mReserved[248];
	/**< Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.*/
}PublicParameterSettings;


/**
 * @}
 * @}
 * @}
 */
#pragma pack(pop)

//---------------------------------------------------------------------------
// Functions
//---------------------------------------------------------------------------

#ifdef __cplusplus
/** . */
extern "C" {
#endif // endif of __cplusplus.
	/**
	* @defgroup CFunctions C Functions
	* @{
	*   
	* Four methods are now supported for editing runtime settings - reset, initialize, append, update. 
	* - Reset runtime settings: reset all parameters in runtime setting to default value.     
	*  
	* - Initialize with template: reset runtime settings firstly and replace all parameters in runtime setting with the values specified in given template regardless of the current runtime settings.   
	*  
	* - Append template to runtime settings: append template and update runtime settings; the conflicting values will be assigned by the rules shown in PublicRuntimeSettings.    
	*
	* - Update with struct: update current runtime settings by the values specified in given struct directly; the parameter not be defined in struct will remain its original value.   
	* 
	* @par References
	* More information about public parameters and template file can be found in file DBR_Developer's_Guide.pdf.
	*
	* 
	* @sa PublicRuntimeSettings
	* @defgroup BasicFunciton Basic Functions
	* @{
	*   Basic APIs used for running Dynamsoft Barcode Reader. 
	*/


	/**
	 * Creates an instance of Dynamsoft Barcode Reader.
	 * 
	 * @return Returns an instance of Dynamsoft Barcode Reader. If failed, return NULL.
	 *
	 * @par Remarks:
	 *		The decoding result maybe unreliable without loading license key.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API void*  DBR_CreateInstance();

	/**
	 * Destroys an instance of Dynamsoft Barcode Reader.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API void DBR_DestroyInstance(void*  hBarcodeReader);

	/**
	 * Reads license key and activate the SDK.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszLicense The license keys.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_InitLicense(void*  hBarcodeReader, const char* pszLicense);

	/**
	 * Initializes barcode reader license and connects to the specified server for online verification.
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszLicenseServer The name/IP of the license server.
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 */
	DBR_API int DBR_InitLicenseFromServer(void* hBarcodeReader, const char* pszLicenseServer, const char* pszLicenseKey);

	/**
	 * Initializes barcode reader license from the license content on the client machine for offline verification.
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 * @param [in] pszLicenseContent An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method DBR_OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 */
	DBR_API int DBR_InitLicenseFromLicenseContent(void* hBarcodeReader, const char* pszLicenseKey, const char* pszLicenseContent);

	/**
	 * Initializes barcode reader license from the license content on the mobile device for offline verification.
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 * @param [in] pszMachineID The machine ID of the mobile device
	 * @param [in] pszLicenseContent An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method DBR_OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 */
	DBR_API int DBR_InitLicenseFromLicenseContentEx(void* hBarcodeReader, const char* pszLicenseKey, const char* pszMachineID, const char* pszLicenseContent);

	/**
	 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in, out] pszContent The output string which stores the contents of license.
	 * @param [in] nContentLen The length of output string.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 */
	DBR_API int DBR_OutputLicenseToString(void* hBarcodeReader, char pszContent[], int nContentLen);
	

	/**
	 * Decodes barcodes in the specified image file.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszFileName A string defining the file name.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeFile(void*  hBarcodeReader, const char* pszFileName, const char* pszTemplateName);

	/**
	 * Decodes barcode from an image file in memory.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pFileBytes The image file bytes in memory.
	 * @param [in] nFileSize The length of the file bytes in memory.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			unsigned char* pFileBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			int errorCode = DBR_DecodeFileInMemory(hBarcodeReader, pFileBytes, nFileSize, "");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeFileInMemory(void*  hBarcodeReader, unsigned char* pFileBytes, int nFileSize, const char* pszTemplateName);

	/**
	 * Decodes barcodes from the memory buffer containing image pixels in defined format.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
	 * @param [in] iWidth The width of the image in pixels.
	 * @param [in] iHeight The height of the image in pixels.
	 * @param [in] iStride The stride of the image (also called scan width).
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			unsigned char* pBufferBytes;
			int iWidth = 0;
			int iHeight = 0;
			int iStride = 0;
			ImagePixelFormat format;
			GetBufferFromFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pBufferBytes, &iWidth, &iHeight, &iStride, &format);
			int errorCode = DBR_DecodeBuffer(hBarcodeReader, pBufferBytes, iWidth, iHeight, iStride, format, "");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeBuffer(void*  hBarcodeReader, unsigned char* pBufferBytes, int iWidth, int iHeight, int iStride, ImagePixelFormat format, const char* pszTemplateName);

	/**
	 * Decodes barcode from an image file encoded as a base64 string.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszBase64String A base64 encoded string that represents an image.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			unsigned char* pBufferBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			char* strBase64String;
			GetFileBase64String(pBufferBytes, &strBase64String);
			int errorCode = DBR_DecodeBase64String(hBarcodeReader, strBase64String, "");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeBase64String(void*  hBarcodeReader, const char* pszBase64String, const char* pszTemplateName);

	/**
	 * Decodes barcode from a handle of device-independent bitmap (DIB).
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] hDIB Handle of the device-independent bitmap.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			HANDLE pDIB;
			GetDIBFromImage("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pDIB);
			int errorCode = DBR_DecodeDIB(hBarcodeReader, pDIB, "");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeDIB(void*  hBarcodeReader, HANDLE hDIB, const char* pszTemplateName);

	/**
	 * Gets all recognized barcode results.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [out] ppResults Barcode text results returned by last calling function 
	 * 				DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB.
	 * 				The ppResults is allocated by SDK and should be freed by calling function DBR_FreeTextResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			STextResultArray* pResults;
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllTextResults(hBarcodeReader, &pResults);
			DBR_FreeTextResults(&pResults);
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_GetAllTextResults(void* hBarcodeReader, STextResultArray **ppResults);

	/**
	 * Gets all localization barcode results. It contains all recognized barcodes and unrecognized
	 * barcodes.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [out] ppResults Barcode localization results returned by last calling function 
	 * 				DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB. 
	 * 				The ppResults is allocated by SDK and should be freed by calling function DBR_FreeLocalizationResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			SLocalizationResultArray* pLocResults;
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllLocalizationResults(hBarcodeReader, &pLocResults);
			DBR_FreeLocalizationResults(&pLocResults);
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_GetAllLocalizationResults(void* hBarcodeReader, SLocalizationResultArray **ppResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] ppResults Text results.
	 *
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			STextResultArray* pResults;
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllTextResults(hBarcodeReader, &pResults);
			DBR_FreeTextResults(&pResults);
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API void  DBR_FreeTextResults(STextResultArray **ppResults);

	/**
	 * Frees memory allocated for localization results.
	 * 
	 * @param [in] ppResults Localization results.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			SLocalizationResultArray* pLocResults;
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllLocalizationResults(hBarcodeReader, &pLocResults);
			DBR_FreeLocalizationResults(&pLocResults);
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API void  DBR_FreeLocalizationResults(SLocalizationResultArray **ppResults);

	/**
	 * Returns the error info string.
	 * 
	 * @param [in] iErrorCode The error code.
	 * 			   
	 * @return The error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_DecodeFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			const char* errorString = DBR_GetErrorString(errorCode);
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API const char* DBR_GetErrorString(int iErrorCode);

	/**
	 * Returns the version info string for the SDK.
	 * 
	 * @return The version info string.
	 *
	 * @par Code Snippet:
	 * @code
			const char* versionInfo = DBR_GetVersion();
	 * @endcode
	 */
	DBR_API const char* DBR_GetVersion();

	/**
	 * Gets current settings and save it into a struct.
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in,out] pSettings The struct of template settings.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(hBarcodeReader, pSettings);
			delete pSettings;
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_GetRuntimeSettings(void* hBarcodeReader, PublicRuntimeSettings *pSettings);

	/**
	 * Update runtime settings with a given struct.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length 
	 * 				   is 256.The error message will be copied to the buffer.
	 * @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 *		  DBR_GetErrorString to get detail message.
	 * 
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(hBarcodeReader, pSettings);
			pSettings->mAntiDamageLevel = 7;
			pSettings->mDeblurLevel = 9;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(hBarcodeReader, pSettings, errorMessage, 256);
			delete pSettings;
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_UpdateRuntimeSettings(void* hBarcodeReader,PublicRuntimeSettings *pSettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);

	/**
	 * Resets all parameters to default values.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(hBarcodeReader, pSettings);
			pSettings->mAntiDamageLevel = 7;
			pSettings->mDeblurLevel = 9;
			DBR_UpdateRuntimeSettings(hBarcodeReader, pSettings);
			DBR_ResetRuntimeSettings(hBarcodeReader);
			delete pSettings;
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_ResetRuntimeSettings(void* hBarcodeReader);

	/**
	* @}
	*/

	/**
	* @defgroup AdvancedFunctions Advanced Functions
	* @{
	*   Advanced APIs for customizing parameters in runtime settings to fit specified scenarios.
	*/
	/**
	* Initialize runtime settings with the parameters obtained from JSON file.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszFilePath The settings file path.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from 
	* 			  previous template setting or overwrite previous settings and replace by new template.  
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommending 
	* 				  length is 256. The error message would be copy to the buffer.
	* @param [in] nErrorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	* 		  DBR_GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_InitRuntimeSettingsWithFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessage, 256);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithFile(void* hBarcodeReader, const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Initialize runtime settings with the parameters obtained from JSON string.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from 
	* 			  previous template setting or overwrite previous settings and replace by new template.  
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message would be copy to the buffer.
	* @param [in] nErrorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	* 		  DBR_GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_InitRuntimeSettingsWithString(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Overwrite, errorMessage, 256);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithString(void* hBarcodeReader, const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Append a new template file to current runtime settings.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszFilePath The settings file path.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message would be copy to the buffer.
	* @param [in] nErrorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_AppendTplFileToRuntimeSettings(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Ignore, errorMessage, 256);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_AppendTplFileToRuntimeSettings(void* hBarcodeReader, const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Append a new template string to current runtime settings.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message would be copy to the buffer.
	* @param [in] nErrorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_AppendTplStringToRuntimeSettings(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessage, 256);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings 
	*/
	DBR_API int  DBR_AppendTplStringToRuntimeSettings(void* hBarcodeReader, const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Get count of parameter template.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	*
	* @return Returns the count of parameter template.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			int currentTemplateCount = DBR_GetParameterTemplateCount(hBarcodeReader);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	*/
	DBR_API int  DBR_GetParameterTemplateCount(void* hBarcodeReader);

	/**
	* Get paramter template name by index.
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] iIndex The index of parameter template array.
	* @param [in,out] szNameBuffer The buffer is allocated by caller and the recommended
	* 				  length is 256. The template name would be copy to the buffer.
	* @param [in] nNameBufferLen The length of allocated buffer
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			int currentTemplateCount = DBR_GetParameterTemplateCount(hBarcodeReader);
			int templateIndex = 2;
			// notice that the value of 'templateIndex' should less than currentTemplateCount.
			char errorMessage[256];
			DBR_GetParameterTemplateName(hBarcodeReader, templateIndex, errorMessage, 256);
			DBR_DestroyInstance(hBarcodeReader);
	* @endcode
	*
	*/
	DBR_API int  DBR_GetParameterTemplateName(void* hBarcodeReader, int iIndex, char szNameBuffer[], int nNameBufferLen);

	/**
	 * Outputs runtime settings to a string.
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in,out] pszContent The output string which stores the contents of current settings.	   
	 * @param [in] nContentLen The length of output string.
	 * @param [in] pszSettingsName A unique name for declaring current runtime settings.	
     *	 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			 DBR_InitRuntimeSettingsWithFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			char pszContent[256];
			DBR_OutputSettingsToString(hBarcodeReader, pszContent, 256, "currentRuntimeSettings");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_OutputSettingsToString(void* hBarcodeReader, char pszContent[], int nContentLen, const char* pszSettingsName);

	/**
	 * Outputs runtime settings and save it into a settings file (JSON file).
	 * 
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszFilePath The output file path which stores current settings.
	 * @param [in] pszSettingsName A unique name for declaring current runtime settings.
     *				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			void* hBarcodeReader = DBR_CreateInstance();
			DBR_InitLicense(hBarcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(hBarcodeReader, "{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			DBR_OutputSettingsToFile(hBarcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\CurrentRuntimeSettings.json", "currentRuntimeSettings");
			DBR_DestroyInstance(hBarcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_OutputSettingsToFile(void* hBarcodeReader, const char* pszFilePath, const char* pszSettingsName);

	/**
	 * @} 
	 */

	/**
	 * @defgroup CompatibleFunctionsC Compatible Functions
	 * @{
	 */

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_InitRuntimeSettingsWithFile with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_LoadSettingsFromFile
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszFilePath The path of the settings file. 
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length
	* 				   is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	* 		  
	* @sa DBR_InitRuntimeSettingsWithFile
	*/
	DBR_API int  DBR_LoadSettingsFromFile(void* hBarcodeReader, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_InitRuntimeSettingsWithString with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_LoadSettings
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	* 		  
	* @sa DBR_InitRuntimeSettingsWithString
	*/	
	DBR_API int  DBR_LoadSettings(void* hBarcodeReader, const char* pszContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_AppendTplFileToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_AppendParameterTemplateFromFile
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszFilePath The path of the settings file.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	* 		  
	* @sa DBR_AppendTplFileToRuntimeSettings
	*/
	DBR_API int  DBR_AppendParameterTemplateFromFile(void* hBarcodeReader, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_AppendTplStringToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_AppendParameterTemplate
	*
	* @param [in] hBarcodeReader Handle of the barcode reader instance.
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	* 		  
	* @sa DBR_AppendTplStringToRuntimeSettings
	*/
	DBR_API int  DBR_AppendParameterTemplate(void* hBarcodeReader, const char* pszContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to DBR_GetRuntimeSettings.
	 *
	 * @deprecated DBR_GetTemplateSettings
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszTemplateName The template name.
	 * @param [in,out] pSettings The struct of template settings.
	 * 				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @sa DBR_GetRuntimeSettings	 
	 */ 
	DBR_API int DBR_GetTemplateSettings(void* hBarcodeReader,const char*pszTemplateName, PublicParameterSettings *pSettings);

	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to DBR_UpdateRuntimeSettings.
	 *
	 * @deprecated DBR_SetTemplateSettings
	 *
	 * @param [in] hBarcodeReader Handle of the barcode reader instance.
	 * @param [in] pszTemplateName The template name.
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length 
	 * 				   is 256. The error message will be copied to the buffer.
	 * @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @sa DBR_UpdateRuntimeSettings
	 */
	DBR_API int DBR_SetTemplateSettings(void* hBarcodeReader,const char*pszTemplateName,PublicParameterSettings *pSettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);


	//DBR_API int DBR_GetDBRImageObject(void* hBarcodeReader, void* hDBRImageObject);

	/**
	 * @}
	 * @} 
	 */
#ifdef __cplusplus
}
#endif //endif of __cplusplus

//---------------------------------------------------------------------------
// Class
//---------------------------------------------------------------------------


#ifdef __cplusplus
class BarcodeReaderInner;


/**
*
* @defgroup CBarcodeReaderClass CBarcodeReader Class
* @{
*
*/

/**
* Defines a class that provides functions for working with extracting barcode data.
* @class CBarcodeReader
*
* @nosubgrouping
*
* Four methods are now supported for editing runtime settings - reset, initialize, append, update. 
* - Reset runtime settings: reset all parameters in runtime setting to default value.     
*  
* - Initialize with template: reset runtime settings firstly and replace all parameters in runtime setting with the values specified in given template regardless of the current runtime settings.   
*  
* - Append template to runtime settings: append template and update runtime settings; the conflicting values will be assigned by the rules shown in PublicRuntimeSettings.    
*
* - Update with struct: update current runtime settings by the values specified in given struct directly; the parameter not be defined in struct will remain its original value.   
*
*
* @par References
* More information about public parameters and template file can be found in file DBR_Developer's_Guide.pdf.
*
*
* @sa PublicRuntimeSettings		 
*/
class DBR_API CBarcodeReader
{
private:
	/** The barcode reader */
	BarcodeReaderInner* m_pBarcodeReader;

public:
	/**
	 * @{
	 * 
	 * Default constructor
	 *
	 */

	CBarcodeReader();

	/**
	 * Destructor
	 *
	 */

	~CBarcodeReader();

	/**
	 * @}
	 *
	 * @name Basic Functions
	 * @{
	 */

	/**
	 * Reads license key and activate the SDK.
	 * 
	 * @param [in] pLicense The license keys.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			delete reader;
	 * @endcode
	 */
	int InitLicense(const char* pLicense);

	/**
	 * Initializes barcode reader license and connects to the specified server for online verification.
	 *
	 * @param [in] pszLicenseServer The name/IP of the license server.
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 */
	int InitLicenseFromServer(const char* pszLicenseServer, const char* pszLicenseKey);

	/**
	 * Initializes barcode reader license from the license content on the client machine for offline verification.
	 *
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 * @param [in] pszLicenseContent An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 */
	int InitLicenseFromLicenseContent(const char* pszLicenseKey, const char* pszLicenseContent);

	/**
	 * Initializes barcode reader license from the license content on the mobile device for offline verification.
	 *
	 * @param [in] pszLicenseKey The license key of Barcode Reader.
	 * @param [in] pszMachineID The machine ID of the mobile device
	 * @param [in] pszLicenseContent An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 */
	int InitLicenseFromLicenseContentEx(const char* pszLicenseKey, const char* pszMachineID, const char* pszLicenseContent);

	/**
	 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
	 *
	 * @param [in, out] pszContent The output string which stores the contents of license.
	 * @param [in] nContentLen The length of output string.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 */
	int OutputLicenseToString(char pszContent[], int nContentLen);

	/**
	 * Decodes barcodes in a specified image file.
	 * 
	 * @param [in] pszFileName A string defining the file name.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 * If no template name is specified, current runtime settings will be used.
	 */
	int  DecodeFile(const char* pszFileName, const char* pszTemplateName = "");

	/**
	 * Decodes barcodes from an image file in memory.
	 * 
	 * @param [in] pFileBytes The image file bytes in memory.
	 * @param [in] nFileSize The length of the file bytes in memory.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			unsigned char* pFileBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			int errorCode = reader->DecodeFileInMemory(pFileBytes, nFileSize, "");
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 * If no template name is specified, current runtime settings will be used.
	 */
	int  DecodeFileInMemory(unsigned char* pFileBytes, int nFileSize, const char* pszTemplateName = "");

	/**
	 * Decodes barcodes from the memory buffer containing image pixels in defined format.
	 * 
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
	 * @param [in] iWidth The width of the image in pixels.
	 * @param [in] iHeight The height of the image in pixels.
	 * @param [in] iStride The stride of the image (also called scan width).
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			unsigned char* pBufferBytes;
			int iWidth = 0;
			int iHeight = 0;
			int iStride = 0;
			ImagePixelFormat format;
			GetBufferFromFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pBufferBytes, &iWidth, &iHeight, &iStride, &format);
			int errorCode = reader->DecodeBuffer(pBufferBytes, iWidth, iHeight, iStride, format, "");
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 * If no template name is specified, current runtime settings will be used.
	 */
	int  DecodeBuffer(unsigned char* pBufferBytes, int iWidth, int iHeight, int iStride, ImagePixelFormat format, const char* pszTemplateName = "");

	/**
	 * Decodes barcode from an image file encoded as a base64 string.
	 * 
	 * @param [in] pszBase64String A base64 encoded string that represents an image.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			unsigned char* pFileBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			char* strBase64String;
			GetFileBase64String(pBufferBytes, &strBase64String);
			int errorCode = reader->DecodeBase64String(strBase64String, "");
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 * If no template name is specified, current runtime settings will be used.
	 */
	int  DecodeBase64String(const char* pszBase64String, const char* pszTemplateName = "");

	/**
	 * Decodes barcode from a handle of device-independent bitmap (DIB).
	 * 
	 * @param [in] hDIB Handle of the device-independent bitmap.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			HANDLE pDIB;
			GetDIBFromImage("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pDIB);
			int errorCode = reader->DecodeDIB(pDIB "");
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 * If no template name is specified, current runtime settings will be used.
	 */
	int  DecodeDIB(HANDLE  hDIB, const char* pszTemplateName = "");

	/**
	 * Gets all recognized barcode results.
	 * 
	 * @param [out] ppResults Barcode text results returned by the last called function
	 * 				DecodeFile/DecodeFileInMemory/DecodeBuffer/DecodeBase64String/DecodeDIB. The ppResults is
	 * 				allocated by our SDK and should be freed by calling the function FreeLocalizationResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			STextResultArray* pResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllTextResults(&pResults);
			CBarcodeReader::FreeTextResults(&pResults);
			delete reader;
	 * @endcode
	 *
	 */
	int GetAllTextResults(STextResultArray **ppResults);

	/**
	 * Gets all localization barcode results. It contains all recognized barcodes and unrecognized
	 * barcodes.
	 * 
	 * @param [out] ppResults Barcode localization results returned by the last called function 
	 * 				DecodeFile/DecodeFileInMemory/DecodeBuffer/DecodeBase64String/DecodeDIB. The ppResults is 
	 * 				allocated by our SDK and should be freed by calling the function FreeLocalizationResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			SLocalizationResultArray* pLocResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllLocalizationResults(&pLocResults);
			CBarcodeReader::FreeLocalizationResults(&pLocResults);
			delete reader;
	 * @endcode
	 *
	 */
	int GetAllLocalizationResults(SLocalizationResultArray **ppResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] ppResults Text results.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			STextResultArray* pResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllTextResults(&pResults);
			CBarcodeReader::FreeTextResults(&pResults);
			delete reader;
	 * @endcode
	 *
	 */
	static void FreeTextResults(STextResultArray **ppResults);

	/**
	 * Frees memory allocated for localization results.
	 * 
	 * @param [in] ppResults Localization results.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			SLocalizationResultArray* pLocResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllLocalizationResults(&pLocResults);
			CBarcodeReader::FreeLocalizationResults(&pLocResults);
			delete reader;
	 * @endcode
	 *
	 */
	static void FreeLocalizationResults(SLocalizationResultArray **ppResults);

	/**
	 * Returns the error info string.
	 * 
	 * @param [in] iErrorCode The error code.
	 * 			   
	 * @return The error message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			const char* errorString = CBarcodeReader::GetErrorString(errorCode);
			delete reader;
	 * @endcode
	 *
	 */
	static const char* GetErrorString(int iErrorCode);

	/**
	 * Returns the version info string for the SDK.
	 * 
	 * @return The version info string.
	 *
	 * @par Code Snippet:
	 * @code
			const char* versionInfo = CBarcodeReader::GetVersion();
	 * @endcode
	 *

	 */
	static const char* GetVersion();

	/**
	 * Gets current settings and save it into a struct.
	 * 
	 * @param [in,out] psettings The struct of template settings.
	 * 				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = reader->GetRuntimeSettings(pSettings);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 */
	int GetRuntimeSettings(PublicRuntimeSettings *psettings);

	/**
	 * Update runtime settings with a given struct.
	 * 
	 * @param [in] psettings The struct of template settings.
	 * @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length 
	 * 				   is 256. The error message will be copied to the buffer.
	 * @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = reader->GetRuntimeSettings(pSettings);
			pSettings->mAntiDamageLevel = 7;
			pSettings->mDeblurLevel = 9;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 */
	int UpdateRuntimeSettings(PublicRuntimeSettings *psettings, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Resets all parameters to default values.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = reader->GetRuntimeSettings(pSettings);
			pSettings->mAntiDamageLevel = 7;
			pSettings->mDeblurLevel = 9;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			reader->ResetRuntimeSettings();
			delete pSettings;
			delete reader;
	* @endcode
	*
	*/
	int ResetRuntimeSettings();

	/**
     * @}
	 * 
	 * @name Advanced Functions
	 * @{
	 */

	/**
	* Initialize runtime settings with the settings in given JSON file.
	*
	* @param [in] pszFilePath The path of the settings file.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				   is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  InitRuntimeSettingsWithFile(const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Initialize runtime settings with the settings in given JSON string.
	*
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->InitRuntimeSettingsWithString("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Overwrite, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  InitRuntimeSettingsWithString(const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Append a new template file to current runtime settings.
	*
	* @param [in] pszFilePath The path of the settings file.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->AppendTplFileToRuntimeSettings("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Ignore, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  AppendTplFileToRuntimeSettings(const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Append a new template string to current runtime settings.
	*
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in] emSettingPriority The parameter setting mode, which decides to inherit parameters from
	* 			  previous template setting or overwrite previous settings and replace by new template.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  AppendTplStringToRuntimeSettings(const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Gets the count of the parameter templates.
	*
	* @return Returns the count of parameter template.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			int currentTemplateCount = reader->GetParameterTemplateCount();
			delete reader;
	* @endcode
	*
	*/
	int  GetParameterTemplateCount();

	/**
	* Gets the parameter template name by index.
	*
	* @param [in] iIndex The index of the parameter template array.
	* @param [in,out] szNameBuffer The buffer is allocated by caller and the recommended
	* 				   length is 256. The template name would be copy to the buffer.
	* @param [in] nNameBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		   GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			int currentTemplateCount = reader->GetParameterTemplateCount();
			int templateIndex = 2;
			// notice that the value of 'templateIndex' should less than currentTemplateCount.
			char errorMessage[256];
			reader->GetParameterTemplateName(templateIndex, errorMessage, 256);
			delete reader;
	* @endcode
	*
	*/
	int  GetParameterTemplateName(int iIndex, char szNameBuffer[], int nNameBufferLen);


	/**
	* Outputs runtime settings and save it into a settings file (JSON file).
	*
	* @param [in] pszFilePath The output file path which stores current settings.
	* @param [in] pszSettingsName A unique name for declaring current runtime settings.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		   GetErrorString to get detail message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			reader->OutputSettingsToFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\CurrentRuntimeSettings.json", "currentRuntimeSettings");
			delete reader;
	* @endcode
	*
	*/
	int OutputSettingsToFile(const char* pszFilePath, const char* pszSettingsName);


	/**
	 * Outputs runtime settings to a string.
	 * 
	 * @param [in,out] szContent The output string which stores the contents of current settings.
	 * @param [in] nContentLen The length of output string.
	 * @param [in] pszSettingsName A unique name for declaring current runtime settings.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", ECM_Overwrite, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"2.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"QR_CODE\"], \"ExpectedBarcodesCount\":10, \"AntiDamageLevel\":3}}", ECM_Ignore, errorMessageAppend, 256);
			char szContent[256];
			reader->OutputSettingsToString(szContent, 256, "currentRuntimeSettings");
			delete reader;
	 * @endcode
	 *
	 */
	int OutputSettingsToString(char szContent[], int nContentLen, const char* pszSettingsName);

	

	/**
	 * @}
	 * 
	 * @name Compatible Functions
	 * @{
	 */
	 
	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to InitRuntimeSettingsWithFile with conflict mode ECM_Overwrite as default.
	*
	* @deprecated LoadSettingsFromFile
	*
	* @param [in] pszFilePath The path of the settings file.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				   is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	* 		  
	* @sa InitRuntimeSettingsWithFile
	*/
	int  LoadSettingsFromFile(const char* pszFilePath, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to InitRuntimeSettingsWithString with conflict mode ECM_Overwrite as default.
	*
	* @deprecated LoadSettings
	*
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	* 		  
	* @sa InitRuntimeSettingsWithString
	*/
	int  LoadSettings(const char* pszContent, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to AppendTplFileToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated AppendParameterTemplateFromFile
	*
	* @param [in] pszFilePath The path of the settings file.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	* 		  
	* @sa AppendTplFileToRuntimeSettings
	*/
	int  AppendParameterTemplateFromFile(const char* pszFilePath, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);
	
	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to AppendTplStringToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated AppendParameterTemplate
	*
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
	* 		  
	* @sa AppendTplStringToRuntimeSettings
	*/
	int  AppendParameterTemplate(const char* pszContent, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to GetRuntimeSettings.
	 *
	 * @deprecated GetTemplateSettings
	 *
	 * @param [in] pszTemplateName The template name.
	 * @param [in,out] pSettings The struct of template settings.
	 * 				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @sa GetRuntimeSettings	 
	 */
	int GetTemplateSettings(const char* pszTemplateName, PublicParameterSettings *pSettings);
	
	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to UpdateRuntimeSettings.
	 *
	 * @deprecated SetTemplateSettings
	 *
	 * @param [in] pszTemplateName The template name.
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] szErrorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length 
	 * 				   is 256. The error message will be copied to the buffer.
	 * @param [in] nErrorMsgBufferLen (Optional) The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
	 * @sa UpdateRuntimeSettings
	 */
	int SetTemplateSettings(const char* pszTemplateName, PublicParameterSettings *pSettings, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	//int GetDBRImageObject(void* hDBRImageObject);

	/**
	 * @}
	 */	
private:


	CBarcodeReader(const CBarcodeReader& r);

	CBarcodeReader& operator = (const CBarcodeReader& r);

};

/** 
 * @}
 * @}
 */
#endif
#endif
