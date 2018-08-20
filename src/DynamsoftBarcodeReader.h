/*
*	@file DynamsoftBarcodeReader.h
*	
*	Dynamsoft Barcode Reader 6.3 C/C++ API header file.
*	Copyright 2018 Dynamsoft Corporation. All rights reserved.
*	
*	@version 6.3.0.710
*	@author Dynamsfot
*	@date 07/10/2018
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

/**
* @defgroup DBRAPIs Dynamsoft Barcode Reader 6.3.0 - API Reference
* @{
* Dynamsoft Barcode Reaeder 6.3.0 Documentation for windows edition - API References.
* @defgroup CandCPlus C/C++ APIs
* @{
* Dynamsoft Barcode Reaeder 6.3.0 - C/C++ APIs Description.
*/
#define DBR_VERSION                  "6.3.0.710"

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

/**
 * @}
 */

/**
* @defgroup Enum Enumerations
* @{
*/

/**
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
	/**< The region name the barcode located in. */

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

/** Values that represent region predetection modes */
typedef enum 
{
    RPM_Disable = 1,
	/**< Disable region pre-detection */

    RPM_Enable = 2,
	/**< Enable region pre-detection */
}RegionPredetectionMode;


/** Values that represent text filter modes */
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
 * @brief This struct used for storing current runtime settings.
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
	/**@brief The timeout threshold. */ 
    int mTimeout;
	/**< It stores the maximum amount of time (in milliseconds) it should spend searching for a barcode per page. It does not include the time taken to load/decode an image (Tiff, PNG, etc.) from disk into memory. 
	 *
	 * @par Value range:
	 * 	   [0,7ffffff]
	 * @par Default value:
	 * 	   10000
	 */

	/**@brief The PDF raster DPI */	
    int mPDFRasterDPI;
	/**< It stores the output image resolution. When you are trying to decode a PDF file using DecodeFile 
	 *method, the library will convert the pdf file to image(s) first, then perform barcode recognition.
	 * 
	 * @par Value range:
	 * 		[100,600]
	 * @par Default value:
	 * 		300
	 */

	/**@brief The text filter mode */	
    TextFilterMode mTextFilterMode;
	/**< It stores the text filter mode for barcodes search, which decides whether to filter text before barcode localization. 
	 *  
	 *  @par Value range:
	 * 		TFM_Disable, TFM_Enable
	 * 	@par Default value:
	 *		TFM_Enable
	 *	@sa TextFilterMode
	 *
	 */

	/**@brief The region predetection mode */	
    RegionPredetectionMode mRegionPredetectionMode;
	/**< It stores the region pre-detection mode for barcodes search, which decides whether to pre-detect barcode region before accurate localization.
	 * If you want to pre-detect barcode regions, it is better to set the mColourImageConvertMode to "CICM_Auto" as the color features need to be used in region detection.
	 * 
	 * @par Value range:
	 * 		RPM_Disable, RPM_Enable
	 * @par Default value:
	 * 		RPM_Disable
	 * @sa RegionPredetectionMode mColourImageConvertMode
	 */

	/**@brief The localization algorithm priority */	
    char mLocalizationAlgorithmPriority[64];
	/**< It stores the priority of localization algorithms, which decides the order of using following four localization algorithms.
	 *
	 * @par Default values:
	 * 		""
	 * @par Optional localization algorithms:
	 * 		"ConnetectedBlock", "Statistics", "Lines", "FullImageAsBarcodeZone"
	 * @par Remarks:
	 * 		- Default value: The library will automatically use optimized localization priority, i.e. ConnetectedBlock -> Statistics -> Lines -> FullImageAsBarcodeZone, which is also the recommended order.    
	 * 	
	 * 		- ConnectedBlock: Localizes barcodes by searching connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlock to the highest priority.    
	 * 	
	 * 		- Lines: Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes.     
	 * 	
	 * 		- Statistics: Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix.    
	 * 	
	 * 		- FullImageAsBarcodeZone: Disables localization. In this mode, it will directly localize barcodes on the full image without localization. If there is nothing other than the barcode in the image, it is recommended to use this mode. 
	 * 		
	 */

	/**@brief List of identifiers for the barcode formats */	
    int mBarcodeFormatIds;
	/**< It stores the information of which types of barcode need to be read. Notice that one barcode reader can support more than one barcode format, i.e. the barcode format can be combined like BF_CODE_39 | BF_CODE_128, then the value will be set as 3 (= 1+2).
	 * 
	 * @sa BarcodeFormat
	 */


	/**@brief Number of maximum algorithm threads */	
    int mMaxAlgorithmThreadCount;
	/**< It stores how many image processing algorithm threads will be used to decode barcodes. By default, the library concurrently runs four different threads for decoding barcodes in order to keep a balance between speed and quality. For some devices (e.g. Raspberry Pi) that is only using one core, you can set it to 1 for best speed.
	 * 
	 * @par Value range:
	 * 		[1,4]
	 * @par Default value:
	 * 		4
	 * 		
	 */

	/**@brief The texture detection sensitivity */	
    int mTextureDetectionSensitivity;
	/**< It stores the value of sensitivity for texture detection. The higher value you set, the more efforts it will take to detect texture. 
	 * 
	 * @par Value range:
	 * 		[0,9]
	 * @par Default value:
	 * 		5
	 * @par Notice:
	 *		If the value is set to 0, texture detection will be disabled compulsively; if the value is set to 9, texture detection will be activated compulsively otherwise. 
	 */

	/**@brief The deblur level */	
    int mDeblurLevel;
	/**< It stores the degree of blurriness of the barcode. The higher value you set, the much more effort the library will take to decode images, but it may also slow down the recognition process.
     * @par Value range:
     * 		[0,9]
     * @par Default value:
     * 		9
	 */

	/**@brief The anti damage level */	
    int mAntiDamageLevel;
	/**< It stores the degree of anti-damage of the barcode, which decides how many localization algorithms will be used for locating barcode area. 
     * @par Value range:
     * 		[0,9]
     * @par Default Value:
     * 		9
	 * @par Remarks:
	 * 		- 0 = N = 3: one localization algorithm will be used.  
	 * 		
	 * 		- 4 = N = 5: two localization algorithm will be used.   
	 * 	
	 * 		- 6 = N = 7: three localization algorithm will be used.
	 * 	
	 * 		- 8 = N = 9: four(i.e. all) localization algorithm will be used. 
	 *
	 * @par Notice:
	 * 		To ensure the best decode efficiency, the value of AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	 *
	 * @sa mExpectedBarcodesCount
	 */

	/**@brief The maximum dimension of full image as barcode zone */	
    int mMaxDimOfFullImageAsBarcodeZone;
	/**< Sets the maximum image dimension (in pixels) to localize barcode on the full image. If the image dimension is smaller than the given value, 
	 * the library will localize barcode on the full image. Otherwise, “FullImageAsBarcodeZone?mode will not be enabled. 
	 * 
	 * @par Value range:
	 * 		[261244,0x7fffffff]
	 * @par Default value:
	 * 		261244
	 * @sa mLocalizationAlgorithmPriority
	 */

	/**@brief Number of maximum barcodes */	
    int mMaxBarcodesCount;
	/**< It stores the maximum number of barcodes to read, which limits the number of barcodes returned by library.
	 * @par Value range:
	 * 		[1,0x7fffffff]
	 * @par Default value:
	 * 		0x7fffffff
	 */

	 
	/**@brief The barcode invert mode */	
    BarcodeInvertMode mBarcodeInvertMode;
	/**< It stores the barcode invert mode which decides whether to invert colour before binarization. This mode is designed to fit the scenarios which light barcode located at dark background, for example, a white QR in a black paper.
     * @par Value range:
     * 		BIM_DarkOnLight, BIM_LightOnDark
     * @par Default value:
     * 		BIM_DarkOnLight
     * @sa BarcodeInvertMode
	 */

	/**@brief The scale down threshold */	
    int mScaleDownThreshold;
	/**< It stores the threshold value of the image shrinking. If the shorter edge size is larger than the given value, 
	 * the library will calculate the required height and width of the barcode image and shrink the image to that size 
	 * before localization. Otherwise, it will perform barcode localization on the original image.
	 * @par Value range:
	 * 		[512,0x7fffffff]
	 * @par Default value:
	 * 		2300
	 */

	/**@brief The gray equalization sensitivity */
    int mGrayEqualizationSensitivity;
	/**< It stores the sensitivity used for gray equalization. The higher the value, the more likely gray equalization will be 
	 * activated. Effective for images with low comparison between black and white colour. May cause adverse effect on images 
	 * with high level of black and white colour comparison.
	 * @par Value range:
	 * 		[0,9]
	 * @par Default value:
	 * 		0
	 * @par Notice:
	 *		If the value is set to 0, gray equalization will be disabled compulsively; if the value is set to 9, gray equalization will be activated compulsively otherwise. 
     */

	/**@brief The enable fill binary vacancy */	
    int mEnableFillBinaryVacancy;
	/**< For barcodes with a large module size there might be a vacant area in the position detection pattern after binarization 
	 * which may result in a decoding failure. Setting this to true will fill in the vacant area with black and may help to decode 
	 * it successfully. 
	 * @par Value range:
	 * 		0,1 (0 - disable, 1 - enable)
	 * @par Default value:
	 * 		1
	 */

	/**@brief The colour image convert mode */	
    ColourImageConvertMode mColourImageConvertMode;
	/**< It stores the information whether to convert colour images to grayscale before processing.
	 * @par Value range:
	 * 		CICM_Auto, CICM_Grayscale
	 * @par Default value:
	 * 		CICM_Auto
	 * @sa ColourImageConvertMode 
	 */

	/**@brief Reserved memory for struct. */	
	char mReserved[248];
	/**< The length of this array indicates the size of the memory reserved for this struct.*/

	/**@brief Number of expected barcodes */	
	int mExpectedBarcodesCount;
	/**< It stores the expected number of barcodes to read for each image (or each region of the image if you 
	 * specified barcode regions). 
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
	 * @par Notice:
	 * 		The value of ExpectedBarcodesCount must be less than or equal to the value of MaxBarcodesCount. Also, to ensure the best decode efficiency, the value of 
	 * 		AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	 * @sa mMaxBarcodesCount mAntiDamageLevel
     */

	/**@brief Size of the binarization block */	
	int mBinarizationBlockSize;
	/**< It stores the block size for the process of binarization. Block size means the size of a pixel neighborhood that is used to calculate a threshold value for the pixel.
	 * @par Value range:
	 * 		[0,1000]
	 * @par Default:
	 * 		0
	 * @par Remarks:
	 * 		- 0: the block size used for binarization will be set to a value which is calculated automatically.
	 * 		
	 * 		- N:    
	 * 		 - 1< N = 3: the block size used for binarization will be set to 3.  
	 * 		 - N > 3: the block size used for binarization will be set to N.

	 */	

}PublicRuntimeSettings;


