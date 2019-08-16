/*
*	@file DynamsoftBarcodeReader.h
*	
*	Dynamsoft Barcode Reader C/C++ API header file.
*	Copyright 2019 Dynamsoft Corporation. All rights reserved.
*	
*	@author Dynamsoft
*	@date 27/06/2019
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
* Dynamsoft Barcode Reader - C/C++ APIs Description.
*/

#define DBR_VERSION                  "7.1.0.0808"

#pragma region ErrorCode

/**
 * @defgroup ErrorCode ErrorCode
 * @{
 */

 /**Successful. */
#define DBR_OK									 0 

 /**Unknown error. */
#define DBRERR_UNKNOWN						-10000 

 /**Not enough memory to perform the operation. */
#define DBRERR_NO_MEMORY					-10001 

 /**Null pointer. */
#define DBRERR_NULL_POINTER					-10002 

 /**The license is invalid. */
#define DBRERR_LICENSE_INVALID				-10003 

 /**The license has expired. */
#define DBRERR_LICENSE_EXPIRED				-10004 

 /**The file is not found. */
#define DBRERR_FILE_NOT_FOUND				-10005 

 /**The file type is not supported. */
#define DBRERR_FILETYPE_NOT_SUPPORTED		-10006 

 /**The BPP (Bits Per Pixel) is not supported. */
#define DBRERR_BPP_NOT_SUPPORTED			-10007 

 /**The index is invalid. */
#define DBRERR_INDEX_INVALID				-10008 

 /**The barcode format is invalid. */
#define DBRERR_BARCODE_FORMAT_INVALID		-10009 

 /**The input region value parameter is invalid. */
#define DBRERR_CUSTOM_REGION_INVALID		-10010 

 /**The maximum barcode number is invalid. */
#define DBRERR_MAX_BARCODE_NUMBER_INVALID	-10011 

 /**Failed to read the image. */
#define DBRERR_IMAGE_READ_FAILED			-10012

 /**Failed to read the TIFF image. */
#define DBRERR_TIFF_READ_FAILED				-10013

 /**The QR Code license is invalid. */
#define DBRERR_QR_LICENSE_INVALID			-10016

 /**The 1D Barcode license is invalid. */
#define DBRERR_1D_LICENSE_INVALID			-10017

 /**The DIB (Device-Independent Bitmaps) buffer is invalid. */
#define DBRERR_DIB_BUFFER_INVALID			-10018

 /**The PDF417 license is invalid. */
#define DBRERR_PDF417_LICENSE_INVALID		-10019

 /**The DATAMATRIX license is invalid. */
#define DBRERR_DATAMATRIX_LICENSE_INVALID	-10020

 /**Failed to read the PDF file. */
#define DBRERR_PDF_READ_FAILED				-10021

 /**The PDF DLL is missing. */
#define	DBRERR_PDF_DLL_MISSING				-10022

 /**The page number is invalid. */
#define DBRERR_PAGE_NUMBER_INVALID			-10023

 /**The custom size is invalid. */
#define DBRERR_CUSTOM_SIZE_INVALID			-10024

 /**The custom module size is invalid. */
#define DBRERR_CUSTOM_MODULESIZE_INVALID	-10025

 /**Recognition timeout. */
#define DBRERR_RECOGNITION_TIMEOUT			-10026

 /**Failed to parse JSON string. */
#define DBRERR_JSON_PARSE_FAILED			-10030

 /**The value type is invalid. */
#define DBRERR_JSON_TYPE_INVALID			-10031

 /**The key is invalid. */
#define DBRERR_JSON_KEY_INVALID				-10032

 /**The value is invalid or out of range. */
#define DBRERR_JSON_VALUE_INVALID			-10033

 /**The mandatory key "Name" is missing. */
#define DBRERR_JSON_NAME_KEY_MISSING		-10034

 /**The value of the key "Name" is duplicated. */
#define DBRERR_JSON_NAME_VALUE_DUPLICATED	-10035

 /**The template name is invalid. */
#define DBRERR_TEMPLATE_NAME_INVALID		-10036

 /**The name reference is invalid. */
#define DBRERR_JSON_NAME_REFERENCE_INVALID	-10037

 /**The parameter value is invalid or out of range. */
#define DBRERR_PARAMETER_VALUE_INVALID      -10038

 /**The domain of your current site does not match the domain bound in the current product key. */
#define DBRERR_DOMAIN_NOT_MATCHED           -10039

 /**The reserved info does not match the reserved info bound in the current product key. */
#define DBRERR_RESERVEDINFO_NOT_MATCHED     -10040 

/**The AZTEC license is invalid. */
#define DBRERR_AZTEC_LICENSE_INVALID        -10041 

/**The License DLL is missing. */
#define	DBRERR_LICENSE_DLL_MISSING		    -10042

/**The license key does not match the license content. */
#define DBRERR_LICENSEKEY_NOT_MATCHED       -10043

/**Failed to request the license content. */
#define DBRERR_REQUESTED_FAILED             -10044

/**Failed to init the license. */
#define DBRERR_LICENSE_INIT_FAILED          -10045

/**The Patchcode license is invalid. */
#define DBRERR_PATCHCODE_LICENSE_INVALID    -10046

/**The Postal code license is invalid. */
#define DBRERR_POSTALCODE_LICENSE_INVALID   -10047

/**The DPM license is invalid. */
#define DBRERR_DPM_LICENSE_INVALID          -10048

/**The frame decoding thread already exists. */
#define DBRERR_FRAME_DECODING_THREAD_EXISTS -10049

/**Failed to stop the frame decoding thread. */
#define DBRERR_STOP_DECODING_THREAD_FAILED  -10050

/**Failed to set mode's argument. */
#define DBRERR_SET_MODE_ARGUMENT_ERROR      -10051

/**The license content is invalid. */
#define DBRERR_LICENSE_CONTENT_INVALID      -10052

/**The license key is invalid. */
#define DBRERR_LICENSE_KEY_INVALID      -10053

/**The device number in the license key runs out. */
#define DBRERR_LICENSE_DEVICE_RUNS_OUT      -10054


/**
 * @}defgroup ErrorCode
 */
#pragma endregion

#pragma region Enum
 /**
 * @defgroup Enum Enumerations
 * @{
 */

 /**
 * @enum BarcodeFormat
 *
 * Describes the barcode types. All the formats can be combined, such as BF_CODE_39 | BF_CODE_128.
 */
typedef enum
{
	/**All supported formats */
	BF_ALL = 0x1E0007FF,
	
	/**Combined value of BF_CODABAR, BF_CODE_128, BF_CODE_39, BF_CODE_39_Extended, BF_CODE_93, BF_EAN_13, BF_EAN_8, INDUSTRIAL_25, BF_ITF, BF_UPC_A, BF_UPC_E; */
	BF_ONED = 0x7FF,
	
	/**Combined value of BF_USPSINTELLIGENTMAIL, BF_POSTNET, BF_PLANET, BF_AUSTRALIANPOST, BF_UKROYALMAIL. Not supported yet. */
	BF_POSTALCODE = 0x01F00000,
	
	/**Code 39 */
	BF_CODE_39 = 0x1,
	
	/**Code 128 */
	BF_CODE_128 = 0x2,
	
	/**Code 93 */
	BF_CODE_93 = 0x4,
	
	/**Codabar */
	BF_CODABAR = 0x8,
	
	/**ITF */
	BF_ITF = 0x10,
	
	/**EAN-13 */
	BF_EAN_13 = 0x20,
	
	/**EAN-8 */
	BF_EAN_8 = 0x40,
	
	/**UPC-A */
	BF_UPC_A = 0x80,
	
	/**UPC-E */
	BF_UPC_E = 0x100,
	
	/**Industrial 2 of 5 */
	BF_INDUSTRIAL_25 = 0x200,
	
	/**CODE39 Extended */
	BF_CODE_39_EXTENDED = 0x400,
	
	/**PDF417 */
	BF_PDF417 = 0x2000000,
	
	/**QRCode */
	BF_QR_CODE = 0x4000000,
	
	/**DataMatrix */
	BF_DATAMATRIX = 0x8000000,
	
	/**AZTEC */
	BF_AZTEC = 0x10000000,
	
	/**USPS Intelligent Mail. Not supported yet. */
	BF_USPSINTELLIGENTMAIL = 0x00100000,
	
	/**Postnet. Not supported yet. */
	BF_POSTNET = 0x00200000,
	
	/**Planet. Not supported yet. */
	BF_PLANET = 0x00400000,
	
	/**Australian Post. Not supported yet. */
	BF_AUSTRALIANPOST = 0x00800000,
	
	/**UK Royal Mail. Not supported yet. */
	BF_UKROYALMAIL = 0x01000000,
	
	/**Patch code. Not supported yet. */
	BF_PATCHCODE = 0x00010000

}BarcodeFormat;

/**
* @enum BarcodeComplementMode
*
* Describes the barcode complement mode.
*/
typedef enum
{
	/**Not supported yet. */
	BCM_AUTO = 0x01,

	/**Complements the barcode using the general algorithm. */
	BCM_GENERAL = 0x02,

	/**Skips the barcode complement. */
	BCM_SKIP = 0x00

}BarcodeComplementMode;

/**
* @enum ImagePixelFormat
*
* Describes the image pixel format.
*/
typedef enum
{
	/**0:Black, 1:White */
	IPF_BINARY,
	
	/**0:White, 1:Black */
	IPF_BINARYINVERTED,
	
	/**8bit gray */
	IPF_GRAYSCALED,
	
	/**NV21 */
	IPF_NV21,
	
	/**16bit */
	IPF_RGB_565,
	
	/**16bit */
	IPF_RGB_555,
	
	/**24bit */
	IPF_RGB_888,
	
	/**32bit */
	IPF_ARGB_8888,
	
	/**48bit */
	IPF_RGB_161616,
	
	/**64bit */
	IPF_ARGB_16161616

}ImagePixelFormat;

/**
* @enum BarcodeColourMode
*
* Describes the barcode colour mode.
*/
typedef enum
{
	/**Dark items on a light background. */
	BICM_DARK_ON_LIGHT = 0x01,
	
	/**Light items on a dark background. Not supported yet. */
	BICM_LIGHT_ON_DARK = 0x02,
	
	/**Dark items on a dark background. Not supported yet. */
	BICM_DARK_ON_DARK = 0x04,
	
	/**Light items on a light background. Not supported yet. */
	BICM_LIGHT_ON_LIGHT = 0x08,
	
	/**The background is mixed by dark and light. Not supported yet. */
	BICM_DARK_LIGHT_MIXED = 0x10,
	
	/**Dark item on a light background surrounded by dark. */
	BICM_DARK_ON_LIGHT_DARK_SURROUNDING = 0x20,
	
	/**Skips the barcode colour operation.  */
	BICM_SKIP = 0x00

}BarcodeColourMode;

/**
* @enum BinarizationMode
*
* Describes the binarization mode.
*/
typedef enum
{
	/**Not supported yet. */
	BM_AUTO = 0x01,
	
	/**Binarizes the image based on the local block. */
	BM_LOCAL_BLOCK = 0x02,
	
	/**Skips the binarization. */
	BM_SKIP = 0x00

}BinarizationMode;

/**
* @enum ColourClusteringMode
*
* Describes the colour clustering mode.
*/
typedef enum
{
	/**Not supported yet. */
	CCM_AUTO = 0x00000001,
	
	/**Clusters colours using the general algorithm based on HSV. */
	CCM_GENERAL_HSV = 0x00000002,
	
	/**Skips the colour clustering. */
	CCM_SKIP = 0x00
	
}ColourClusteringMode;	
	