/**
 * @brief This struct used for ensuring compatibility with earlier versions. It is functionally equivalent to PublicRuntimeSettings. 
 * 
 * @deprecated tagPublicParameterSettings PublicParameterSettings 
 * 
 * @sa tagPublicRuntimeSettings PublicRuntimeSettings
 *
 */
typedef struct tagPublicParameterSettings
{
	/**@brief The name used for identifying the struct. */
	char mName[32];
	/**< It stores the name of the struct, which is mainly help users to distinguish different version rather than practical use in the library.
	* @deprecated mName
	*
	*/

	/**@brief The timeout threshold. */
	int mTimeout;
	/**< It stores the maximum amount of time (in milliseconds) it should spend searching for a barcode per page. It does not include the time taken to load/decode an image (Tiff, PNG, etc.) from disk into memory.
	*
	* @par Value range:
	* 	   [0,7ffffff]
	* @par Default value:
	* 	   10000
	*/

	/**@brief The PDF raster DPI */
	int mPDFRasterDPI;
	/**< It stores the output image resolution. When you are trying to decode a PDF file using DecodeFile
	*method, the library will convert the pdf file to image(s) first, then perform barcode recognition.
	*
	* @par Value range:
	* 		[100,600]
	* @par Default value:
	* 		300
	*/

	/**@brief The text filter mode */
	TextFilterMode mTextFilterMode;
	/**< It stores the text filter mode for barcodes search, which decides whether to filter text before barcode localization.
	*
	*  @par Value range:
	* 		TFM_Disable, TFM_Enable
	* 	@par Default value:
	*		TFM_Enable
	*	@sa TextFilterMode
	*
	*/

	/**@brief The region predetection mode */
	RegionPredetectionMode mRegionPredetectionMode;
	/**< It stores the region pre-detection mode for barcodes search, which decides whether to pre-detect barcode region before accurate localization.
	* If you want to pre-detect barcode regions, it is better to set the mColourImageConvertMode to "CICM_Auto" as the color features need to be used in region detection.
	*
	* @par Value range:
	* 		RPM_Disable, RPM_Enable
	* @par Default value:
	* 		RPM_Disable
	* @sa RegionPredetectionMode mColourImageConvertMode
	*/

	/**@brief The localization algorithm priority */
	char mLocalizationAlgorithmPriority[64];
	/**< It stores the priority of localization algorithms, which decides the order of using following four localization algorithms.
	*
	* @par Default values:
	* 		""
	* @par Optional localization algorithms:
	* 		"ConnetectedBlock", "Statistics", "Lines", "FullImageAsBarcodeZone"
	* @par Remarks:
	* 		- Default value: The library will automatically use optimized localization priority, i.e. ConnetectedBlock -> Statistics -> Lines -> FullImageAsBarcodeZone, which is also the recommended order.
	*
	* 		- ConnectedBlock: Localizes barcodes by searching connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlock to the highest priority.
	*
	* 		- Lines: Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes.
	*
	* 		- Statistics: Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix.
	*
	* 		- FullImageAsBarcodeZone: Disables localization. In this mode, it will directly localize barcodes on the full image without localization. If there is nothing other than the barcode in the image, it is recommended to use this mode.
	*
	*/

	/**@brief List of identifiers for the barcode formats */
	int mBarcodeFormatIds;
	/**< It stores the information of which types of barcode need to be read. Notice that one barcode reader can support more than one barcode format, i.e. the barcode format can be combined like BF_CODE_39 | BF_CODE_128, then the value will be set as 3 (= 1+2).
	*
	* @sa BarcodeFormat
	*/


	/**@brief Number of maximum algorithm threads */
	int mMaxAlgorithmThreadCount;
	/**< It stores how many image processing algorithm threads will be used to decode barcodes. By default, the library concurrently runs four different threads for decoding barcodes in order to keep a balance between speed and quality. For some devices (e.g. Raspberry Pi) that is only using one core, you can set it to 1 for best speed.
	*
	* @par Value range:
	* 		[1,4]
	* @par Default value:
	* 		4
	*
	*/

	/**@brief The texture detection sensitivity */
	int mTextureDetectionSensitivity;
	/**< It stores the value of sensitivity for texture detection. The higher value you set, the more efforts it will take to detect texture.
	*
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		5
	* @par Notice:
	*		If the value is set to 0, texture detection will be disabled compulsively; if the value is set to 9, texture detection will be activated compulsively otherwise.
	*/

	/**@brief The deblur level */
	int mDeblurLevel;
	/**< It stores the degree of blurriness of the barcode. The higher value you set, the much more effort the library will take to decode images, but it may also slow down the recognition process.
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		9
	*/

	/**@brief The anti damage level */
	int mAntiDamageLevel;
	/**< It stores the degree of anti-damage of the barcode, which decides how many localization algorithms will be used for locating barcode area.
	* @par Value range:
	* 		[0,9]
	* @par Default Value:
	* 		9
	* @par Remarks:
	* 		- 0 = N = 3: one localization algorithm will be used.
	*
	* 		- 4 = N = 5: two localization algorithm will be used.
	*
	* 		- 6 = N = 7: three localization algorithm will be used.
	*
	* 		- 8 = N = 9: four(i.e. all) localization algorithm will be used.
	*
	* @par Notice:
	* 		To ensure the best decode efficiency, the value of AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	*
	* @sa mExpectedBarcodesCount
	*/

	/**@brief The maximum dimension of full image as barcode zone */
	int mMaxDimOfFullImageAsBarcodeZone;
	/**< Sets the maximum image dimension (in pixels) to localize barcode on the full image. If the image dimension is smaller than the given value,
	* the library will localize barcode on the full image. Otherwise, “FullImageAsBarcodeZone?mode will not be enabled.
	*
	* @par Value range:
	* 		[261244,0x7fffffff]
	* @par Default value:
	* 		261244
	* @sa mLocalizationAlgorithmPriority
	*/

	/**@brief Number of maximum barcodes */
	int mMaxBarcodesCount;
	/**< It stores the maximum number of barcodes to read, which limits the number of barcodes returned by library.
	* @par Value range:
	* 		[1,0x7fffffff]
	* @par Default value:
	* 		0x7fffffff
	*/


	/**@brief The barcode invert mode */
	BarcodeInvertMode mBarcodeInvertMode;
	/**< It stores the barcode invert mode which decides whether to invert colour before binarization. This mode is designed to fit the scenarios which light barcode located at dark background, for example, a white QR in a black paper.
	* @par Value range:
	* 		BIM_DarkOnLight, BIM_LightOnDark
	* @par Default value:
	* 		BIM_DarkOnLight
	* @sa BarcodeInvertMode
	*/

	/**@brief The scale down threshold */
	int mScaleDownThreshold;
	/**< It stores the threshold value of the image shrinking. If the shorter edge size is larger than the given value,
	* the library will calculate the required height and width of the barcode image and shrink the image to that size
	* before localization. Otherwise, it will perform barcode localization on the original image.
	* @par Value range:
	* 		[512,0x7fffffff]
	* @par Default value:
	* 		2300
	*/

	/**@brief The gray equalization sensitivity */
	int mGrayEqualizationSensitivity;
	/**< It stores the sensitivity used for gray equalization. The higher the value, the more likely gray equalization will be
	* activated. Effective for images with low comparison between black and white colour. May cause adverse effect on images
	* with high level of black and white colour comparison.
	* @par Value range:
	* 		[0,9]
	* @par Default value:
	* 		0
	* @par Notice:
	*		If the value is set to 0, gray equalization will be disabled compulsively; if the value is set to 9, gray equalization will be activated compulsively otherwise.
	*/

	/**@brief The enable fill binary vacancy */
	int mEnableFillBinaryVacancy;
	/**< For barcodes with a large module size there might be a vacant area in the position detection pattern after binarization
	* which may result in a decoding failure. Setting this to true will fill in the vacant area with black and may help to decode
	* it successfully.
	* @par Value range:
	* 		0,1 (0 - disable, 1 - enable)
	* @par Default value:
	* 		1
	*/

	/**@brief The colour image convert mode */
	ColourImageConvertMode mColourImageConvertMode;
	/**< It stores the information whether to convert colour images to grayscale before processing.
	* @par Value range:
	* 		CICM_Auto, CICM_Grayscale
	* @par Default value:
	* 		CICM_Auto
	* @sa ColourImageConvertMode
	*/

	/**@brief Reserved memory for struct. */
	char mReserved[248];
	/**< The length of this array indicates the size of the memory reserved for this struct.*/

	/**@brief Number of expected barcodes */
	int mExpectedBarcodesCount;
	/**< It stores the expected number of barcodes to read for each image (or each region of the image if you
	* specified barcode regions).
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
	* @par Notice:
	* 		The value of ExpectedBarcodesCount must be less than or equal to the value of MaxBarcodesCount. Also, to ensure the best decode efficiency, the value of
	* 		AntiDamageLevel is suggested to be set to 9 if the ExpectedBarcodesCount is set to 0 or 1; otherwise, the value of AntiDamageLevel is suggested to be set to 7.
	* @sa mMaxBarcodesCount mAntiDamageLevel
	*/

	/**@brief Size of the binarization block */
	int mBinarizationBlockSize;
	/**< It stores the block size for the process of binarization. Block size means the size of a pixel neighborhood that is used to calculate a threshold value for the pixel.
	* @par Value range:
	* 		[0,1000]
	* @par Default:
	* 		0
	* @par Remarks:
	* 		- 0: the block size used for binarization will be set to a value which is calculated automatically.
	*
	* 		- N:
	* 		 - 1< N = 3: the block size used for binarization will be set to 3.
	* 		 - N > 3: the block size used for binarization will be set to N.

	*/

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
#endif
	/**
	* @defgroup CFunctions C Functions
	* @{
	*   
	* Four methods are now supported for editing runtime settings ¨C reset, initialize, append, update. 
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
	 */
	DBR_API void*  DBR_CreateInstance();

	/**
	 * Destroys an instance of Dynamsoft Barcode Reader.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 */
	DBR_API void DBR_DestroyInstance(void*  hBarcode);

	/**
	 * Reads license key and activate the SDK.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pszLicense The license keys.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int  DBR_InitLicense(void*  hBarcode, const char* pszLicense);


	/**
	 * Decodes barcodes in the specified image file.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pszFileName A string defining the file name.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int  DBR_DecodeFile(void*  hBarcode, const char* pszFileName, const char* pszTemplateName);

	/**
	 * Decodes barcode from an image file in memory.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pFileBytes The image file bytes in memory.
	 * @param [in] nFileSize The length of the file bytes in memory.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int  DBR_DecodeFileInMemory(void*  hBarcode, unsigned char* pFileBytes, int nFileSize, const char* pszTemplateName);

	/**
	 * Decodes barcodes from the memory buffer containing image pixels in defined format.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
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
	 */
	DBR_API int  DBR_DecodeBuffer(void*  hBarcode, unsigned char* pBufferBytes, int iWidth, int iHeight, int iStride, ImagePixelFormat format, const char* pszTemplateName);

	/**
	 * Decodes barcode from an image file encoded as a base64 string.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pszBase64String A base64 encoded string that represents an image.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int  DBR_DecodeBase64String(void*  hBarcode, const char* pszBase64String, const char* pszTemplateName);

	/**
	 * Decodes barcode from a handle of device-independent bitmap (DIB).
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] hDIB Handle of the device-independent bitmap.
	 * @param [in] pszTemplateName The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int  DBR_DecodeDIB(void*  hBarcode, HANDLE  hDIB, const char* pszTemplateName);

	/**
	 * Gets all recognized barcode results.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [out] ppResults Barcode text results returned by last calling function 
	 * 				DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB.
	 * 				The ppResults is allocated by SDK and should be freed by calling function DBR_FreeTextResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int DBR_GetAllTextResults(void* hBarcode, STextResultArray **ppResults);

	/**
	 * Gets all localization barcode results. It contains all recognized barcodes and unrecognized
	 * barcodes.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [out] ppResults Barcode localization results returned by last calling function 
	 * 				DBR_DecodeFile/DBR_DecodeFileInMemory/DBR_DecodeBuffer/DBR_DecodeBase64String/DBR_DecodeDIB. 
	 * 				The ppResults is allocated by SDK and should be freed by calling function DBR_FreeLocalizationResults.
	 * 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int DBR_GetAllLocalizationResults(void* hBarcode, SLocalizationResultArray **ppResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] ppResults Text results.
	 *
	 */
	DBR_API void  DBR_FreeTextResults(STextResultArray **ppResults);

	/**
	 * Frees memory allocated for localization results.
	 * 
	 * @param [in] ppResults Localization results.
	 *
	 */
	DBR_API void  DBR_FreeLocalizationResults(SLocalizationResultArray **ppResults);

	/**
	 * Returns the error info string.
	 * 
	 * @param [in] iErrorCode The error code.
	 * 			   
	 * @return The error message.
	 *
	 */
	DBR_API const char* DBR_GetErrorString(int iErrorCode);

	/**
	 * Returns the version info string for the SDK.
	 * 
	 * @return The version info string.
	 */
	DBR_API const char* DBR_GetVersion();

	/**
	 * Gets current settings and save it into a struct.
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in,out] pSettings The struct of template settings.
	 *
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message.
	 * 
	 */
	DBR_API int DBR_GetRuntimeSettings(void* hBarcode, PublicRuntimeSettings *pSettings);

	/**
	 * Update runtime settings with a given struct.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pSettings The struct of template settings.
	 * @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length 
	 * 				   is 256.The error message will be copied to the buffer.
	 * @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	 * 			   
	 *@return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 *		  DBR_GetErrorString to get detail message.
	 * 
	 */
	DBR_API int DBR_UpdateRuntimeSettings(void* hBarcode,PublicRuntimeSettings *pSettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);

	/**
	 * Resets all parameters to default values.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call 
	 * 		   DBR_GetErrorString to get detail message
	 *
	 */
	DBR_API int DBR_ResetRuntimeSettings(void* hBarcode);

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
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithFile(void* hBarcode, const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Initialize runtime settings with the parameters obtained from JSON string.
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_InitRuntimeSettingsWithString(void* hBarcode, const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Append a new template file to current runtime settings.
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_AppendTplFileToRuntimeSettings(void* hBarcode, const char* pszFilePath, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Append a new template string to current runtime settings.
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	* @sa CFunctions PublicRuntimeSettings 
	*/
	DBR_API int  DBR_AppendTplStringToRuntimeSettings(void* hBarcode, const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Get count of parameter template.
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
	*
	* @return Returns the count of parameter template.
	*
	*/
	DBR_API int  DBR_GetParameterTemplateCount(void* hBarcode);

	/**
	* Get paramter template name by index.
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
	* @param [in] iIndex The index of parameter template array.
	* @param [in,out] szNameBuffer The buffer is allocated by caller and the recommended
	* 				  length is 256. The template name would be copy to the buffer.
	* @param [in] nNameBufferLen The length of allocated buffer
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	*
	*/
	DBR_API int  DBR_GetParameterTemplateName(void* hBarcode, int iIndex, char szNameBuffer[], int nNameBufferLen);

	/**
	 * Outputs runtime settings to a string.
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in,out] pszContent The output string which stores the contents of current settings.	   
	 * @param [in] nContentLen The length of output string.
	 * @param [in] pszSettingsName A unique name for declaring current runtime settings.	
     *	 
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int DBR_OutputSettingsToString(void* hBarcode, char pszContent[], int nContentLen, const char* pszSettingsName);

	/**
	 * Outputs runtime settings and save it into a settings file (JSON file).
	 * 
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pszFilePath The output file path which stores current settings.
	 * @param [in] pszSettingsName A unique name for declaring current runtime settings.
     *				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 */
	DBR_API int DBR_OutputSettingsToFile(void* hBarcode, const char* pszFilePath, const char* pszSettingsName);

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
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	DBR_API int  DBR_LoadSettingsFromFile(void* hBarcode, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_InitRuntimeSettingstWithString with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_LoadSettings
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
	* @param [in] pszContent A JSON string that represents the content of the settings.
	* @param [in,out] szErrorMsgBuffer The buffer is allocated by caller and the recommended length
	* 				  is 256. The error message will be copied to the buffer.
	* @param [in] nErrorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  DBR_GetErrorString to get detail message.
	* 		  
	* @sa DBR_InitRuntimeSettingstWithString
	*/	
	DBR_API int  DBR_LoadSettings(void* hBarcode, const char* pszContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_AppendTplFileToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_AppendParameterTemplateFromFile
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	DBR_API int  DBR_AppendParameterTemplateFromFile(void* hBarcode, const char* pszFilePath, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	* Ensure compatibility with earlier versions. It is functionally equivalent to DBR_AppendTplStringToRuntimeSettings with conflict mode ECM_Overwrite as default.
	*
	* @deprecated DBR_AppendParameterTemplate
	*
	* @param [in] hBarcode Handle of the barcode reader instance.
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
	DBR_API int  DBR_AppendParameterTemplate(void* hBarcode, const char* pszContent, char szErrorMsgBuffer[], int nErrorMsgBufferLen);

	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to DBR_GetRuntimeSettings.
	 *
	 * @deprecated DBR_GetTemplateSettings
	 *
	 * @param [in] hBarcode Handle of the barcode reader instance.
	 * @param [in] pszTemplateName The template name.
	 * @param [in,out] pSettings The struct of template settings.
	 * 				   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   DBR_GetErrorString to get detail message.
	 *
	 * @sa DBR_GetRuntimeSettings	 
	 */ 
	DBR_API int DBR_GetTemplateSettings(void* hBarcode,const char*pszTemplateName, PublicParameterSettings *pSettings);

	/**
	 * Ensure compatibility with earlier versions. It is functionally equivalent to DBR_UpdateRuntimeSettings.
	 *
	 * @deprecated DBR_SetTemplateSettings
	 *
	 * @param [in] hBarcode Handle of the barcode reader instance.
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
	DBR_API int DBR_SetTemplateSettings(void* hBarcode,const char*pszTemplateName,PublicParameterSettings *pSettings,char szErrorMsgBuffer[],int nErrorMsgBufferLen);


	/**
	 * @}
	 * @} 
	 */

#ifdef __cplusplus
}
#endif

//---------------------------------------------------------------------------
// Class
//---------------------------------------------------------------------------


#ifdef __cplusplus
class BarcodeReaderInner;


/**
*
* @defgroup CBarcodeReader CBarcodeReader Class
* @{
*
*/

/**
* Defines a class that provides functions for working with extracting barcode data.
* @class CBarcodeReader
*
*
* Four methods are now supported for editing runtime settings ¨C reset, initialize, append, update. 
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
	 */
	int InitLicense(const char* pLicense);


	/**
	 * Decodes barcodes in a specified image file.
	 * 
	 * @param [in] pszFileName A string defining the file name.
	 * @param [in] pszTemplateName (Optional) The template name.
	 * 			   
	 * @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	 * 		   GetErrorString to get detail message.
	 *
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
	 */
	int GetAllLocalizationResults(SLocalizationResultArray **ppResults);

	/**
	 * Frees memory allocated for text results.
	 * 
	 * @param [in] ppResults Text results.
	 * 			   
	 */
	static void FreeTextResults(STextResultArray **ppResults);

	/**
	 * Frees memory allocated for localization results.
	 * 
	 * @param [in] ppResults Localization results.
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
	 */
	static const char* GetErrorString(int iErrorCode);

	/**
	 * Returns the version info string for the SDK.
	 * 
	 * @return The version info string.
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
	 */
	int UpdateRuntimeSettings(PublicRuntimeSettings *psettings, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Resets all parameters to default values.
	*
	* @return Returns error code. Returns 0 if the function completed successfully, otherwise call
	* 		  GetErrorString to get detail message.
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
	* @sa CBarcodeReader PublicRuntimeSettings
	*/
	int  AppendTplStringToRuntimeSettings(const char* pszContent, ConflictMode emSettingPriority, char szErrorMsgBuffer[] = NULL, int nErrorMsgBufferLen = 0);

	/**
	* Gets the count of the parameter templates.
	*
	* @return Returns the count of parameter template.
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
 * @}
 */
#endif
#endif