/**	
* @enum ColourConversionMode	
*	
* Describes the colour conversion mode.	
*/	
typedef enum	
{	
	/**Converts a colour image to a grayscale image using the general algorithm. */
	CICM_GENERAL = 0x00000001,
	
	/**Skips the colour conversion. */
	CICM_SKIP = 0x00
	
}ColourConversionMode;	

/**
* @enum DPMCodeReadingMode
*
* Describes the DPM code reading mode.
*/
typedef enum	
{	
	/**Not supported yet. */
	DPMCRM_AUTO = 0x01,
	
	/**Reads DPM code using the general algorithm. */
	DPMCRM_GENERAL = 0x02,
	
	/**Skips DPM code reading. */
	DPMCRM_SKIP = 0x00
	
}DPMCodeReadingMode;	
	
/**	
* @enum ConflictMode	
*	
* Describes the conflict mode.	
*/	
typedef enum	
{	
	/**Ignores new settings and inherits the previous settings. */
	CM_IGNORE = 1,
	
	/**Overwrites the old settings with new settings. */
	CM_OVERWRITE = 2
	
}ConflictMode;	
	
/**	
* @enum ImagePreprocessingMode	
*	
* Describes the image preprocessing mode.	
*/	
typedef enum	
{	
	/**Not supported yet. */
	IPM_AUTO = 0x01,
	
	/**Takes the unpreprocessed image for following operations. */
	IPM_GENERAL = 0x02,
	
	/**Preprocesses the image using the gray equalization algorithm. */
	IPM_GRAY_EQUALIZE = 0x04,
	
	/**Preprocesses the image using the gray smoothing algorithm. */
	IPM_GRAY_SMOOTH = 0x08,
	
	/**Preprocesses the image using the sharpening and smoothing algorithm. */
	IPM_SHARPEN_SMOOTH = 0x10,
	
	/**Skips image preprocessing. */
	IPM_SKIP = 0x00
	
}ImagePreprocessingMode;	
	
/**	
* @enum IntermediateResultType	
*	
* Describes the intermediate result type.	
*/	
typedef enum	
{	
	/**No intermediate result */
	IRT_NO_RESULT = 0x00000000,
	
	/**Original image */
	IRT_ORIGINAL_IMAGE = 0x00000001,
	
	/**Colour clustered image. Not supported yet. */
	IRT_COLOUR_CLUSTERED_IMAGE = 0x00000002,
	
	/**Colour image converted to grayscale  */
	IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE = 0x00000004,
	
	/**Transformed grayscale image */
	IRT_TRANSFORMED_GRAYSCALE_IMAGE = 0x00000008,
	
	/**Predetected region */
	IRT_PREDETECTED_REGION = 0x00000010,
	
	/**Preprocessed image */
	IRT_PREPROCESSED_IMAGE = 0x00000020,
	
	/**Binarized image */
	IRT_BINARIZED_IMAGE = 0x00000040,
	
	/**Text zone */
	IRT_TEXT_ZONE = 0x00000080,
	
	/**Contour */
	IRT_CONTOUR = 0x00000100,
	
	/**Line segment */
	IRT_LINE_SEGMENT = 0x00000200,
	
	/**Form. Not supported yet. */
	IRT_FORM = 0x00000400,
	
	/**Segmentation block. Not supported yet. */
	IRT_SEGMENTATION_BLOCK = 0x00000800,
	
	/**Typed barcode zone */
	IRT_TYPED_BARCODE_ZONE = 0x00001000
	
}IntermediateResultType;	
	
/**	
* @enum LocalizationMode	
*	
* Describes the localization mode.	
*/	
typedef enum	
{	
	/**Not supported yet. */
	LM_AUTO = 0x01,
	
	/**Localizes barcodes by searching for connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlocks to the highest priority. */
	LM_CONNECTED_BLOCKS = 0x02,
	
	/**Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix. */
	LM_STATISTICS = 0x04,
	
	/**Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes.  */
	LM_LINES = 0x08,
	
	/**Localizes barcodes quickly. This mode is recommended in interactive scenario. */
	LM_SCAN_DIRECTLY = 0x10,

	/**Localizes barcodes by groups of marks.This is optimized for DPM codes. Not supported yet.*/
	LM_STATISTICS_MARKS = 0x20,
	
	/**Skips localization. */
	LM_SKIP = 0x00
	
}LocalizationMode;	
	
/**	
* @enum QRCodeErrorCorrectionLevel	
*	
* Describes the QR Code error correction level.	
*/	
typedef enum	
{	
	/**Error Correction Level H (high) */
	QRECL_ERROR_CORRECTION_H,
	
	/**Error Correction Level L (low) */
	QRECL_ERROR_CORRECTION_L,
	
	/**Error Correction Level M (medium-low) */
	QRECL_ERROR_CORRECTION_M,
	
	/**Error Correction Level Q (medium-high) */
	QRECL_ERROR_CORRECTION_Q
	
}QRCodeErrorCorrectionLevel;	
	
/**	
* @enum RegionPredetectionMode	
*	
* Describes the region predetection mode.	
*/	
typedef enum	
{	
	/**Lets the library choose an algorithm automatically to detect region. */
	RPM_AUTO = 0x01,
	
	/**Takes the whole image as a region. */
	RPM_GENERAL = 0x02,
	
	/**Detects region using the general algorithm based on RGB colour contrast. */
	RPM_GENERAL_RGB_CONTRAST = 0x04,
	
	/**Detects region using the general algorithm based on gray contrast. */
	RPM_GENERAL_GRAY_CONTRAST = 0x08,
	
	/**Detects region using the general algorithm based on HSV colour contrast. */
	RPM_GENERAL_HSV_CONTRAST = 0x10,
	
	/**Skips region detection. */
	RPM_SKIP = 0x00
	
}RegionPredetectionMode;	
	
/**	
* @enum DeformationResistingMode	
*	
* Describes the deformation resisting mode.	
*/	
typedef enum	
{	
	/**Not supported yet. */
	DRM_AUTO = 0x01,
	
	/**Resists deformation using the general algorithm. */
	DRM_GENERAL = 0x02,
	
	/**Skips deformation resisting. */
	DRM_SKIP = 0x00
	
}DeformationResistingMode;	
	
/**	
* @enum ResultType	
*	
* Describes the extended result type.	
*/	
typedef enum	
{	
	/**Specifies the standard text. This means the barcode value. */
	RT_STANDARD_TEXT,
	
	/**Specifies the raw text. This means the text that includes start/stop characters, check digits, etc. */
	RT_RAW_TEXT,
	
	/**Specifies all the candidate text. This means all the standard text results decoded from the barcode. */
	RT_CANDIDATE_TEXT,
	
	/**Specifies the partial text. This means part of the text result decoded from the barcode. */
	RT_PARTIAL_TEXT
	
}ResultType;	
	
/**	
* @enum TerminatePhase	
*	
* Describes the terminate phase.	
*/	
typedef enum	
{	
	/**Exits the barcode reading algorithm after the region predetection is done. */
	TP_REGION_PREDETECTED = 0x00000001,
	
	/**Exits the barcode reading algorithm after the region predetection and image pre-processing is done. */
	TP_IMAGE_PREPROCESSED = 0x00000002,
	
	/**Exits the barcode reading algorithm after the region predetection, image pre-processing, and image binarization are done. */
	TP_IMAGE_BINARIZED = 0x00000004,
	
	/**Exits the barcode reading algorithm after the region predetection, image pre-processing, image binarization, and barcode localization are done. */
	TP_BARCODE_LOCALIZED = 0x00000008,
	
	/**Exits the barcode reading algorithm after the region predetection, image pre-processing, image binarization, barcode localization, and barcode type determining are done. */
	TP_BARCODE_TYPE_DETERMINED = 0x00000010,
	
	/**Exits the barcode reading algorithm after the region predetection, image pre-processing, image binarization, barcode localization, barcode type determining, and barcode recognition are done. */
	TP_BARCODE_RECOGNIZED = 0x00000020
	
}TerminatePhase;	
	
/**	
* @enum TextAssistedCorrectionMode	
*	
* Describes the text assisted correction mode.	
*/	
typedef enum	
{	
	/**Not supported yet. */
	TACM_AUTO = 0x01,
	
	/**Uses the accompanying text to verify the decoded barcode result. */
	TACM_VERIFYING = 0x02,
	
	/**Uses the accompanying text to verify and patch the decoded barcode result. */
	TACM_VERIFYING_PATCHING = 0x04,
	
	/**Skips the text assisted correction. */
	TACM_SKIP = 0x00
	
}TextAssistedCorrectionMode;	
	
/**	
* @enum TextFilterMode	
*	
* Describes the text filter mode. 	
*/	
typedef enum	
{	
	/**Not supported yet. */
	TFM_AUTO = 0x01,
	
	/**Filters text using the general algorithm based on contour. */
	TFM_GENERAL_CONTOUR = 0x02,
	
	/**Skips text filtering. */
	TFM_SKIP = 0x00
	
}TextFilterMode;	

/**
* @enum IntermediateResultSavingMode
*
* Describes the intermediate result saving mode.
*/
typedef enum
{
	/**Saves intermediate results in memory.*/
	IRSM_MEMORY = 0x01,

	/**Saves intermediate results in file system.*/
	IRSM_FILESYSTEM = 0x02,

	/**Saves intermediate results in both memory and file system.*/
	IRSM_BOTH = 0x04

}IntermediateResultSavingMode;

/**	
* @enum TextResultOrderMode	
*	
* Describes the text result order mode.	
*/	
typedef enum	
{	
	/**Returns the text results in descending order by confidence. */
	TROM_CONFIDENCE = 0x01,
	
	/**Returns the text results in position order, from top to bottom, then left to right */
	TROM_POSITION = 0x02,
	
	/**Returns the text results in alphabetical and numerical order by barcode format string. */
	TROM_FORMAT = 0x04,
	
	/**Skips the result ordering operation. */
	TROM_SKIP = 0x00
	
}TextResultOrderMode;	
	
/**	
* @enum TextureDetectionMode	
*	
* Describes the texture detection mode.	
*/	
typedef enum	
{	
	/**Not supported yet. */
	TDM_AUTO = 0X01,
	
	/**Detects texture using the general algorithm. */
	TDM_GENERAL_WIDTH_CONCENTRATION = 0X02,
	
	/**Skips texture detection. */
	TDM_SKIP = 0x00
	
}TextureDetectionMode;	
	
/**	
* @enum GrayscaleTransformationMode	
*	
* Describes the grayscale transformation mode.	
*/	
typedef enum	
{	
	/**Transforms to inverted grayscale. Recommended for light on dark images. */
	GTM_INVERTED = 0x01,
	
	/**Keeps the original grayscale. Recommended for dark on light images. */
	GTM_ORIGINAL = 0x02,
	
	/**Skips grayscale transformation. */
	GTM_SKIP = 0x00
	
}GrayscaleTransformationMode;	
	
/**	
* @enum ResultCoordinateType	
*	
* Describes the result coordinate type.	
*/	
typedef enum	
{	
	/**Returns the coordinate in pixel value. */
	RCT_PIXEL = 0x01,
	
	/**Returns the coordinate as a percentage. */
	RCT_PERCENTAGE = 0x02
	
}ResultCoordinateType;	
	
/**	
* @enum IMResultDataType	
*	
* Describes the intermediate result data type.	
*/	
typedef enum	
{	
	/**Specifies the ImageData */
	IMRDT_IMAGE = 0x01,
	
	/**Specifies the Contour */
	IMRDT_CONTOUR = 0x02,
	
	/**Specifies the LineSegment */
	IMRDT_LINESEGMENT = 0x04,
	
	/**Specifies the LocalizationResult */
	IMRDT_LOCALIZATIONRESULT = 0x08,
	
	/**Specifies the RegionOfInterest */
	IMRDT_REGIONOFINTEREST = 0x10
	
}IMResultDataType;	

/**
 * @} defgroup Enum Enumerations
 */

#pragma endregion

#pragma region Struct
//---------------------------------------------------------------------------
// Structures
//---------------------------------------------------------------------------

#pragma pack(push)
#pragma pack(1)

/**
* @defgroup Struct Struct
* @{
*/

/**
* @defgroup RegionDefinition RegionDefinition
* @{
*/
/**
*Stores the region info.
*/
typedef struct tagRegionDefinition
{
	/**The top-most coordinate or percentage of the region.
	*
	* @par Value range:
	* 	    regionMeasuredByPercentage = 0, [0, 0x7fffffff]
	* 	    regionMeasuredByPercentage = 1, [0, 100]
	* @par Default value:
	* 	    0
	*/
	int regionTop;

	/**The left-most coordinate or percentage of the region.
	*
	* @par Value range:
	* 	    regionMeasuredByPercentage = 0, [0, 0x7fffffff]
	* 	    regionMeasuredByPercentage = 1, [0, 100]
	* @par Default value:
	* 	    0
	*/
	int regionLeft;

	/**The right-most coordinate or percentage of the region.
	*
	* @par Value range:
	* 	    regionMeasuredByPercentage = 0, [0, 0x7fffffff]
	* 	    regionMeasuredByPercentage = 1, [0, 100]
	* @par Default value:
	* 	    0
	*/
	int regionRight;

	/**The bottom-most coordinate or percentage of the region.
	*
	* @par Value range:
	* 	    regionMeasuredByPercentage = 0, [0, 0x7fffffff]
	* 	    regionMeasuredByPercentage = 1, [0, 100]
	* @par Default value:
	* 	    0
	*/
	int regionBottom;

	/**Sets whether or not to use percentage to measure the region size.
	*
	* @par Value range:
	* 	    [0, 1]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*     When it's set to 1, the values of Top, Left, Right, Bottom indicate percentage (from 0 to 100); Otherwise, they indicate coordinates.
	*     0: not by percentage
	*     1: by percentage
	*/
	int regionMeasuredByPercentage;
}RegionDefinition;

/**
* @} defgroup RegionDefinition
*/

/**
* @defgroup FurtherModes FurtherModes
* @{
*/
/**
* Stores the FurtherModes.
*
*/
typedef struct tagFurtherModes
{
	/**Sets the mode and priority for colour categorization. Not supported yet.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ColourClusteringMode Enumeration items.
	* @par Default value:
	* 	    [CCM_SKIP,CCM_SKIP,CCM_SKIP,CCM_SKIP,CCM_SKIP,CCM_SKIP,CCM_SKIP,CCM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa ColourClusteringMode
	*/
	ColourClusteringMode colourClusteringModes[8];

	/**Sets the mode and priority for converting a colour image to a grayscale image.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ColourConversionMode Enumeration items.
	* @par Default value:
	* 	    [CICM_GENERAL,CICM_SKIP,CICM_SKIP,CICM_SKIP,CICM_SKIP,CICM_SKIP,CICM_SKIP,CICM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa ColourConversionMode
	*/
	ColourConversionMode colourConversionModes[8];

	/**Sets the mode and priority for the grayscale image conversion.
	*
	* @par Value range:
	* 	    Each array item can be any one of the GrayscaleTransformationMode Enumeration items.
	* @par Default value:
	* 	    [GTM_ORIGINAL,GTM_SKIP,GTM_SKIP,GTM_SKIP,GTM_SKIP,GTM_SKIP,GTM_SKIP,GTM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa GrayscaleTransformationMode
	*/
	GrayscaleTransformationMode grayscaleTransformationModes[8];

	/**Sets the region pre-detection mode for barcodes search.
	*
	* @par Value range:
	* 	    Each array item can be any one of the RegionPredetectionMode Enumeration items
	* @par Default value:
	* 	    [RPM_GENERAL,RPM_SKIP,RPM_SKIP,RPM_SKIP,RPM_SKIP,RPM_SKIP,RPM_SKIP,RPM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	*     If the image is large and the barcode on the image is very small, it is recommended to enable region predetection to speed up the localization process and recognition accuracy.
	* @sa RegionPredetectionMode
	*/
	RegionPredetectionMode regionPredetectionModes[8];

	/**Sets the mode and priority for image preprocessing algorithms.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ImagePreprocessingMode Enumeration items.
	* @par Default value:
	* 	    [IPM_GENERAL,IPM_SKIP,IPM_SKIP,IPM_SKIP,IPM_SKIP,IPM_SKIP,IPM_SKIP,IPM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa ImagePreprocessingMode
	*/
	ImagePreprocessingMode imagePreprocessingModes[8];

	/**Sets the mode and priority for texture detection.
	*
	* @par Value range:
	* 	    Each array item can be any one of the TextureDetectionMode Enumeration items
	* @par Default value:
	* 	    [TDM_GENERAL_WIDTH_CONCENTRATION,TDM_SKIP,TDM_SKIP,TDM_SKIP,TDM_SKIP,TDM_SKIP,TDM_SKIP,TDM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa TextureDetectionMode
	*/
	TextureDetectionMode textureDetectionModes[8];

	/**Sets the mode and priority for text filter.
	*
	* @par Value range:
	* 	    Each array item can be any one of the TextFilterMode Enumeration items.
	* @par Default value:
	* 	    [TFM_GENERAL_CONTOUR,TFM_SKIP,TFM_SKIP,TFM_SKIP,TFM_SKIP,TFM_SKIP,TFM_SKIP,TFM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	*     If the image contains a lot of text, you can enable text filter to speed up the localization process.
	* @sa TextFilterMode
	*/
	TextFilterMode textFilterModes[8];

	/**Sets the mode of text assisted correction for barcode decoding. Not supported yet.
	*
	* @par Value range:
	* 	    Any one of the TextAssistedCorrectionMode Enumeration items
	* @par Default value:
	* 	    TACM_VERIFYING
	* @sa TextAssistedCorrectionMode
	*/
	TextAssistedCorrectionMode textAssistedCorrectionMode;

	/**Sets the mode and priority for DPM code reading. Not supported yet.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ColourConversionMode Enumeration items.
	* @par Default value:
	* 	    [DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa ColourConversionMode
	*/
	DPMCodeReadingMode dpmCodeReadingModes[8];

	/**Sets the mode and priority for deformation resisting. Not supported yet.
	*
	* @par Value range:
	* 	    Each array item can be any one of the DeformationResistingMode Enumeration items
	* @par Default value:
	* 	    [DRM_SKIP,DRM_SKIP,DRM_SKIP,DRM_SKIP,DRM_SKIP,DRM_SKIP,DRM_SKIP,DRM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa DeformationResistingMode
	*/
	DeformationResistingMode deformationResistingModes[8];

	/**Sets the mode and priority to complement the missing parts in the barcode. Not supported yet.
	*
	* @par Value range:
	* 	    Each array item can be any one of the BarcodeComplementMode Enumeration items.
	* @par Default value:
	* 	    [BCM_SKIP,BCM_SKIP,BCM_SKIP,BCM_SKIP,BCM_SKIP,BCM_SKIP,BCM_SKIP,BCM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa BarcodeComplementMode
	*/
	BarcodeComplementMode barcodeComplementModes[8];

	/**Sets the mode and priority for the barcode colour mode used to process the barcode zone.
	*
	* @par Value range:
	* 	    Each array item can be any one of the BarcodeColourMode Enumeration items
	* @par Default value:
	* 	    [BICM_DARK_ON_LIGHT,BICM_SKIP,BICM_SKIP,BICM_SKIP,BICM_SKIP,BICM_SKIP,BICM_SKIP,BICM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa BarcodeColourMode
	*/
	BarcodeColourMode barcodeColourModes[8];

	/**Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[64];
}FurtherModes;

/**
* @} defgroup FurtherModes
*/

/**
* @defgroup CPublicRuntimeSettings PublicRuntimeSettings
* @{
*/
/**
* Defines a struct to configure the barcode reading runtime settings.
* These settings control the barcode recognition process such as which barcode types to decode.
*
*/
typedef struct tagPublicRuntimeSettings
{
	/**Sets the phase to stop the barcode reading algorithm.
	*
	* @par Value range:
	* 	    Any one of the TerminatePhase Enumeration items
	* @par Default value:
	* 	    TP_BARCODE_RECOGNIZED
	* @par Remarks:
	*	    When the recognition result is not desired, you can set this parameter can be set to skip certain processing stages.
	* @sa TerminatePhase
	*/
	TerminatePhase terminatePhase;

	/**Sets the maximum amount of time (in milliseconds) that should be spent searching for a barcode per page. It does not include the time taken to load/decode an image (TIFF, PNG, etc.) from disk into memory.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    10000
	* @par Remarks:
	*	    If you want to stop reading barcodes after a certain period of time, you can use this parameter to set a timeout.
	*/
	int timeout;

	/**Sets the number of threads the image processing algorithm will use to decode barcodes.
	*
	* @par Value range:
	* 	    [1, 4]
	* @par Default value:
	* 	    4
	* @par Remarks:
	*	    To keep a balance between speed and quality, the library concurrently runs four different threads for barcode decoding by default. 
	*/
	int maxAlgorithmThreadCount;

	/**Sets the number of barcodes expected to be detected for each image.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*	    0: means Unknown and it will find at least one barcode.
	*	    1: try to find one barcode. If one barcode is found, the library will stop the localization process and perform barcode decoding.
	*	    n: try to find n barcodes. If the library only finds m (m<n) barcode, it will try different algorithms till n barcodes are found or all algorithms are tried.
	*/
	int expectedBarcodesCount;

	/**Sets the formats of the barcode to be read. Barcode formats can be combined.
	*
	* @par Value range:
	* 	    A combined value of BarcodeFormat Enumeration items
	* @par Default value:
	* 	    BF_ALL
	* @par Remarks:
	*	    If the barcode type(s) are certain, specifying the barcode type(s) to be read will speed up the recognition process.
	* @sa BarcodeFormat
	*/
	int barcodeFormatIds;

	/**Sets the output image resolution.
	*
	* @par Value range:
	* 	    [100, 600]
	* @par Default value:
	* 	    300
	* @par Remarks:
	*	    When decoding barcodes from a PDF file using the DecodeFile method, the library will convert the PDF file to image(s) first, then perform barcode recognition.
	*/
	int pdfRasterDPI;

	/**Sets the threshold for the image shrinking.
	*
	* @par Value range:
	* 	    [512, 0x7fffffff]
	* @par Default value:
	* 	    2300
	* @par Remarks:
	*	    If the shorter edge size is larger than the given threshold value, the library will calculate the required height and width of the barcode image and shrink the image to that size before localization. Otherwise, the library will perform barcode localization on the original image.
	*/
	int scaleDownThreshold;

	/**Sets the mode and priority for binarization.
	*
	* @par Value range:
	* 	    Each array item can be any one of the BinarizationMode Enumeration items.
	* @par Default value:
	* 	    [BM_LOCAL_BLOCK,BM_SKIP,BM_SKIP,BM_SKIP,BM_SKIP,BM_SKIP,BM_SKIP,BM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa BinarizationMode
	*/
	BinarizationMode binarizationModes[8];

	/**Sets the mode and priority for localization algorithms.
	*
	* @par Value range:
	* 	    Each array item can be any one of the LocalizationMode Enumeration items.
	* @par Default value:
	* 	    [LM_CONNECTED_BLOCKS, LM_SCAN_DIRECTLY, LM_STATISTICS, LM_LINES, LM_SKIP, LM_SKIP, LM_SKIP, LM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller the index, the higher the priority.
	* @sa LocalizationMode
	*/
	LocalizationMode localizationModes[8];

	/**Sets further modes.
	*
	*/
	FurtherModes furtherModes;

	/**Sets the degree of blurriness of the barcode.
	*
	* @par Value range:
	* 	    [0, 9]
	* @par Default value:
	* 	    9
	* @par Remarks:
	*	    If you have a blurry image, you can set this property to a larger value. The higher the value set, the more effort the library will spend to decode images, but it may also slow down the recognition process.
	*/
	int deblurLevel;

	/**Sets which types of intermediate result to be kept for further reference. Intermediate result types can be combined.
	*
	* @par Value range:
	* 	    A combined value of IntermediateResultType Enumeration items
	* @par Default value:
	* 	    0
	* @sa IntermediateResultType
	*/
	int intermediateResultTypes;

	/**Sets the mode for saving intermediate result.
	*
	* @par Value range:
	* 	    A value of IntermediateResultSavingMode Enumeration items
	* @par Default value:
	* 	    IRSM_MEMORY
	* @sa IntermediateResultSavingMode
	*/
	IntermediateResultSavingMode intermediateResultSavingMode;

	/**Specifies the format for the coordinates returned.
	*
	* @par Value range:
	* 	    Any one of the ResultCoordinateType Enumeration items
	* @par Default value:
	* 	    RCT_PIXEL
	* @sa ResultCoordinateType
	*/
	ResultCoordinateType resultCoordinateType;

	/**Sets the mode and priority for the order of the text results returned.
	*
	* @par Value range:
	* 	    Each array item can be any one of the TextResultOrderMode Enumeration items.
	* @par Default value:
	* 	    [TROM_CONFIDENCE, TROM_POSITION, TROM_FORMAT, TROM_SKIP, TROM_SKIP, TROM_SKIP, TROM_SKIP, TROM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller the index, the higher the priority.
	* @sa TextResultOrderMode
	*/
	TextResultOrderMode textResultOrderModes[8];

	/**Sets the region definition including regionTop, regionLeft, regionRight, regionBottom, and regionMeasuredByPercentage.
	*
	*/
	RegionDefinition region;

	/**Sets the range of barcode text length for barcodes search.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*     0: means no limitation on the barcode text length.
	*/
	int minBarcodeTextLength;

	/**The minimum confidence of the result.
	*
	* @par Value range:
	* 	    [0, 100]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*     0: means no limitation on the result confidence.
	*/
	int minResultConfidence;

	/**Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[124];
}PublicRuntimeSettings;

/**
* @} defgroup CPublicRuntimeSettings
*/

/**
* @defgroup CFrameDecodingParameters FrameDecodingParameters
* @{
*/
/**
* Defines a struct to configure the frame decoding Parameters.
*
*/
typedef struct tagFrameDecodingParameters
{
	/**The maximum number of frames waiting for decoding.
	*
	* @par Value range:
	* 	    [0,0x7fffffff]
	* @par Default value:
	* 	    3
	*/
	int maxQueueLength;

	/**The maximum number of frames waiting results (text result/localization result) will be kept for further reference.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    10
	*/
	int maxResultQueueLength;

	/**The width of the frame image in pixels.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    0
	*/
	int width;

	/**The height of the frame image in pixels.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    0
	*/
	int height;

	/**The stride (or scan width) of the frame image.
	*
	* @par Value range:
	* 	    [0,0x7fffffff]
	* @par Default value:
	* 	    0
	*/
	int stride;

	/**The image pixel format used in the image byte array.
	*
	* @par Value range:
	* 	    A value of ImagePixelFormat Enumeration items
	* @par Default value:
	* 	    IPF_GRAYSCALED
	* @sa ImagePixelFormat
	*/
	ImagePixelFormat imagePixelFormat;	

	/**The region definition of the frame to calculate the internal indicator.
	*
	* @par Default Value:
	*		{
	*			regionLeft = 0,
	*			regionRight = 100,
	*			regionTop = 0,
	*			regionBottom = 100,
	*			regionMeasuredByPercentage = 1
	*		}
	* @sa RegionDefinition
	*/
	RegionDefinition region;

	/**The threshold used for filtering frames.
	*
	* @par Value range:
	* 	    [0, 1]
	* @par Default value:
	* 	    0.1
	* @par Remarks:
	*	      The SDK will calculate an inner indicator for each frame from AppendFrame(), if the change rate of the indicators
	*		between the current frame and the history frames is larger than the given threshold, the current frame will not be added to the inner frame queue waiting for decoding.
	*/
	float threshold;

	/**The frequency of calling AppendFrame() per second.
	*
	* @par Value range:
	* 	    [0,0x7fffffff]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*		  0 means the frequency will be calculated automatically by the SDK.
	*/
	int fps;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[32];
}FrameDecodingParameters;

/**
* @} defgroup CFrameDecodingSettings
*/

/**
* @defgroup ExtendedResult ExtendedResult
* @{
*/
/**
* Stores the extended result.
*
*/
typedef struct tagExtendedResult
{
	/**Extended result type */
	ResultType resultType;

	/**Barcode type */
	BarcodeFormat barcodeFormat;
	
	/**Barcode type as string */
	const char* barcodeFormatString;

	/**The confidence of the result */
	int confidence;

	/**The content in a byte array */
	unsigned char* bytes;

	/**The length of the byte array */
	int bytesLength;
	
	/**The accompanying text content in a byte array */
	unsigned char* accompanyingTextBytes;
	
	/**The length of the accompanying text byte array */
	int accompanyingTextBytesLength;

	/**The deformation value */
	int deformation;

	/**One of the following: @ref QRCodeDetails, @ref PDF417Details, @ref DataMatrixDetails, @ref AztecDetails, @ref OneDCodeDetails */
	void* detailedResult;
	
	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[64];
}ExtendedResult, *PExtendedResult;

/**
* @} defgroup ExtendedResult
*/

/**
* @defgroup LocalizationResult LocalizationResult
* @{
*/
/**
* Stores the localization result
*
*/
typedef struct tagLocalizationResult
{
	/**The terminate phase of localization result. */
	TerminatePhase terminatePhase;
	
	/**Barcode type */
	BarcodeFormat barcodeFormat;
	
	/**Barcode type as string */
	const char* barcodeFormatString;

	/**The X coordinate of the left-most point */
	int x1;
	
	/**The Y coordinate of the left-most point */
	int y1;
	
	/**The X coordinate of the second point in a clockwise direction */
	int x2;
	
	/**The Y coordinate of the second point in a clockwise direction */
	int y2;
	
	/**The X coordinate of the third point in a clockwise direction */
	int x3;
	
	/**The Y coordinate of the third point in a clockwise direction */
	int y3;
	
	/**The X coordinate of the fourth point in a clockwise direction */
	int x4;
	
	/**The Y coordinate of the fourth point in a clockwise direction */
	int y4;
	
	/**The angle of a barcode. Values range is from 0 to 360. */
	int angle;

	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;
	
	/**The page number the barcode located in. The index is 0-based. */
	int pageNumber;

	/**The region name the barcode located in. */
	const char* regionName;

	/**The document name */
	const char* documentName;
	
	/**The coordinate type */
	ResultCoordinateType resultCoordinateType;

	/**The accompanying text content in a byte array */
	unsigned char* accompanyingTextBytes;

	/**The length of the accompanying text byte array */
	int accompanyingTextBytesLength;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[64];
}LocalizationResult, *PLocalizationResult;

/**
* @} defgroup LocalizationResult
*/

/**
* @defgroup TextResult TextResult
* @{
*/
/**
* Stores the text result.
*
*/
typedef struct tagTextResult
{

	/**The barcode format */
	BarcodeFormat barcodeFormat;

	/**Barcode type as string */
	const char* barcodeFormatString;
	
	/**The barcode text, ends by '\0' */
	const char* barcodeText;

	/**The barcode content in a byte array */
	unsigned char* barcodeBytes;
	
	/**The length of the byte array */
	int barcodeBytesLength;

	/**The corresponding localization result */
	LocalizationResult* localizationResult;
	
	/**One of the following: @ref QRCodeDetails, @ref PDF417Details, @ref DataMatrixDetails, @ref AztecDetails, @ref OneDCodeDetails */
	void* detailedResult;

	/**The total count of extended result */
	int resultsCount;

	/**The extended result array */
	PExtendedResult* results;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[64];
}TextResult, *PTextResult;

/**
* @} defgroup TextResult
*/

/**
* @defgroup TextResultArray TextResultArray
* @{
*/
/**
* Stores the text result array.
*
*/
typedef struct tagTextResultArray
{
	/**The total count of text result */
	int resultsCount;

	/**The text result array */
	PTextResult *results;
}TextResultArray, *PTextResultArray;

/**
* @} defgroup TextResultArray
*/

/**
* @defgroup OneDCodeDetails OneDCodeDetails
* @{
*/
/**
* Stores the OneD code details.
*
*/
typedef struct tagOneDCodeDetails
{
	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;

	/**The start chars in a byte array */
	unsigned char* startCharsBytes;

	/**The length of the start chars byte array */
	int startCharsBytesLength;

	/**The stop chars in a byte array */
	unsigned char* stopCharsBytes;

	/**The length of the stop chars byte array */
	int stopCharsBytesLength;

	/**The check digit chars in a byte array */
	unsigned char* checkDigitBytes;

	/**The length of the check digit chars byte array */
	int checkDigitBytesLength;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[32];
}OneDCodeDetails;

/**
* @} defgroup OneDCodeDetails
*/

/**
* @defgroup QRCodeDetails QRCodeDetails
* @{
*/
/**
* Stores the QRCode details.
*
*/
typedef struct tagQRCodeDetails
{
	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;

	/**The row count of the barcode */
	int rows;

	/**The column count of the barcode */
	int columns;

	/**The error correction level of the barcode */
	QRCodeErrorCorrectionLevel errorCorrectionLevel;

	/**The version of the QR Code */
	int version;

	/**Number of the models */
	int model;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[32];
}QRCodeDetails;

/**
* @} defgroup QRCodeDetails
*/

/**
* @defgroup PDF417Details PDF417Details
* @{
*/
/**
* Stores the PDF417 details.
*
*/
typedef struct tagPDF417Details
{
	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;

	/**The row count of the barcode */
	int rows;

	/**The column count of the barcode */
	int columns;

	/**The error correction level of the barcode */
	int errorCorrectionLevel;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[32];
}PDF417Details;

/**
* @} defgroup PDF417Details
*/

/**
* @defgroup DataMatrixDetails DataMatrixDetails
* @{
*/
/**
* Stores the DataMatrix details.
*
*/
typedef struct tagDataMatrixDetails
{
	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;

	/**The row count of the barcode */
	int rows;

	/**The column count of the barcode */
	int columns;

	/**The data region row count of the barcode */
	int dataRegionRows;

	/**The data region column count of the barcode */
	int dataRegionColumns;

	/**The data region count */
	int dataRegionNumber;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[32];
}DataMatrixDetails;

/**
* @} defgroup DataMatrixDetails
*/

/**
* @defgroup AztecDetails AztecDetails
* @{
*/
/**
* Stores the Aztec details.
*
*/
typedef struct tagAztecDetails
{
	/**The barcode module size (the minimum bar width in pixel) */
	int moduleSize;

	/**The row count of the barcode */
	int rows;

	/**The column count of the barcode */
	int columns;

	/**A negative number (-1, -2, -3, -4) specifies a compact Aztec code.
    *  A positive number (1, 2, .. 32) specifies a normal (full-rang) Aztec code*/
	int layerNumber;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[32];
}AztecDetails;

/**
* @} defgroup AztecDetails
*/

/**
* @defgroup IntermediateResult IntermediateResult
* @{
*/
/**
* Stores the intermediate result.
*
*/
typedef struct tagIntermediateResult
{
	/**The total result count */
	int resultsCount;

	/**One of the following types: Array of @ref Contour, Array of @ref ImageData, Array of @ref LineSegment, Array of @ref LocalizationResult, Array of @ref RegionOfInterest */
	const void** results;

	/**The data type of the intermediate result */
	IMResultDataType dataType;

	/**Intermediate result type */
	IntermediateResultType resultType;

	/**The BarcodeComplementMode used when generating the current intermediate result */
	BarcodeComplementMode barcodeComplementMode;

	/**The array index of current used ColourClusteringMode in the ColourClusteringModes setting */
	int bcmIndex;

	/**The DeformationResistingMode used when generating the current intermediate result */
	DeformationResistingMode deformationResistingMode;

	/**The array index of current used DeformationResistingMode in the DeformationResistingModes setting */
	int drmIndex;

	/**The DPMCodeReadingMode used when generating the current intermediate result */
	DPMCodeReadingMode dpmCodeReadingMode;

	/**The array index of current used DPMCodeReadingMode in the DPMCodeReadingModes setting */
	int dpmcrmIndex;

	/**The rotation matrix */
	double rotationMatrix[9];

	/**The TextFilterMode used when generating the current intermediate result */
	TextFilterMode textFilterMode;

	/**The array index of current used TextFilterMode in the TextFilterModes setting */
	int tfmIndex;

	/**The LocalizationMode used when generating the current intermediate result */
	LocalizationMode localizationMode;

	/**The array index of current used LocalizationMode in the LocalizationModes setting */ 
	int lmIndex;

	/**The BinarizationMode used when generating the current intermediate result */
	BinarizationMode binarizationMode;

	/**The array index of current used BinarizationMode in the BinarizationModes setting */
	int bmIndex;

	/**The ImagePreprocessingMode used when generating the current intermediate result */
	ImagePreprocessingMode imagePreprocessingMode;

	/**The array index of current used ImagePreprocessingMode in ImagePreprocessingModes setting */
	int ipmIndex;

	/**The ID of the ROI (Region Of Interest) generated by the SDK. -1 means the original image. */
	int roiId;

	/**The RegionPredetectionMode used when generating the current intermediate result */
	RegionPredetectionMode regionPredetectionMode;

	/**The array index of current used RegionPredetectionMode in the RegionPredetectionModes setting */
	int rpmIndex;

	/**The GrayscaleTransformationMode used when generating the current intermediate result */
	GrayscaleTransformationMode grayscaleTransformationMode;

	/**The array index of current used GrayscaleTransformationMode in the GrayscaleTransformationModes setting */
	int gtmIndex;

	/**The ColourConversionMode used when generating the current intermediate result */
	ColourConversionMode colourConversionMode;

	/**The array index of current used ColourConversionMode in the ColourConversionModes setting */
	int cicmIndex;

	/**The ColourClusteringMode used when generating the current intermediate result */
	ColourClusteringMode colourClusteringMode;

	/**The array index of current used ColourClusteringMode in the ColourClusteringModes setting */
	int ccmIndex;

	/**The scale down ratio */
	int scaleDownRatio;

	/**The ID of the operated frame */
	int frameId;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[64];
}IntermediateResult, *PIntermediateResult;

/**
* @} defgroup IntermediateResult
*/

/**
* @defgroup IntermediateResultArray IntermediateResultArray
* @{
*/
/**
* Stores the intermediate result array.
*
*/
typedef struct tagIntermediateResultArray
{
	/**The total count of intermediate result */
	int resultsCount;

	/**The intermediate result array */
	PIntermediateResult *results;
}IntermediateResultArray;

/**
* @} defgroup IntermediateResultArray
*/

/**
* @defgroup DBRPoint DBRPoint
* @{
*/
/**
* Stores an x- and y-coordinate pair in two-dimensional space.
*
*/
typedef struct tagDBRPoint
{
	/**The X coordinate of the point */
	int x;

	/**The Y coordinate of the point */
	int y;
}DBRPoint,*PDBRPoint;

/**
* @} defgroup DBRPoint
*/

/**
* @defgroup RegionOfInterest RegionOfInterest
* @{
*/
/**
* Stores the region of interest.
*
*/
typedef struct tagRegionOfInterest
{
	/**The ID generated by the SDK */
	int roiId;

	/**The left top point of the region */
	DBRPoint point;

	/**The width of the region */
	int width;

	/**The height of the region */
	int height;
}RegionOfInterest;

/**
* @} defgroup RegionOfInterest
*/

/**
* @defgroup Contour Contour
* @{
*/
/**
* Stores the contour
*
*/
typedef struct tagContour
{
	/**The total points count of the contour */
	int pointsCount;

	/**The points array */
	DBRPoint* points;
}Contour;

/**
* @} defgroup Contour
*/

/**
* @defgroup ImageData ImageData
* @{
*/
/**
* Stores the image data.
*
*/
typedef struct tagImageData
{
	/**The length of the image data byte array */
	int bytesLength;

	/**The image data content in a byte array */
	unsigned char* bytes;

	/**The width of the image in pixels */
	int width;

	/**The height of the image in pixels */
	int height;

	/**The stride (or scan width) of the image */
	int stride;

	/**The image pixel format used in the image byte array */
	ImagePixelFormat format;
}ImageData;

/**
* @} defgroup ImageData
*/

/**
* @defgroup LineSegment LineSegment
* @{
*/
/**
* Stores line segment data.
*
*/
typedef struct tagLineSegment
{
	/**The start point of the line segment */
	DBRPoint startPoint;

	/**The end point of the line segment */
	DBRPoint endPoint;
}LineSegment;

/**
 * @}defgroup LineSegment
 * @}defgroup Struct Struct
 */

#pragma pack(pop)

#pragma endregion

#pragma region FunctionPointer
 /**
 * @defgroup FunctionPointer Function Pointer
 * @{
 */
 /**
 * Represents the method that will handle the error code returned by the SDK.
 *
 * @param frameId The ID of the frame.
 * @param errorCode Error Code generated when decoding the frame.
 * @param pUser Customized arguments passed to your function.
 *
 * @sa ErrorCode
 */
typedef void(*CB_Error)(int frameId, int errorCode, void * pUser);

/**
* Represents the method that will handle the text result array returned by the SDK.
*
* @param frameId The ID of the frame.
* @param pResults Recognized barcode results of the frame.
* @param pUser Arguments passed to your function.
*
* @sa TextResultArray
*/
typedef void(*CB_TextResult)(int frameId, TextResultArray *pResults, void * pUser);

/**
* Represents the method that will handle the intermediate result array returned by the SDK.
*
* @param frameId The ID of the frame.
* @param pResults The intermediate results of the frame.
* @param pUser Arguments passed to your function.
*
* @sa IntermediateResultArray
*/
typedef void(*CB_IntermediateResult)(int frameId, IntermediateResultArray *pResults, void * pUser);

/**
* @}defgroup Function Pointer
*/

#pragma endregion

#pragma region C/C++ Function
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
	* Four methods are now supported for editing runtime settings - reset, initialize, append, and update. 
	* - Reset runtime settings: reset all parameters in runtime setting to default values.     
	*  
	* - Initialize with template: reset runtime settings firstly and replace all parameters in runtime setting with the values specified in the given template regardless of the current runtime settings.   
	*  
	* - Append template to runtime settings: append a template and update the runtime settings; the conflicting values will be assigned by the rules shown in PublicRuntimeSettings.    
	*
	* - Update with struct: update current runtime settings with the values specified in the given struct directly; the parameters not defined in the struct will remain their original values.   
	* 
	* @par References
	* More information about public parameters and template file can be found in the DBR_Developer's_Guide.pdf file.
	*
	* 
	* @sa PublicRuntimeSettings
	*/

	/**
	* @defgroup CGeneral General Functions
	* @{
	*   APIs for getting global info.
	*/

	/**
	 * Returns the error info string.
	 * 
	 * @param [in] errorCode The error code.
	 * 			   
	 * @return The error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			const char* errorString = DBR_GetErrorString(errorCode);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API const char* DBR_GetErrorString(int errorCode);

	/**
	 * Returns the version info of the SDK.
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
	 * @}defgroup CGeneral
	 */

	/**
	* @defgroup CInitiation Initiation Functions
	* @{
	*   APIs for initiating Dynamsoft Barcode Reader SDK.
	*/

	/**
	 * Creates an instance of Dynamsoft Barcode Reader.
	 * 
	 * @return Returns an instance of Dynamsoft Barcode Reader. If failed, returns NULL.
	 *
	 * @par Remarks:
	 *		Partial of the decoding result will be masked with "*" without a valid license key.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API void* DBR_CreateInstance();

	/**
	 * Destroys an instance of Dynamsoft Barcode Reader.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API void DBR_DestroyInstance(void* barcodeReader);

	/**
	 * Reads product key and activates the SDK.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pLicense The product keys.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_InitLicense(void* barcodeReader, const char* pLicense);

	/**
	 * Initializes barcode reader license and connects to the specified server for online verification.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pLicenseServer The name/IP of the license server.
	 * @param [in] pLicenseKey The license key.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 */
	DBR_API int DBR_InitLicenseFromServer(void* barcodeReader, const char* pLicenseServer, const char* pLicenseKey);

	/**
	 * Initializes barcode reader license from the license content on the client machine for offline verification.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pLicenseKey The license key.
	 * @param [in] pLicenseContent An encrypted string representing the license content (quota, expiration date, barcode type, etc.) obtained from the method DBR_OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 */
	DBR_API int DBR_InitLicenseFromLicenseContent(void* barcodeReader, const char* pLicenseKey, const char* pLicenseContent);


	/**
	 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in, out] content The output string which stores the content of license.
	 * @param [in] contentLen The length of output string. The recommended length is 512 per license key.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 * @par Remarks:
	 *	    DBR_InitLicenseFromServer() has to be successfully called before calling this method.
	 */
	DBR_API int DBR_OutputLicenseToString(void* barcodeReader, char content[], int contentLen);

	/**
	 * @}defgroup CInitiation
	 */

	
	/**
	* @defgroup CDecoding Decoding Functions
	* @{
	*   APIs for barcode decoding.
	*/
	
	/**
	 * Decodes barcodes in the specified image file.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pFileName A string defining the file name.
	 * @param [in] pTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeFile(void* barcodeReader, const char* pFileName, const char* pTemplateName);

	/**
	 * Decodes barcodes from an image file in memory.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pFileBytes The image file bytes in memory.
	 * @param [in] fileSize The length of the file bytes in memory.
	 * @param [in] pTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			unsigned char* pFileBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			int errorCode = DBR_DecodeFileInMemory(barcodeReader, pFileBytes, nFileSize, "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeFileInMemory(void* barcodeReader, const unsigned char* pFileBytes, const int fileSize, const char* pTemplateName);

	/**
	 * Decodes barcodes from the memory buffer containing image pixels in defined format.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
	 * @param [in] width The width of the image in pixels.
	 * @param [in] height The height of the image in pixels.
	 * @param [in] stride The stride (or scan width) of the image.
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			unsigned char* pBufferBytes;
			int iWidth = 0;
			int iHeight = 0;
			int iStride = 0;
			ImagePixelFormat format;
			GetBufferFromFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pBufferBytes, &iWidth, &iHeight, &iStride, &format);
			int errorCode = DBR_DecodeBuffer(barcodeReader, pBufferBytes, iWidth, iHeight, iStride, format, "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeBuffer(void* barcodeReader, const unsigned char* pBufferBytes, const int width, const int height, const int stride, const ImagePixelFormat format, const char* pTemplateName);

	/**
	 * Decodes barcodes from an image file encoded as a base64 string.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pBase64String A base64 encoded string that represents an image.
	 * @param [in] pTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			unsigned char* pBufferBytes;
			int nFileSize = 0;
			GetFileStream("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pFileBytes, &nFileSize);
			char* strBase64String;
			GetFileBase64String(pBufferBytes, &strBase64String);
			int errorCode = DBR_DecodeBase64String(barcodeReader, strBase64String, "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeBase64String(void* barcodeReader, const char* pBase64String, const char* pTemplateName);

	/**
	 * Decodes barcodes from a handle of device-independent bitmap (DIB).
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] hDIB Handle of the device-independent bitmap.
	 * @param [in] pTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			HANDLE pDIB;
			GetDIBFromImage("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", &pDIB);
			int errorCode = DBR_DecodeDIB(barcodeReader, pDIB, "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int  DBR_DecodeDIB(void* barcodeReader, const HANDLE hDIB, const char* pTemplateName);

	/**
	* Init frame decoding parameters.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in,out] pParameters The frame decoding parameters.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call 
	* 		  DBR_GetErrorString() to get detailed error message. Possible returns are:
	*		  DBR_OK;
	*		  DBRERR_NULL_POINTER;
	*
	*/
	DBR_API int DBR_InitFrameDecodingParameters(void *barcodeReader, FrameDecodingParameters *pParameters);

	/**
	 * Starts a new thread to decode barcodes from the inner frame queue.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] maxQueueLength The max number of frames waiting for decoding.
	 * @param [in] maxResultQueueLength The max number of frames whose results (text result/localization result) will be kept.
	 * @param [in] width The width of the frame image in pixels.
	 * @param [in] height The height of the frame image in pixels.
	 * @param [in] stride The stride (or scan width) of the frame image.
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pTemplateName The template name.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 * 		   DBRERR_PARAMETER_VALUE_INVALID;
	 * 		   DBRERR_NULL_POINTER;
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_StartFrameDecoding(barcodeReader, 2, 10, 1024, 720, 720, IPF_BINARY, "");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_StartFrameDecoding(void *barcodeReader, const int maxQueueLength, const int maxResultQueueLength, const int width, const int height, const int stride, const ImagePixelFormat format, const char *pTemplateName);

	/**
	* Starts a new thread to decode barcodes from the inner frame queue.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] parameters The frame decoding parameters.
	* @param [in] pTemplateName The template name.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call 
	* 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	* 		   DBR_OK;
	* 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	* 		   DBRERR_PARAMETER_VALUE_INVALID;
	* 		   DBRERR_NULL_POINTER;
	*
	* @par Code Snippet:
	* @code
	*		void* barcodeReader = DBR_CreateInstance();
	*		DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
	*		FrameDecodingParameters parameters;
	*		int errorCode = DBR_InitFrameDecodingParameters(barcodeReader, &parameters);
	*		if(errorCode == DBR_OK)
	*		{
	*			parameters.maxQueueLength = 3;
	*			parameters.maxResultQueueLength = 10;
	*			parameters.width = 20;
	*			parameters.height = 30;
	*			parameters.stride = 10;
	*			parameters.imagePixelFormat = IPF_GRAYSCALED;
	*			parameters.region.regionMeasuredByPercentage = 1;
	*			parameters.region.regionTop = 0;
	*			parameters.region.regionBottom = 100;
	*			parameters.region.regionLeft = 0;
	*			parameters.region.regionRight = 100;
	*			parameters.threshold = 0.1;
	*			parameters.fps = 0;
	*			int errorCode = DBR_StartFrameDecodingEx(barcodeReader, parameters, "");
	*			DBR_DestroyInstance(barcodeReader);
	*		}
	* @endcode
	*
	*/
	DBR_API int DBR_StartFrameDecodingEx(void *barcodeReader, FrameDecodingParameters parameters, const char* pTemplateName);

	/**
	 * Appends a frame image buffer to the inner frame queue.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
     *				   
	 * @return Returns the ID of the appended frame.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int frameId = DBR_AppendFrame(barcodeReader, pBufferBytes);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */	
	DBR_API int DBR_AppendFrame(void *barcodeReader, unsigned char *pBufferBytes);

	/**
	 * Gets current length of the inner frame queue.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
     *				   
	 * @return Returns the length of the inner frame queue.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int frameLength = DBR_GetLengthOfFrameQueue(barcodeReader);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */	
	DBR_API int DBR_GetLengthOfFrameQueue(void *barcodeReader);

	/**
	 * Stops the frame decoding thread created by StartFrameDecoding().
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_STOP_DECODING_THREAD_FAILED;
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			int errorCode = DBR_StopFrameDecoding(barcodeReader);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_StopFrameDecoding(void *barcodeReader);

	/**
	 * @}defgroup CDecoding
	 */

	/**
	* @defgroup CBasicSetting Basic Setting Functions
	* @{
	*   Basic APIs used for customizing runtime settings 
	*/

	/**
	 * Sets the optional argument for a specified mode in Modes parameters.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pModesName The mode parameter name to set argument.
	 * @param [in] index The array index of mode parameter to indicate a specific mode.
	 * @param [in] pArgumentName The name of the argument to set.
	 * @param [in] pArgumentValue The value of the argument to set.
	 * @param [in,out] errorMsgBuffer The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
	 * @param [in] errorMsgBufferLen The length of the allocated buffer.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_SET_MODE_ARGUMENT_ERROR;
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->binarizationModes[0] = BM_LOCAL_BLOCK;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings, errorMessage, 256);
			DBR_SetModeArgument(barcodeReader, "BinarizationModes", 0, "EnableFillBinaryVacancy", "1", errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 * @par Remarks:
	 *		Check @ref ModesArgument for details
	 *
	 */	
	DBR_API int DBR_SetModeArgument(void *barcodeReader, const char *pModesName,const int index, const char *pArgumentName, const char *pArgumentValue, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	 * Gets current settings and save them into a struct.
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in,out] pSettings The struct of template settings.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(barcodeReader, pSettings);
			delete pSettings;
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_GetRuntimeSettings(void* barcodeReader, PublicRuntimeSettings *pSettings);

	/**
	 * Updates runtime settings with a given struct.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] errorMsgBuffer The buffer is allocated by caller and the recommended length 
	 * 				   is 256.The error message will be copied to the buffer.
	 * @param [in] errorMsgBufferLen The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 *		  DBR_GetErrorString() to get detailed error message.
	 * 
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->deblurLevel = 9;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings, errorMessage, 256);
			delete pSettings;
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_UpdateRuntimeSettings(void* barcodeReader,PublicRuntimeSettings *pSettings,char errorMsgBuffer[],const int errorMsgBufferLen);

	/**
	 * Resets all parameters to default values.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call  
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->deblurLevel = 9;
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings);
			DBR_ResetRuntimeSettings(barcodeReader);
			delete pSettings;
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_ResetRuntimeSettings(void* barcodeReader);

	/**
	* @}defgroup CBasicSetting
	*/

	/**
	* @defgroup CAdvancedSettings Advanced Setting Functions
	* @{
	*   Advanced APIs for customizing scanning parameters with a template file to fit specified scenarios.
	*/
	/**
	* Initialize runtime settings with the parameters obtained from a JSON file.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] pFilePath The settings file path.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from 
	* 			  previous template settings or to overwrite previous settings with the new template.  
	* @param [in,out] errorMsgBuffer The buffer is allocated by caller and the recommending 
	* 				  length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call 
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_InitRuntimeSettingsWithFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithFile(void* barcodeReader, const char* pFilePath, const ConflictMode conflictMode, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Initializes runtime settings with the parameters obtained from a JSON string.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] content A JSON string that represents the content of the settings.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from 
	* 			  previous template setting or to overwrite previous settings with the new template.  
	* @param [in,out] errorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. YOu can call 
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_InitRuntimeSettingsWithString(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_OVERWRITE, errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithString(void* barcodeReader, const char* content, const ConflictMode conflictMode, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Appends a new template file to the current runtime settings.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] pFilePath The settings file path.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template settings or to overwrite previous settings with the new template.
	* @param [in,out] errorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_AppendTplFileToRuntimeSettings(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_IGNORE, errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_AppendTplFileToRuntimeSettings(void* barcodeReader, const char* pFilePath, const ConflictMode conflictMode, char errorMsgBuffer[],const int errorMsgBufferLen);

	/**
	* Appends a new template string to the current runtime settings.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] content A JSON string that represents the content of the settings.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template setting or to overwrite previous settings with the new template.
	* @param [in,out] errorMsgBuffer The buffer is allocated by caller and the recommending
	* 				  length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessage[256];
			DBR_AppendTplStringToRuntimeSettings(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	* @sa CFunctions PublicRuntimeSettings 
	*/
	DBR_API int  DBR_AppendTplStringToRuntimeSettings(void* barcodeReader, const char* content, const ConflictMode conflictMode, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Gets count of parameter templates.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	*
	* @return Returns the count of parameter templates.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			int currentTemplateCount = DBR_GetParameterTemplateCount(barcodeReader);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	*/
	DBR_API int  DBR_GetParameterTemplateCount(void* barcodeReader);

	/**
	* Gets parameter template name by index.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] index The index of parameter template array.
	* @param [in,out] nameBuffer The buffer is allocated by caller and the recommended
	* 				  length is 256. The template name will be copied to the buffer.
	* @param [in] nameBufferLen The length of allocated buffer
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			int currentTemplateCount = DBR_GetParameterTemplateCount(barcodeReader);
			int templateIndex = 1;
			// notice that the value of 'templateIndex' should less than currentTemplateCount.
			char errorMessage[256];
			DBR_GetParameterTemplateName(barcodeReader, templateIndex, errorMessage, 256);
			DBR_DestroyInstance(barcodeReader);
	* @endcode
	*
	*/
	DBR_API int  DBR_GetParameterTemplateName(void* barcodeReader, const int index, char nameBuffer[], const int nameBufferLen);

	/**
	 * Outputs runtime settings to a string.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in,out] content The output string which stores the contents of current settings.	   
	 * @param [in] contentLen The length of output string.
	 * @param [in] pSettingsName A unique name for declaring current runtime settings.	
     *	 
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			 DBR_InitRuntimeSettingsWithFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			char pContent[256];
			DBR_OutputSettingsToString(barcodeReader, pContent, 256, "currentRuntimeSettings");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_OutputSettingsToString(void* barcodeReader, char content[], const int contentLen, const char* pSettingsName);

	/**
	 * Outputs runtime settings and save them into a settings file (JSON file).
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pFilePath The path of the output file which stores current settings.
	 * @param [in] pSettingsName A unique name for declaring current runtime settings.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			DBR_InitRuntimeSettingsWithFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			DBR_AppendTplStringToRuntimeSettings(barcodeReader, "{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			DBR_OutputSettingsToFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\CurrentRuntimeSettings.json", "currentRuntimeSettings");
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_OutputSettingsToFile(void* barcodeReader, const char* pFilePath, const char* pSettingsName);

	/**
	 * @}defgroup CAdvancedSettings
	 */

	/**
	* @defgroup CResults Results Functions
	* @{
	*   APIs for operating results.
	*/

	/**
	 * Gets all recognized barcode results.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [out] pResults Barcode text results returned by last calling function 
	 * 				DBR_DecodeFile() / DBR_DecodeFileInMemory() / DBR_DecodeBuffer() / DBR_DecodeBase64String() / DBR_DecodeDIB().
	 * 				The results is allocated by SDK and should be freed by calling function DBR_FreeTextResults.
	 * 
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call 
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			TextResultArray* pResults;
			int errorCode = DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllTextResults(barcodeReader, &pResults);
			DBR_FreeTextResults(&pResults);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API int DBR_GetAllTextResults(void* barcodeReader, TextResultArray **pResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] pResults Text results.
	 *
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			TextResultArray* pResults;
			int errorCode = DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			DBR_GetAllTextResults(barcodeReader, &pResults);
			DBR_FreeTextResults(&pResults);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 */
	DBR_API void  DBR_FreeTextResults(TextResultArray **pResults);

	/**
	 * Returns intermediate results containing the original image, the colour clustered image, the binarized image, contours, lines, text blocks, etc.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [out] pResult The intermediate results returned by the SDK.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 *
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings, errorMessage, 256);
			DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			IntermediateResultArray* pResults;
			DBR_GetIntermediateResults(barcodeReader, &pResults);
			DBR_FreeIntermediateResults(&pResults);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API int DBR_GetIntermediateResults(void *barcodeReader, IntermediateResultArray **pResult);

	/**
	 * Frees memory allocated for the intermediate results.
	 * 
	 * @param [in] pResults The intermediate results.
     *				   
	 * @par Code Snippet:
	 * @code
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings, errorMessage, 256);
			DBR_DecodeFile(barcodeReader, "C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			IntermediateResultArray* pResults;
			DBR_GetIntermediateResults(barcodeReader, &pResults);
			DBR_FreeIntermediateResults(&pResults);
			DBR_DestroyInstance(barcodeReader);
	 * @endcode
	 *
	 */
	DBR_API void DBR_FreeIntermediateResults(IntermediateResultArray **pResults);

	/**
	 * @}defgroup CResults
	 */

	/**
	* @defgroup CCallback Callback Functions
	* @{
	*   APIs for setting callback functions.
	*/

	/**
	 * Sets callback function to process errors generated during frame decoding.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] cbFunction Callback function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void ErrorFunction(int frameId, int errorCode, void * pUser)
			{
				//TODO add your code for using error code
			}
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			DBR_SetErrorCallback(barcodeReader, ErrorFunction, NULL);
			DBR_StartFrameDecoding(barcodeReader, 2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	DBR_API	int DBR_SetErrorCallback(void *barcodeReader, CB_Error cbFunction, void * pUser);

	/**
	 * Sets callback function to process text results generated during frame decoding.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] cbFunction Callback function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void TextResultFunction(int frameId, TextResultArray *pResults, void * pUser)
			{
				//TODO add your code for using test results
			}
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			DBR_SetTextResultCallback(barcodeReader, TextResultFunction, NULL);
			DBR_StartFrameDecoding(barcodeReader, 2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	DBR_API	int DBR_SetTextResultCallback(void *barcodeReader, CB_TextResult cbFunction, void * pUser);

	/**
	 * Sets callback function to process intermediate results generated during frame decoding.
	 * 
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] cbFunction Callback function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void IntermediateResultFunction(int frameId, IntermediateResultArray *pResults, void * pUser)
			{
				//TODO add your code for using intermediate results
			}
			void* barcodeReader = DBR_CreateInstance();
			DBR_InitLicense(barcodeReader, "t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = DBR_GetRuntimeSettings(barcodeReader, pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			DBR_UpdateRuntimeSettings(barcodeReader, pSettings, errorMessage, 256);
			DBR_SetIntermediateResultCallback(barcodeReader, IntermediateResultFunction, NULL);
			DBR_StartFrameDecoding(barcodeReader, 2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	DBR_API	int DBR_SetIntermediateResultCallback(void *barcodeReader, CB_IntermediateResult cbFunction, void * pUser);

	/**
	 * @}defgroup CCallback
	 */

	/**
	 * @}defgroup CFunctions
	 */
#ifdef __cplusplus
}
#endif // endif of __cplusplus.

#ifdef __cplusplus
class BarcodeReaderInner;
//---------------------------------------------------------------------------
// Class
//---------------------------------------------------------------------------


/**
*
* @defgroup CBarcodeReaderClass CBarcodeReader Class
* @{
*
*/

/**
* Defines a class that provides functions for working with barcode data extracting.
* @class CBarcodeReader
*
* @nosubgrouping
*
* Four methods are now supported for editing runtime settings - reset, initialize, append, and update.
* - Reset runtime settings: reset all parameters in runtime setting to default values.
*
* - Initialize with template: reset runtime settings firstly and replace all parameters in runtime setting with the values specified in the given template regardless of the current runtime settings.
*
* - Append template to runtime settings: append template and update runtime settings; the conflicting values will be assigned by the rules shown in PublicRuntimeSettings.
*
* - Update with struct: update current runtime settings by the values specified in the given struct directly; the parameters not defined in the struct will remain their original values.
*
*
* @par References
* More information about public parameters and template file can be found in the DBR_Developer's_Guide.pdf file.
*
*
* @sa CPublicRuntimeSettings
*/
class DBR_API CBarcodeReader
{
protected:

	/** The internal barcode reader */
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
	 */

	/**
	* @name General Functions
	* @{
	*/

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
	static const char* GetErrorString(const int iErrorCode);

	/**
	 * Returns the version info of the SDK.
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
	 * @}
	 */

	/**
	* @name Initiation Functions
	* @{
	*/

	/**
	 * Reads product key and activates the SDK.
	 * 
	 * @param [in] pLicense The product keys.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	 * Initializes the license and connects to the specified server for online verification.
	 *
	 * @param [in] pLicenseServer The URL of the license server.
	 * @param [in] pLicenseKey The license key.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
	 */
	int InitLicenseFromServer(const char* pLicenseServer, const char* pLicenseKey);

	/**
	 * Initializes barcode reader license from the license content on the client machine for offline verification.
	 *
	 * @param [in] pLicenseKey The license key.
	 * @param [in] pLicenseContent An encrypted string representing the license content (quota, expiration date, barcode type, etc.) obtained from the method OutputLicenseToString().
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
	 */
	int InitLicenseFromLicenseContent(const char* pLicenseKey, const char* pLicenseContent);

	/**
	 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
	 *
	 * @param [in, out] content The output string which stores the content of license.
	 * @param [in] contentLen The length of output string. The recommended length is 512 per license key.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
	 * @par Remarks:
	 *	    InitLicenseFromServer() has to be successfully called before calling this method.
	 */
	int OutputLicenseToString(char content[], const int contentLen);

	/**
	 * @}
	 */

	
	/**
	* @name Decoding Functions
	* @{
	*/

	/**
	 * Decodes barcodes in a specified image file.
	 * 
	 * @param [in] pFileName A string defining the file name.
	 * @param [in] pTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	int  DecodeFile(const char* pFileName, const char* pTemplateName = "");

	/**
	 * Decodes barcodes from an image file in memory.
	 * 
	 * @param [in] pFileBytes The image file bytes in memory.
	 * @param [in] fileSize The length of the file bytes in memory.
	 * @param [in] pTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	int  DecodeFileInMemory(const unsigned char* pFileBytes, int fileSize, const char* pTemplateName = "");

	/**
	 * Decodes barcodes from the memory buffer containing image pixels in defined format.
	 * 
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
	 * @param [in] iWidth The width of the image in pixels.
	 * @param [in] iHeight The height of the image in pixels.
	 * @param [in] iStride The stride (or scan width) of the image.
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	int  DecodeBuffer(const unsigned char* pBufferBytes, const int iWidth, const int iHeight, const int iStride, const ImagePixelFormat format, const char* pszTemplateName = "");

	/**
	 * Decodes barcode from an image file encoded as a base64 string.
	 * 
	 * @param [in] pBase64String A base64 encoded string that represents an image.
	 * @param [in] pTemplateName (Optional) The template name.
	 * 			   
	  * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	int  DecodeBase64String(const char* pBase64String, const char* pTemplateName = "");

	/**
	 * Decodes barcode from a handle of device-independent bitmap (DIB).
	 * 
	 * @param [in] hDIB Handle of the device-independent bitmap.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	  * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	int  DecodeDIB(const HANDLE  hDIB, const char* pszTemplateName = "");

	/**
	* Initiates frame decoding parameters.
	*
	* @param [in,out] pParameters The frame decoding parameters.
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message. Possible returns are:
	* 		  DBR_OK;
	*
	*/
	int InitFrameDecodingParameters(FrameDecodingParameters *pParameters);

	/**
	 * Starts a new thread to decode barcodes from the inner frame queue.
	 * 
	 * @param [in] maxQueueLength The max number of frames waiting for decoding.
	 * @param [in] maxResultQueueLength The max number of frames whose results (text result/localization result) will be kept.
	 * @param [in] width The width of the frame image in pixels.
	 * @param [in] height The height of the frame image in pixels.
	 * @param [in] stride The stride (or scan width) of the frame image.
	 * @param [in] format The image pixel format used in the image byte array.
	 * @param [in] pTemplateName (Optional) The template name.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 * 		   DBRERR_PARAMETER_VALUE_INVALID;
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			reader->StartFrameDecoding(2, 10, 1024, 720, 720, IPF_BINARY, "");
			delete reader;
	 * @endcode
	 *
	 */
	int StartFrameDecoding(const int maxQueueLength, const int maxResultQueueLength, const int width, const int height, const int stride, const ImagePixelFormat format, const char *pTemplateName = "");
	
	/**
	* Starts a new thread to decode barcodes from the inner frame queue.
	*
	* @param [in] parameters The frame decoding parameters.
	* @param [in] pTemplateName (Optional) The template name.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message. Possible returns are:
	* 		   DBR_OK;
	* 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	* 		   DBRERR_PARAMETER_VALUE_INVALID;
	*
	* @par Code Snippet:
	* @code
	*		CBarcodeReader* reader = new CBarcodeReader();
	*		reader->InitLicense("t0260NwAAAHV***************");
	*		FrameDecodingParameters parameters;
	*		int errorCode = reader->InitFrameDecodingParameters(&parameters);
	*		if(errorCode == DBR_OK)
	*		{
	*			parameters.maxQueueLength = 3;
	*			parameters.maxResultQueueLength = 10;
	*			parameters.width = 20;
	*			parameters.height = 30;
	*			parameters.stride = 10;
	*			parameters.imagePixelFormat = IPF_GRAYSCALED;
	*			parameters.region.regionMeasuredByPercentage = 1;
	*			parameters.region.regionTop = 0;
	*			parameters.region.regionBottom = 100;
	*			parameters.region.regionLeft = 0;
	*			parameters.region.regionRight = 100;
	*			parameters.threshold = 0.1;
	*			parameters.fps = 0;
	*			reader->StartFrameDecodingEx(parameters, "");
	*			delete reader;
	*		}
	* @endcode
	*
	*/
	int StartFrameDecodingEx(FrameDecodingParameters parameters, const char* pTemplateName = "");

	/**
	 * Appends a frame image buffer to the inner frame queue.
	 * 
	 * @param [in] pBufferBytes The array of bytes which contain the image data.
     *				   
	 * @return Returns the ID of the appended frame.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			int frameId = reader->AppendFrame(pBufferBytes);
			delete reader;
	 * @endcode
	 *
	 */	
	int AppendFrame(unsigned char *pBufferBytes);

	/**
	 * Gets current length of the inner frame queue.
     *				   
	 * @return Returns the length of the inner frame queue.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			int frameLength = reader->GetLengthOfFrameQueue();
			delete reader;
	 * @endcode
	 *
	 */	
	int GetLengthOfFrameQueue();

	/**
	 * Stops the frame decoding thread created by StartFrameDecoding().
	 * 
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_STOP_DECODING_THREAD_FAILED;
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			int errorCode = reader->StopFrameDecoding();
			delete reader;
	 * @endcode
	 *
	 */
	int StopFrameDecoding();

	/**
	 * @}
	 */

	/**
	* @name Basic Setting Functions
	* @{
	*/

	/**
	 * Gets current settings and save them into a struct.
	 * 
	 * @param [in,out] psettings The struct of template settings.
	 * 				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
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
	 * Updates runtime settings with a given struct.
	 * 
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length 
	 * 				   is 256. The error message will be copied to the buffer.
	 * @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = reader->GetRuntimeSettings(pSettings);
			pSettings->deblurLevel = 9;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 */
	int UpdateRuntimeSettings(PublicRuntimeSettings *pSettings, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

	/**
	* Resets all parameters to default values.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			int errorCode = reader->GetRuntimeSettings(pSettings);
			pSettings->deblurLevel = 9;
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
	 * Sets the optional argument for a specified mode in Modes parameters.
	 * 
	 * @param [in] pModesName The mode parameter name to set argument.
	 * @param [in] index The array index of mode parameter to indicate a specific mode.
	 * @param [in] pArgumentName The name of the argument to set.
	 * @param [in] pArgumentValue The value of the argument to set.
	 * @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
	 * @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_SET_MODE_ARGUMENT_ERROR;
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			reader->GetRuntimeSettings(pSettings);
			pSettings->binarizationModes[0] = BM_LOCAL_BLOCK;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			reader->SetModeArgument("BinarizationModes", 0, "EnableFillBinaryVacancy", "1", errorMessage, 256);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 * @par Remarks:
	 *		Check @ref ModesArgument for details
	 *
	 */
	int SetModeArgument(const char *pModesName,const int index, const char *pArgumentName, const char *pArgumentValue, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

	/**
	* @}
	*/

	/**
	* @name Advanced Setting Functions
	* @{
	*/

	/**
	* Initialize runtime settings with the settings in a given JSON file.
	*
	* @param [in] pFilePath The path of the settings file.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template setting or to overwrite previous settings and replace with the new template.
	* @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				   is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  InitRuntimeSettingsWithFile(const char* pFilePath, const ConflictMode conflictMode, char errorMsgBuffer[] = NULL, int errorMsgBufferLen = 0);

	/**
	* Initializes runtime settings with the settings in a given JSON string.
	*
	* @param [in] content A JSON string that represents the content of the settings.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template setting or to overwrite previous settings with the new template.
	* @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->InitRuntimeSettingsWithString("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_OVERWRITE, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  InitRuntimeSettingsWithString(const char* content, const ConflictMode conflictMode, char errorMsgBuffer[] = NULL, int errorMsgBufferLen = 0);

	/**
	* Appends a new template file to the current runtime settings.
	*
	* @param [in] pFilePath The path of the settings file.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template setting or to overwrite previous settings with the new template.
	* @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->AppendTplFileToRuntimeSettings("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_IGNORE, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  AppendTplFileToRuntimeSettings(const char* pFilePath, const ConflictMode conflictMode, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

	/**
	* Appends a new template string to the current runtime settings.
	*
	* @param [in] content A JSON string that represents the content of the settings.
	* @param [in] conflictMode The parameter setting mode, which decides whether to inherit parameters from
	* 			  previous template setting or to overwrite previous settings with the new template.
	* @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessage[256];
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessage, 256);
			delete reader;
	* @endcode
	*
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  AppendTplStringToRuntimeSettings(const char* content, const ConflictMode conflictMode, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

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
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			int currentTemplateCount = reader->GetParameterTemplateCount();
			delete reader;
	* @endcode
	*
	*/
	int  GetParameterTemplateCount();

	/**
	* Gets the parameter template name by index.
	*
	* @param [in] index The index of the parameter template array.
	* @param [in,out] nameBuffer The buffer is allocated by caller and the recommended
	* 				   nameBufferLen is 256. The template name will be copied to the buffer.
	* @param [in] nameBufferLen The length of allocated buffer.

	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			int currentTemplateCount = reader->GetParameterTemplateCount();
			int templateIndex = 1;
			// notice that the value of 'templateIndex' should less than currentTemplateCount.
			char errorMessage[256];
			reader->GetParameterTemplateName(templateIndex, errorMessage, 256);
			delete reader;
	* @endcode
	*
	*/
	int  GetParameterTemplateName(const int index, char nameBuffer[], int nameBufferLen);


	/**
	* Outputs runtime settings and save them into a settings file (JSON file).
	*
	* @param [in] pFilePath The output file path which stores current settings.
	* @param [in] pSettingsName A unique name for declaring current runtime settings.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	*
	* @par Code Snippet:
	* @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			reader->OutputSettingsToFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\CurrentRuntimeSettings.json", "currentRuntimeSettings");
			delete reader;
	* @endcode
	*
	*/
	int OutputSettingsToFile(const char* pFilePath, const char* pSettingsName);


	/**
	 * Outputs runtime settings to a string.
	 * 
	 * @param [in,out] content The output string which stores the contents of current settings.
	 * @param [in] contentLen The length of the output string.
	 * @param [in] pSettingsName A unique name for declaring current runtime settings.
	 * 			   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			char errorMessageInit[256];
			char errorMessageAppend[256];
			reader->InitRuntimeSettingsWithFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Templates\\RuntimeSettings.json", CM_OVERWRITE, errorMessageInit, 256);
			reader->AppendTplStringToRuntimeSettings("{\"Version\":\"3.0\", \"ImageParameter\":{\"Name\":\"IP1\", \"BarcodeFormatIds\":[\"BF_QR_CODE\"], \"ExpectedBarcodesCount\":10}}", CM_IGNORE, errorMessageAppend, 256);
			char content[256];
			reader->OutputSettingsToString(content, 256, "currentRuntimeSettings");
			delete reader;
	 * @endcode
	 *
	 */
	int OutputSettingsToString(char content[], const int contentLen, const char* pSettingsName);
	
	/**
	 * @}
	 */

	/**
	* @name Results Functions
	* @{
	*/

	/**
	 * Gets all recognized barcode results.
	 * 
	 * @param [out] pResults Barcode text results returned by the last called function
	 * 				DecodeFile/DecodeFileInMemory/DecodeBuffer/DecodeBase64String/DecodeDIB. The pResults is
	 * 				allocated by the SDK and should be freed by calling the function FreeLocalizationResults.
	 * 
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		   GetErrorString() to get detailed error message.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			TextResultArray* pResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllTextResults(&pResults);
			CBarcodeReader::FreeTextResults(&pResults);
			delete reader;
	 * @endcode
	 *
	 */
	int GetAllTextResults(TextResultArray **pResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] pResults Text results.
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			TextResultArray* pResults;
			int errorCode = reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			reader->GetAllTextResults(&pResults);
			CBarcodeReader::FreeTextResults(&pResults);
			delete reader;
	 * @endcode
	 *
	 */
	static void FreeTextResults(TextResultArray **pResults);

	/**
	 * Returns intermediate results containing the original image, the colour clustered image, the binarized Image, contours, Lines, TextBlocks, etc.
	 * 
	 * @param [out] pResults The intermediate results returned by the SDK.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 *
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			reader->GetRuntimeSettings(pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			IntermediateResultArray* pResults;
			reader->GetIntermediateResults(&pResults);
			CBarcodeReader::FreeIntermediateResults(&pResults);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 */
	int GetIntermediateResults(IntermediateResultArray **pResults);

	/**
	 * Frees memory allocated for the intermediate results.
	 * 
	 * @param [in] pResults The intermediate results.
     *				   
	 * @par Code Snippet:
	 * @code
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			reader->GetRuntimeSettings(pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			reader->DecodeFile("C:\\Program Files (x86)\\Dynamsoft\\{Version number}\\Images\\AllSupportedBarcodeTypes.tif", "");
			IntermediateResultArray* pResults;
			reader->GetIntermediateResults(&pResults);
			CBarcodeReader::FreeIntermediateResults(&pResults);
			delete pSettings;
			delete reader;
	 * @endcode
	 *
	 */
	static void FreeIntermediateResults(IntermediateResultArray **pResults);

	
	/**
	 * @}
	 */

	/**
	* @name Callback Functions
	* @{
	*/

	/**
	 * Sets callback function to process errors generated during frame decoding.
	 * 
	 * @param [in] cbFunction Callback function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void ErrorFunction(int frameId, int errorCode, void * pUser)
			{
				//TODO add your code for using error code
			}
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			reader->SetErrorCallback(ErrorFunction, NULL);
			reader->StartFrameDecoding(2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	int SetErrorCallback(CB_Error cbFunction, void * pUser);

	/**
	 * Sets callback function to process text results generated during frame decoding.
	 * 
	 * @param [in] cbFunction Call back function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void TextResultFunction(int frameId, TextResultArray *pResults, void * pUser)
			{
				//TODO add your code for using test results
			}
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			reader->SetTextResultCallback(TextResultFunction, NULL);
			reader->StartFrameDecoding(2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	int SetTextResultCallback(CB_TextResult cbFunction, void * pUser);

	/**
	 * Sets callback function to process intermediate results generated during frame decoding.
	 * 
	 * @param [in] cbFunction Callback function.
	 * @param [in] pUser Customized arguments passed to your function.
     *				   
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   GetErrorString() to get detailed error message. Possible returns are:
	 * 		   DBR_OK; 
	 * 		   DBRERR_FRAME_DECODING_THREAD_EXISTS;
	 *
	 * @par Code Snippet:
	 * @code
			void IntermediateResultFunction(int frameId, IntermediateResultArray *pResults, void * pUser)
			{
				//TODO add your code for using intermediate results
			}
			CBarcodeReader* reader = new CBarcodeReader();
			reader->InitLicense("t0260NwAAAHV***************");
			PublicRuntimeSettings* pSettings = new PublicRuntimeSettings;
			reader->GetRuntimeSettings(pSettings);
			pSettings->intermediateResultTypes = IRT_ORIGINAL_IMAGE | IRT_COLOUR_CLUSTERED_IMAGE | IRT_COLOUR_CONVERTED_GRAYSCALE_IMAGE;
			char errorMessage[256];
			reader->UpdateRuntimeSettings(pSettings, errorMessage, 256);
			reader->SetIntermediateResultCallback(IntermediateResultFunction, NULL);
			reader->StartFrameDecoding(2, 10, 1024, 720, 720, IPF_BINARY, "");
	 * @endcode
	 *
	 */
	int SetIntermediateResultCallback(CB_IntermediateResult cbFunction, void * pUser);
	
	/**
	 * @}  
	 */

private:


	CBarcodeReader(const CBarcodeReader& r);

	CBarcodeReader& operator = (const CBarcodeReader& r);

};

/** 
* @}defgroup CBarcodeReaderClass
* @}defgroup CandCPlus
 *
 */
#endif // endif of __cplusplus.

#pragma endregion

#endif