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


#pragma region ErrorCode

 /**Successful. */
#define DBR_OK								0 

 /**The file is not found. */
#define DBRERR_FILE_NOT_FOUND				-10005 

 /**The file type is not supported. */
#define DBRERR_FILETYPE_NOT_SUPPORTED		-10006 

 /**The DIB (Device-Independent Bitmaps) buffer is invalid. */
#define DBRERR_DIB_BUFFER_INVALID			-10018

 /**Recognition timeout. */
#define DBRERR_RECOGNITION_TIMEOUT			-10026


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
#define DBRERR_LICENSE_KEY_INVALID			-10053

/**The device number in the license key runs out. */
#define DBRERR_LICENSE_DEVICE_RUNS_OUT      -10054

/**Failed to get mode's argument. */
#define DBRERR_GET_MODE_ARGUMENT_ERROR		-10055

/**The Intermediate Result Types license is invalid. */
#define DBRERR_IRT_LICENSE_INVALID			-10056

/**The Maxicode license is invalid. */
#define DBRERR_MAXICODE_LICENSE_INVALID		-10057

/**The GS1 Databar license is invalid. */
#define DBRERR_GS1_DATABAR_LICENSE_INVALID		-10058

/**The GS1 Composite code license is invalid. */
#define DBRERR_GS1_COMPOSITE_LICENSE_INVALID		-10059

/**The panorama license is invalid. */
#define DBRERR_PANORAMA_LICENSE_INVALID -10060

/**The DotCode license is invalid. */
#define DBRERR_DOTCODE_LICENSE_INVALID -10061

#define DBRERR_PHARMACODE_LICENSE_INVALID -10062

/**
 * @}defgroup ErrorCode
 */
#pragma endregion
#pragma pack(push)
#pragma pack(1)
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
}DBRPoint, *PDBRPoint;
/**
* @} defgroup DBRPoint
*/

#pragma pack(pop)

#pragma region Enum

#ifndef _COMMON_PART2_
#define _COMMON_PART2_
/**
* @enum ImagePixelFormat
*
* Describes the image pixel format.
*/
typedef enum ImagePixelFormat
{
	/**0:Black, 1:White */
	IPF_BINARY,

	/**0:White, 1:Black */
	IPF_BINARYINVERTED,

	/**8bit gray */
	IPF_GRAYSCALED,

	/**NV21 */
	IPF_NV21,

	/**16bit with RGB channel order stored in memory from high to low address*/
	IPF_RGB_565,

	/**16bit with RGB channel order stored in memory from high to low address*/
	IPF_RGB_555,

	/**24bit with RGB channel order stored in memory from high to low address*/
	IPF_RGB_888,

	/**32bit with ARGB channel order stored in memory from high to low address*/
	IPF_ARGB_8888,

	/**48bit with RGB channel order stored in memory from high to low address*/
	IPF_RGB_161616,

	/**64bit with ARGB channel order stored in memory from high to low address*/
	IPF_ARGB_16161616,

	/**32bit with ABGR channel order stored in memory from high to low address*/
	IPF_ABGR_8888,

	/**64bit with ABGR channel order stored in memory from high to low address*/
	IPF_ABGR_16161616,

	/**24bit with BGR channel order stored in memory from high to low address*/
	IPF_BGR_888

}ImagePixelFormat;

/**
* @enum BinarizationMode
*
* Describes the binarization mode.
*/
typedef enum BinarizationMode
{
	/**Not supported yet. */
	BM_AUTO = 0x01,

	/**Binarizes the image based on the local block. Check @ref BM for available argument settings.*/
	BM_LOCAL_BLOCK = 0x02,

	/**Performs image binarization based on the given threshold. Check @ref BM for available argument settings.*/
	BM_THRESHOLD = 0x04,

	/**Reserved setting for binarization mode.*/
#if defined(_WIN32) || defined(_WIN64)
	BM_REV = 0x80000000,
#else
	BM_REV = -2147483648,
#endif

	/**Skips the binarization. */
	BM_SKIP = 0x00

}BinarizationMode;

/**
* @enum ScaleUpMode
*
* Describes the scale up mode .
*/
typedef enum ScaleUpMode
{
	/**The library chooses an interpolation method automatically to scale up.*/
	SUM_AUTO = 0x01,

	/**Scales up using the linear interpolation method. Check @ref SUM for available argument settings.*/
	SUM_LINEAR_INTERPOLATION = 0x02,

	/**Scales up using the nearest-neighbour interpolation method. Check @ref SUM for available argument settings.*/
	SUM_NEAREST_NEIGHBOUR_INTERPOLATION = 0x04,

	/**Reserved setting for scale up mode.*/
#if defined(_WIN32) || defined(_WIN64)
	SUM_REV = 0x80000000,
#else
	SUM_REV = -2147483648,
#endif

	/**Skip the scale-up process.*/
	SUM_SKIP = 0x00

}ScaleUpMode;

typedef enum RegionPredetectionMode
{
	/**Lets the library choose an algorithm automatically to detect region. */
	RPM_AUTO = 0x01,

	/**Takes the whole image as a region. */
	RPM_GENERAL = 0x02,

	/**Detects region using the general algorithm based on RGB colour contrast. Check @ref RPM for available argument settings.*/
	RPM_GENERAL_RGB_CONTRAST = 0x04,

	/**Detects region using the general algorithm based on gray contrast. Check @ref RPM for available argument settings.*/
	RPM_GENERAL_GRAY_CONTRAST = 0x08,

	/**Detects region using the general algorithm based on HSV colour contrast. Check @ref RPM for available argument settings.*/
	RPM_GENERAL_HSV_CONTRAST = 0x10,

	/**Reserved setting for region predection mode.*/
#if defined(_WIN32) || defined(_WIN64)
	RPM_REV = 0x80000000,
#else
	RPM_REV = -2147483648,
#endif

	/**Skips region detection. */
	RPM_SKIP = 0x00

}RegionPredetectionMode;

 /**
 * @defgroup Enum Enumerations
 * @{
 */

 /**
 * @enum BarcodeFormat
 *
 * Describes the barcode types in BarcodeFormat group 1. All the formats can be combined, such as BF_CODE_39 | BF_CODE_128.
 * Note: The barcode format our library will search for is composed of [BarcodeFormat group 1](@ref BarcodeFormat) and [BarcodeFormat group 2](@ref BarcodeFormat_2), so you need to specify the barcode format in group 1 and group 2 individually.
 */
typedef enum BarcodeFormat
{
	/**All supported formats in BarcodeFormat group 1*/
#if defined(_WIN32) || defined(_WIN64)
	BF_ALL = 0xFE3FFFFF,
#else
	BF_ALL = -29360129,
#endif

	/**Combined value of BF_CODABAR, BF_CODE_128, BF_CODE_39, BF_CODE_39_Extended, BF_CODE_93, BF_EAN_13, BF_EAN_8, INDUSTRIAL_25, BF_ITF, BF_UPC_A, BF_UPC_E, BF_MSI_CODE;  */
	BF_ONED = 0x003007FF,

	/**Combined value of BF_GS1_DATABAR_OMNIDIRECTIONAL, BF_GS1_DATABAR_TRUNCATED, BF_GS1_DATABAR_STACKED, BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL, BF_GS1_DATABAR_EXPANDED, BF_GS1_DATABAR_EXPANDED_STACKED, BF_GS1_DATABAR_LIMITED*/
	BF_GS1_DATABAR = 0x0003F800,

	/**Code 39 */
	BF_CODE_39 = 0x1,

	/**Code 128 */
	BF_CODE_128 = 0x2,

	/**Code 93 */
	BF_CODE_93 = 0x4,

	/**Codabar */
	BF_CODABAR = 0x8,

	/**Interleaved 2 of 5 */
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

	/**GS1 Databar Omnidirectional*/
	BF_GS1_DATABAR_OMNIDIRECTIONAL = 0x800,

	/**GS1 Databar Truncated*/
	BF_GS1_DATABAR_TRUNCATED = 0x1000,

	/**GS1 Databar Stacked*/
	BF_GS1_DATABAR_STACKED = 0x2000,

	/**GS1 Databar Stacked Omnidirectional*/
	BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL = 0x4000,

	/**GS1 Databar Expanded*/
	BF_GS1_DATABAR_EXPANDED = 0x8000,

	/**GS1 Databar Expaned Stacked*/
	BF_GS1_DATABAR_EXPANDED_STACKED = 0x10000,

	/**GS1 Databar Limited*/
	BF_GS1_DATABAR_LIMITED = 0x20000,

	/**Patch code. */
	BF_PATCHCODE = 0x00040000,

	/**PDF417 */
	BF_PDF417 = 0x02000000,

	/**QRCode */
	BF_QR_CODE = 0x04000000,

	/**DataMatrix */
	BF_DATAMATRIX = 0x08000000,

	/**AZTEC */
	BF_AZTEC = 0x10000000,

	/**MAXICODE */
	BF_MAXICODE = 0x20000000,

	/**Micro QR Code*/
	BF_MICRO_QR = 0x40000000,

	/**Micro PDF417*/
	BF_MICRO_PDF417 = 0x00080000,

	/**GS1 Composite Code*/
#if defined(_WIN32) || defined(_WIN64)
	BF_GS1_COMPOSITE = 0x80000000,
#else
	BF_GS1_COMPOSITE = -2147483648,
#endif

	/**MSI Code*/
	BF_MSI_CODE = 0x100000,

	/*Code 11*/
	BF_CODE_11 = 0x200000,

	/**No barcode format in BarcodeFormat group 1*/
	BF_NULL = 0x00

}BarcodeFormat;

/**
* @enum BarcodeFormat_2
*
* Describes the barcode types in BarcodeFormat group 2.
* Note: The barcode format our library will search for is composed of [BarcodeFormat group 1](@ref BarcodeFormat) and [BarcodeFormat group 2](@ref BarcodeFormat_2), so you need to specify the barcode format in group 1 and group 2 individually.
*/
typedef enum BarcodeFormat_2
{
	/**No barcode format in BarcodeFormat group 2*/
	BF2_NULL = 0x00,

	/**Combined value of BF2_USPSINTELLIGENTMAIL, BF2_POSTNET, BF2_PLANET, BF2_AUSTRALIANPOST, BF2_RM4SCC.*/
	BF2_POSTALCODE = 0x01F00000,

	/**Nonstandard barcode */
	BF2_NONSTANDARD_BARCODE = 0x01,

	/**USPS Intelligent Mail.*/
	BF2_USPSINTELLIGENTMAIL = 0x00100000,

	/**Postnet.*/
	BF2_POSTNET = 0x00200000,

	/**Planet.*/
	BF2_PLANET = 0x00400000,

	/**Australian Post.*/
	BF2_AUSTRALIANPOST = 0x00800000,

	/**Royal Mail 4-State Customer Barcode.*/
	BF2_RM4SCC = 0x01000000,

	/**DotCode.*/
	BF2_DOTCODE = 0x02,

	/**_PHARMACODE_ONE_TRACK.*/
	BF2_PHARMACODE_ONE_TRACK = 0x04,

	/**PHARMACODE_TWO_TRACK.*/
	BF2_PHARMACODE_TWO_TRACK = 0x08,

	/**PHARMACODE.*/
	BF2_PHARMACODE = 0x0C
}BarcodeFormat_2;


/**
* @enum ColourConversionMode
*
* Describes the colour conversion mode.
*/
typedef enum ColourConversionMode
{
	/**Converts a colour image to a grayscale image using the general algorithm. Check @ref CICM for available argument settings. */
	CICM_GENERAL = 0x01,

	/**Reserved setting for colour conversion mode.*/
#if defined(_WIN32) || defined(_WIN64)
	CICM_REV = 0x80000000,
#else
	CICM_REV = -2147483648,
#endif

	/**Skips the colour conversion. */
	CICM_SKIP = 0x00

}ColourConversionMode;

/**
* @enum TextureDetectionMode
*
* Describes the texture detection mode.
*/
typedef enum TextureDetectionMode
{
	/**Not supported yet. */
	TDM_AUTO = 0X01,

	/**Detects texture using the general algorithm. Check @ref TDM for available argument settings.*/
	TDM_GENERAL_WIDTH_CONCENTRATION = 0X02,

	/**Reserved setting for texture detection mode.*/
#if defined(_WIN32) || defined(_WIN64)
	TDM_REV = 0x80000000,
#else
	TDM_REV = -2147483648,
#endif

	/**Skips texture detection. */
	TDM_SKIP = 0x00

}TextureDetectionMode;

/**
* @enum GrayscaleTransformationMode
*
* Describes the grayscale transformation mode.
*/
typedef enum GrayscaleTransformationMode
{
	/**Transforms to inverted grayscale. Recommended for light on dark images. */
	GTM_INVERTED = 0x01,

	/**Keeps the original grayscale. Recommended for dark on light images. */
	GTM_ORIGINAL = 0x02,

	/**Reserved setting for grayscale transformation mode.*/
#if defined(_WIN32) || defined(_WIN64)
	GTM_REV = 0x80000000,
#else
	GTM_REV = -2147483648,
#endif

	/**Skips grayscale transformation. */
	GTM_SKIP = 0x00

}GrayscaleTransformationMode;

/**
* @enum PDFReadingMode
*
* Describes the PDF reading mode.
*/
typedef enum PDFReadingMode
{
	/** Lets the library choose the reading mode automatically. */
	PDFRM_AUTO = 0x01,

	/** Detects barcode from vector data in PDF file.*/
	PDFRM_VECTOR = 0x02,

	/** Converts the PDF file to image(s) first, then perform barcode recognition.*/
	PDFRM_RASTER = 0x04,

	/**Reserved setting for PDF reading mode.*/
#if defined(_WIN32) || defined(_WIN64)
	PDFRM_REV = 0x80000000,
#else
	PDFRM_REV = -2147483648,
#endif
}PDFReadingMode;

#pragma pack(push)
#pragma pack(1)

typedef DBRPoint DM_Point;

/**
* @defgroup Quadrilateral Quadrilateral
* @{
*/
/**
* Stores the quadrilateral.
*
*/
typedef struct tagQuadrilateral
{

	/**Four vertexes in a clockwise direction of a quadrilateral. Index 0 represents the left-most vertex. */
	DBRPoint points[4];

}Quadrilateral;

/**
* @} defgroup Quadrilateral
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

#pragma pack(pop)
#endif

/**
* @enum ImagePreprocessingMode
*
* Describes the image preprocessing mode.
*/
typedef enum ImagePreprocessingMode
{
	/**Not supported yet. */
	IPM_AUTO = 0x01,

	/**Takes the unpreprocessed image for following operations. */
	IPM_GENERAL = 0x02,

	/**Preprocesses the image using the gray equalization algorithm. Check @ref IPM for available argument settings.*/
	IPM_GRAY_EQUALIZE = 0x04,

	/**Preprocesses the image using the gray smoothing algorithm. Check @ref IPM for available argument settings.*/
	IPM_GRAY_SMOOTH = 0x08,

	/**Preprocesses the image using the sharpening and smoothing algorithm. Check @ref IPM for available argument settings.*/
	IPM_SHARPEN_SMOOTH = 0x10,

	/**Preprocesses the image using the morphology algorithm. Check @ref IPM for available argument settings.*/
	IPM_MORPHOLOGY = 0x20,

	/**Reserved setting for image preprocessing mode.*/
#if defined(_WIN32) || defined(_WIN64)
	IPM_REV = 0x80000000,
#else
	IPM_REV = -2147483648,
#endif

	/**Skips image preprocessing. */
	IPM_SKIP = 0x00

}ImagePreprocessingMode;

/**
* @enum BarcodeComplementMode
*
* Describes the barcode complement mode.
*/
typedef enum BarcodeComplementMode
{
	/**Not supported yet. */
	BCM_AUTO = 0x01,

	/**Complements the barcode using the general algorithm.*/
	BCM_GENERAL = 0x02,

	/**Reserved setting for barcode complement mode.*/
#if defined(_WIN32) || defined(_WIN64)
	BCM_REV = 0x80000000,
#else
	BCM_REV = -2147483648,
#endif

	/**Skips the barcode complement. */
	BCM_SKIP = 0x00

}BarcodeComplementMode;


/**
* @enum BarcodeColourMode
*
* Describes the barcode colour mode.
*/
typedef enum BarcodeColourMode
{
	/**Dark items on a light background. Check @ref BICM for available argument settings.*/
	BICM_DARK_ON_LIGHT = 0x01,

	/**Light items on a dark background. Not supported yet. Check @ref BICM for available argument settings.*/
	BICM_LIGHT_ON_DARK = 0x02,

	/**Dark items on a dark background. Not supported yet. Check @ref BICM for available argument settings.*/
	BICM_DARK_ON_DARK = 0x04,

	/**Light items on a light background. Not supported yet. Check @ref BICM for available argument settings.*/
	BICM_LIGHT_ON_LIGHT = 0x08,

	/**The background is mixed by dark and light. Not supported yet. Check @ref BICM for available argument settings.*/
	BICM_DARK_LIGHT_MIXED = 0x10,

	/**Dark item on a light background surrounded by dark. Check @ref BICM for available argument settings.*/
	BICM_DARK_ON_LIGHT_DARK_SURROUNDING = 0x20,

	/**Reserved setting for barcode colour mode.*/
#if defined(_WIN32) || defined(_WIN64)
	BICM_REV = 0x80000000,
#else
	BICM_REV = -2147483648,
#endif

	/**Skips the barcode colour operation.  */
	BICM_SKIP = 0x00

}BarcodeColourMode;

/**
* @enum ColourClusteringMode
*
* Describes the colour clustering mode. Not supported yet.
*/
typedef enum ColourClusteringMode
{
	/**Not supported yet. */
	CCM_AUTO = 0x00000001,

	/**Clusters colours using the general algorithm based on HSV. Check @ref CCM for available argument settings. */
	CCM_GENERAL_HSV = 0x00000002,

	/**Reserved setting for colour clustering mode.*/
#if defined(_WIN32) || defined(_WIN64)
	CCM_REV = 0x80000000,
#else
	CCM_REV = -2147483648,
#endif

	/**Skips the colour clustering. */
	CCM_SKIP = 0x00

}ColourClusteringMode;

/**
* @enum DPMCodeReadingMode
*
* Describes the DPM code reading mode.
*/
typedef enum DPMCodeReadingMode
{
	/**Not supported yet. */
	DPMCRM_AUTO = 0x01,

	/**Reads DPM code using the general algorithm.
	When this mode is set, the library will automatically add LM_STATISTICS_MARKS to LocalizationModes and add a BM_LOCAL_BLOCK to BinarizationModes which is with arguments:
	BlockSizeX=0, BlockSizeY=0, EnableFillBinaryVacancy=0, ImagePreprocessingModesIndex=1, ThreshValueCoefficient=15 if you doesn't set them.*/
	DPMCRM_GENERAL = 0x02,

	/**Reserved setting for DPM code reading mode.*/
#if defined(_WIN32) || defined(_WIN64)
	DPMCRM_REV = 0x80000000,
#else
	DPMCRM_REV = -2147483648,
#endif

	/**Skips DPM code reading. */
	DPMCRM_SKIP = 0x00

}DPMCodeReadingMode;

/**
* @enum ConflictMode
*
* Describes the conflict mode.
*/
typedef enum ConflictMode
{
	/**Ignores new settings and inherits the previous settings. */
	CM_IGNORE = 1,

	/**Overwrites the old settings with new settings. */
	CM_OVERWRITE = 2

}ConflictMode;

/**
* @enum IntermediateResultType
*
* Describes the intermediate result type.
*/
typedef enum IntermediateResultType
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
	IRT_TYPED_BARCODE_ZONE = 0x00001000,

	/**Predetected quadrilateral*/
	IRT_PREDETECTED_QUADRILATERAL = 0x00002000

}IntermediateResultType;

/**
* @enum LocalizationMode
*
* Describes the localization mode.
*/
typedef enum LocalizationMode
{
	/**Not supported yet. */
	LM_AUTO = 0x01,

	/**Localizes barcodes by searching for connected blocks. This algorithm usually gives best result and it is recommended to set ConnectedBlocks to the highest priority. */
	LM_CONNECTED_BLOCKS = 0x02,

	/**Localizes barcodes by groups of contiguous black-white regions. This is optimized for QRCode and DataMatrix. */
	LM_STATISTICS = 0x04,

	/**Localizes barcodes by searching for groups of lines. This is optimized for 1D and PDF417 barcodes. */
	LM_LINES = 0x08,

	/**Localizes barcodes quickly. This mode is recommended in interactive scenario. Check @ref LM for available argument settings.*/
	LM_SCAN_DIRECTLY = 0x10,

	/**Localizes barcodes by groups of marks.This is optimized for DPM codes. */
	LM_STATISTICS_MARKS = 0x20,

	/**Localizes barcodes by groups of connected blocks and lines.This is optimized for postal codes. */
	LM_STATISTICS_POSTAL_CODE = 0x40,

	/**Localizes barcodes from the centre of the image. Check @ref LM for available argument settings. */
	LM_CENTRE = 0x80,

	/**Localizes 1D barcodes fast. Check @ref LM for available argument settings. */
	LM_ONED_FAST_SCAN = 0x100,

	/**Reserved setting for localization mode.*/
#if defined(_WIN32) || defined(_WIN64)
	LM_REV = 0x80000000,
#else
	LM_REV = -2147483648,
#endif

	/**Skips localization. */
	LM_SKIP = 0x00

}LocalizationMode;

/**
* @enum MirrorMode
*
* Describes the mirror mode.
*/
typedef enum MirrorMode
{
	MM_NORMAL = 0x01,
	MM_MIRROR = 0x02,
	MM_BOTH = 0x04
}MirrorMode;

/**
* @enum QRCodeErrorCorrectionLevel
*
* Describes the QR Code error correction level.
*/
typedef enum QRCodeErrorCorrectionLevel
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
* @enum DeformationResistingMode
*
* Describes the deformation resisting mode.
*/
typedef enum DeformationResistingMode
{
	/**Not supported yet. */
	DRM_AUTO = 0x01,

	/**Resists deformation using the general algorithm. Check @ref DRM for available argument settings.*/
	DRM_GENERAL = 0x02,
	/**Resists deformation when the barcode is warped gently.*/
	DRM_BROAD_WARP = 0x04,
	/**Resists deformation for barcodes with minor deformation in local modules.*/
	DRM_LOCAL_REFERENCE = 0x08,
	/**Resists deformation for barcodes on a wrinkled surface.*/
	DRM_DEWRINKLE = 0x10,

	/**Reserved setting for deformation resisting mode.*/
#if defined(_WIN32) || defined(_WIN64)
	DRM_REV = 0x80000000,
#else
	DRM_REV = -2147483648,
#endif

	/**Skips deformation resisting. */
	DRM_SKIP = 0x00

}DeformationResistingMode;

/**
* @enum ResultType
*
* Describes the extended result type.
*/
typedef enum ResultType
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
typedef enum TerminatePhase
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
typedef enum TextAssistedCorrectionMode
{
	/**Not supported yet. */
	TACM_AUTO = 0x01,

	/**Uses the accompanying text to verify the decoded barcode result. Check @ref TACM for available argument settings.*/
	TACM_VERIFYING = 0x02,

	/**Uses the accompanying text to verify and patch the decoded barcode result. Check @ref TACM for available argument settings.*/
	TACM_VERIFYING_PATCHING = 0x04,

	/**Reserved setting for text assisted correction mode.*/
#if defined(_WIN32) || defined(_WIN64)
	TACM_REV = 0x80000000,
#else
	TACM_REV = -2147483648,
#endif

	/**Skips the text assisted correction. */
	TACM_SKIP = 0x00

}TextAssistedCorrectionMode;

/**
* @enum TextFilterMode
*
* Describes the text filter mode.
*/
typedef enum TextFilterMode
{
	/**Not supported yet. */
	TFM_AUTO = 0x01,

	/**Filters text using the general algorithm based on contour. Check @ref TFM for available argument settings.*/
	TFM_GENERAL_CONTOUR = 0x02,

	/**Reserved setting for text filter mode.*/
#if defined(_WIN32) || defined(_WIN64)
	TFM_REV = 0x80000000,
#else
	TFM_REV = -2147483648,
#endif

	/**Skips text filtering. */
	TFM_SKIP = 0x00

}TextFilterMode;

/**
* @enum IntermediateResultSavingMode
*
* Describes the intermediate result saving mode.
*/
typedef enum IntermediateResultSavingMode
{
	/**Saves intermediate results in memory.*/
	IRSM_MEMORY = 0x01,

	/**Saves intermediate results in file system. Check @ref IRSM for available argument settings.*/
	IRSM_FILESYSTEM = 0x02,

	/**Saves intermediate results in both memory and file system. Check @ref IRSM for available argument settings.*/
	IRSM_BOTH = 0x04,

	/**Saves intermediate results in memory with internal data format.*/
	IRSM_REFERENCE_MEMORY = 0x08

}IntermediateResultSavingMode;

/**
* @enum TextResultOrderMode
*
* Describes the text result order mode.
*/
typedef enum TextResultOrderMode
{
	/**Returns the text results in descending order by confidence. */
	TROM_CONFIDENCE = 0x01,

	/**Returns the text results in position order, from top to bottom, then left to right */
	TROM_POSITION = 0x02,

	/**Returns the text results in alphabetical and numerical order by barcode format string. */
	TROM_FORMAT = 0x04,

	/**Reserved setting for text result order mode.*/
#if defined(_WIN32) || defined(_WIN64)
	TROM_REV = 0x80000000,
#else
	TROM_REV = -2147483648,
#endif

	/**Skips the result ordering operation. */
	TROM_SKIP = 0x00

}TextResultOrderMode;


/**
* @enum ResultCoordinateType
*
* Describes the result coordinate type.
*/
typedef enum ResultCoordinateType
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
typedef enum IMResultDataType
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
	IMRDT_REGIONOFINTEREST = 0x10,

	/**Specifies the quadrilateral */
	IMRDT_QUADRILATERAL = 0x20,

	/**Specifies the internal data format for using other Dynamsoft products, such as Dynamic Web TWAIN.*/
	IMRDT_REFERENCE = 0x40

}IMResultDataType;

/**
* @enum AccompanyingTextRecognitionMode
*
* Describes the accompanying text recognition mode.
*/
typedef enum AccompanyingTextRecognitionMode
{
	/** Recognizes accompanying texts using the general algorithm. Check @ref ATRM for available argument settings.*/
	ATRM_GENERAL = 0x01,

	/**Reserved setting for accompanying text recognition mode.*/
#if defined(_WIN32) || defined(_WIN64)
	ATRM_REV = 0x80000000,
#else
	ATRM_REV = -2147483648,
#endif

	/** Skips the accompanying text recognition. */
	ATRM_SKIP = 0x00

}AccompanyingTextRecognitionMode;

/**
* @enum ClarityCalculationMethod
*
* Describes the clarity calculation method
*/
typedef enum ClarityCalculationMethod
{
	/** Calculates clarity using the contrast method */
	ECCM_CONTRAST = 0x01
}ClarityCalculationMethod;

/**
* @enum ClarityFilterMode
*
* Describes the clarity filter mode
*/
typedef enum ClarityFilterMode
{
	/** Filters the frames using the general algorithm based on calculated clarity */
	CFM_GENERAL = 0x01
}ClarityFilterMode;


/**
* @enum DeblurMode
*
* Describes the deblur mode.
*/
typedef enum DeblurMode
{
	/**Performs deblur process using the direct binarization algorithm.*/
	DM_DIRECT_BINARIZATION = 0x01,

	/**Performs deblur process using the threshold binarization algorithm.*/
	DM_THRESHOLD_BINARIZATION = 0x02,

	/**Performs deblur process using the gray equalization algorithm.*/
	DM_GRAY_EQUALIZATION = 0x04,

	/**Performs deblur process using the smoothing algorithm.*/
	DM_SMOOTHING = 0x08,

	/**Performs deblur process using the morphing algorithm.*/
	DM_MORPHING = 0x10,

	/**Performs deblur process using the deep analysis algorithm.*/
	DM_DEEP_ANALYSIS = 0x20,

	/**Performs deblur process using the sharpening algorithm.*/
	DM_SHARPENING = 0x40,

	/**Performs deblur process based on the binary image from the localization process.*/
	DM_BASED_ON_LOC_BIN = 0x80,

	/**Performs deblur process using the sharpening and smoothing algorithm.*/
	DM_SHARPENING_SMOOTHING = 0x100,

	/**Reserved setting for deblur mode.*/
#if defined(_WIN32) || defined(_WIN64)
	DM_REV = 0x80000000,
#else
	DM_REV = -2147483648,
#endif

	/**Skips the deblur process.*/
	DM_SKIP = 0x00
}DeblurMode;

typedef enum PartitionMode
{
	PM_WHOLE_BARCODE = 0x01,
	PM_ALIGNMENT_PARTITION = 0x02
}PartitionMode;

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
* @defgroup SamplingImageData SamplingImageData
* @{
*/

/**
* Stores the sampling image data.
*
*/
typedef struct tagSamplingImageData
{
	/**The sampling image data in a byte array.*/
	unsigned char* bytes;

	/**The width of the sampling image.*/
	int width;

	/**The height of the sampling image.*/
	int height;
}SamplingImageData;

/**
* @} defgroup SamplingImageData
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

	/**Sets the mode and priority for DPM code reading.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ColourConversionMode Enumeration items.
	* @par Default value:
	* 	    [DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP,DPMCRM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa DPMCodeReadingMode
	*/
	DPMCodeReadingMode dpmCodeReadingModes[8];

	/**Sets the mode and priority for deformation resisting.
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

	/**Sets the mode and priority to complement the missing parts in the barcode.
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

	/**Sets the mode and priority to recognize accompanying text. AccompanyingTextRecognitionModes has been deprecated.
	*
	* @par Value range:
	* 	    Each array item can be any one of the AccompanyingTextRecognitionMode Enumeration items
	* @par Default value:
	* 	    [ATRM_SKIP,ATRM_SKIP,ATRM_SKIP,ATRM_SKIP,ATRM_SKIP,ATRM_SKIP,ATRM_SKIP,ATRM_SKIP]
	* @par Remarks:
	*     The array index represents the priority of the item. The smaller index is, the higher priority is.
	* @sa AccompanyingTextRecognitionMode
	*/
	AccompanyingTextRecognitionMode accompanyingTextRecognitionModes[8];

	/**Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[32];
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

	/**Sets the formats of the barcode in BarcodeFormat group 1 to be read. Barcode formats in BarcodeFormat group 1 can be combined.
	*
	* @par Value range:
	* 	    A combined value of BarcodeFormat Enumeration items
	* @par Default value:
	* 	    BF_ALL
	* @par Remarks:
	*	    If the barcode type(s) are certain, specifying the barcode type(s) to be read will speed up the recognition process.
	*		The barcode format our library will search for is composed of [BarcodeFormat group 1](@ref BarcodeFormat) and [BarcodeFormat group 2](@ref BarcodeFormat_2), so you need to specify the barcode format in group 1 and group 2 individually.
	* @sa BarcodeFormat, BarcodeFormat_2
	*/
	int barcodeFormatIds;

	/**Sets the formats of the barcode in BarcodeFormat group 2 to be read. Barcode formats in BarcodeFormat group 2 can be combined.
	*
	* @par Value range:
	* 	    A combined value of BarcodeFormat_2 Enumeration items
	* @par Default value:
	* 	    BF2_NULL
	* @par Remarks:
	*	    If the barcode type(s) are certain, specifying the barcode type(s) to be read will speed up the recognition process.
	*		The barcode format our library will search for is composed of [BarcodeFormat group 1](@ref BarcodeFormat) and [BarcodeFormat group 2](@ref BarcodeFormat_2), so you need to specify the barcode format in group 1 and group 2 individually.
	* @sa BarcodeFormat, BarcodeFormat_2
	*/
	int barcodeFormatIds_2;

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
	* 	    [8, 0x7fffffff]
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

	/**Sets whether or not to return the clarity of the barcode zone.
	*
	* @par Value range:
	* 	    [0,1]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*     0 : Do not return the clarity of the barcode zone;
	*	  1 : Return the clarity of the batcode zone.
	*/
	int returnBarcodeZoneClarity;

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

	/**Sets the mode and priority to control the sampling methods of scale-up for linear barcode with small module sizes.
	*
	* @par Value range:
	* 	    Each array item can be any one of the ScaleUpMode Enumeration items.
	* @par Default value:
	* 	    [SUM_AUTO, SUM_SKIP, SUM_SKIP, SUM_SKIP, SUM_SKIP, SUM_SKIP, SUM_SKIP, SUM_SKIP]
	* @par Remarks:
	*		The array index represents the priority of the item. The smaller the index, the higher the priority.
	* @sa ScaleUpMode
	*/
	ScaleUpMode scaleUpModes[8];

	/**Sets the way to detect barcodes from a PDF file when using the DecodeFile method.
	*
	* @par Value range:
	* 	    Any one of the PDFReadingMode Enumeration items.
	* @par Default value:
	* 	    PDFRM_AUTO
	* @sa PDFReadingMode
	*/
	PDFReadingMode pdfReadingMode;

	/**Sets the mode and priority for deblur algorithms.
	*
	* @par Value range:
	* 	    Each array item can be any one of the DeblurMode Enumeration items.
	* @par Default value:
	* 	    [DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP, DM_SKIP]
	* @par Remarks:
	*		The array index represents the priority of the item. The smaller the index, the higher the priority.
	* @sa DeblurMode
	*/
	DeblurMode deblurModes[10];

	/**Sets barcode zone min distance to image borders.
	*
	* @par Value range:
	* 	    [0, 0x7fffffff]
	* @par Default value:
	* 	    0
	* @par Remarks:
	*     0: means no limitation on the barcode zone min distance.
	*/
	int barcodeZoneMinDistanceToImageBorders;


	/**Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[36];

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

	/**Sets whether to filter frames automatically.
	*
	* @par Value range:
	* 	    [0,1]
	* @par Default value:
	* 	    1
	* @par Remarks:
	*		0:Diable filtering frames automatically.
	*		1:Enable filtering frames automatically.
	*/
	int autoFilter;

	/**Sets the method used for calculating the clarity of the frames.
	*
	* @par Value range:
	*       Any one of the ClarityCalculationMethod Enumeration items
	* @par Default value:
	* 	    ECCM_CONTRAST
	* @sa ClarityCalculationMethod
	*/
	ClarityCalculationMethod clarityCalculationMethod;

	/**Sets the mode used for filtering frames by calculated clarity.
	*
	* @par Value range:
	* 	    Any one of the ClarityFilterMode Enumeration items
	* @par Default value:
	* 	    CFM_GENERAL
	* @sa ClarityFilterMode
	*/
	ClarityFilterMode clarityFilterMode;


	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct.
	*
	*/
	char reserved[20];
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

	/**Barcode type in BarcodeFormat group 1 */
	BarcodeFormat barcodeFormat;

	/**Barcode type in BarcodeFormat group 1 as string */
	const char* barcodeFormatString;

	/**Barcode type in BarcodeFormat group 2*/
	BarcodeFormat_2 barcodeFormat_2;

	/**Barcode type in BarcodeFormat group 2 as string */
	const char* barcodeFormatString_2;

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

	/**The sampling image info.*/
	SamplingImageData samplingImage;

	/**The clarity of the barcode zone in percentage.*/
	int clarity;

	/**Reserved memory for struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[40];
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

	/**Barcode type in BarcodeFormat group 1 */
	BarcodeFormat barcodeFormat;

	/**Barcode type in BarcodeFormat group 1 as string */
	const char* barcodeFormatString;

	/**Barcode type in BarcodeFormat group 2*/
	BarcodeFormat_2 barcodeFormat_2;

	/**Barcode type in BarcodeFormat group 2 as string */
	const char* barcodeFormatString_2;

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

	/**The confidence of the localization result*/
	int confidence;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[52];
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

	/**Barcode type in BarcodeFormat group 1 */
	BarcodeFormat barcodeFormat;

	/**Barcode type in BarcodeFormat group 1 as string */
	const char* barcodeFormatString;

	/**Barcode type in BarcodeFormat group 2*/
	BarcodeFormat_2 barcodeFormat_2;

	/**Barcode type in BarcodeFormat group 2 as string */
	const char* barcodeFormatString_2;

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
	
	/**Exception */
	const char* exception;
	
	/**DPM mark */
	int isDPM;

	/**Mirror flag*/
	int isMirrored;
	
	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[44];
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

	/**The position of the start pattern relative to the barcode location.
	Index 0 : X coordinate of the start position in percentage value;
	Index 1 : X coordinate of the end position in percentage value.*/
	float startPatternRange[2];

	/**The position of the middle pattern relative to the barcode location.
	Index 0 : X coordinate of the start position in percentage value;
	Index 1 : X coordinate of the end position in percentage value.*/
	float middlePatternRange[2];

	/**The position of the end pattern relative to the barcode location.
	Index 0 : X coordinate of the start position in percentage value;
	Index 1 : X coordinate of the end position in percentage value.*/
	float endPatternRange[2];

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[8];
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
	
	/**Identify the first data encoding mode */
	int mode;
	
	/**Identify the position of the particular symbol */
	int page;

	/**Identify the total number of symbols to be concatenated int the Structured Append format */
	int totalPage;
	
	/**The Parity Data shall be an 8 bit byte following the Symbol Sequence Indicator. 
	The parity data is a value obtained by XORing byte by byte the ASCII/JIS values of all the original input data before division into symbol blocks. */
	unsigned char parityData;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[16];
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

	/**One of the following types: Array of @ref Contour, Array of @ref ImageData, Array of @ref LineSegment, Array of @ref LocalizationResult, Array of @ref RegionOfInterest, Array of @ref Quadrilateral */
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

	/**The index of ForeAndBackgroundColour argument used for RegionPredetectionMode */
	int rpmColourArgumentIndex;

	/**Reserved memory for the struct. The length of this array indicates the size of the memory reserved for this struct. */
	char reserved[60];
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

	/**The confidence coefficients for lines.
	*There are 4 coefficients in this set:
	*linesConfidenceCoefficients[0] is average positive amplitude;
	*linesConfidenceCoefficients[1] is max positive amplitude;
	*linesConfidenceCoefficients[2] is average negative amplitude;
	*linesConfidenceCoefficients[3] is max negative amplitude.
	*/
	unsigned char* linesConfidenceCoefficients;
}LineSegment;

/**
 * @}defgroup LineSegment
 */

typedef struct tagDM_DLSConnectionParameters DM_DLSConnectionParameters;
typedef struct tagDM_DLSConnectionParameters DM_LTSConnectionParameters;

/**
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
	 */
	DBR_API const char* DBR_GetErrorString(int errorCode);

	/**
	 * Returns the version info of the SDK.
	 *
	 * @return The version info string.
	 *
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
	  */
	DBR_API void* DBR_CreateInstance();

	/**
	 * Destroys an instance of Dynamsoft Barcode Reader.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 *
	 */
	DBR_API void DBR_DestroyInstance(void* barcodeReader);

	/**
	* Initializes a DM_LTSConnectionParameters struct with default values. Deprecated, use DBR_InitDLSConnectionParameters instead.
	*
	* @param [in, out] pLTSConnectionParameters The struct of DM_LTSConnectionParameters.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message. Possible returns are:
	*		  DBR_OK;
	*		  DBRERR_NULL_POINTER;
	*
	*/
	DBR_API int DBR_InitLTSConnectionParameters(DM_LTSConnectionParameters *pLTSConnectionParameters);

	/**
	* Initializes a DM_DLSConnectionParameters struct with default values.
	*
	* @param [in, out] pDLSConnectionParameters The struct of DM_DLSConnectionParameters.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message. Possible returns are:
	*		  DBR_OK;
	*		  DBRERR_NULL_POINTER;
	*
	*/
	DBR_API int DBR_InitDLSConnectionParameters(DM_DLSConnectionParameters *pDLSConnectionParameters);

	/**
	* Get available instances count when charging by concurrent instances count.
	*
	* @return Returns available instances count. 
	*
	*/
	DBR_API int DBR_GetIdleInstancesCount();

	/**
	* Initializes the barcode reader license and connects to the specified server for online verification. Deprecated, use DBR_InitLicenseFromDLS instead.
	*
	* @param [in] pLTSConnectionParameters The struct DM_LTSConnectionParameters with customized settings.
	* @param [in, out] errorMsgBuffer The buffer is allocated by caller and the recommending length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	*/
	DBR_API int DBR_InitLicenseFromLTS(DM_LTSConnectionParameters *pLTSConnectionParameters, char errorMsgBuffer[], const int errorMsgBufferLen);


	/**
	* Initializes the barcode reader license and connects to the specified server for online verification.
	*
	* @param [in] pDLSConnectionParameters The struct DM_DLSConnectionParameters with customized settings.
	* @param [in, out] errorMsgBuffer The buffer is allocated by caller and the recommending length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	*/
	DBR_API int DBR_InitLicenseFromDLS(DM_DLSConnectionParameters *pDLSConnectionParameters, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Init Intermediate Result.
	*
	* @param [in] intermediateResultType The type of the intermediate result to init.
	* @param [in,out] pIntermediateResult The intermediate result struct.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	*/
	DBR_API int DBR_InitIntermediateResult(IntermediateResultType intermediateResultType, IntermediateResult* pIntermediateResult);

	/**
	 * Reads product key and activates the SDK.
	 *
	 * @param [in] pLicense The product keys.
	 * @param [in, out] errorMsgBuffer The buffer is allocated by caller and the recommending length is 256. The error message will be copied to the buffer.
	 * @param [in] errorMsgBufferLen The length of allocated buffer.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 */
	DBR_API int  DBR_InitLicense(const char* pLicense, char errorMsgBuffer[], const int errorMsgBufferLen);

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
	 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in, out] content The output string which stores the content of license.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 * @par Remarks:
	 *	    DBR_InitLicenseFromServer() has to be successfully called before calling this method.
	 */
	DBR_API int DBR_OutputLicenseToStringPtr(void* barcodeReader, char** content);

	/**
	 *Frees memory allocated for the license string.
	 *
	 * @param [in] content The output string which stores the content of license.
	 *
	 * @par Remarks:
	 *		DBR_OutputLicenseToStringPtr() has to be successfully called before calling this method.
	 */
	DBR_API void DBR_FreeLicenseString(char** content);

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
	 */
	DBR_API int DBR_DecodeDIB(void* barcodeReader, const HANDLE hDIB, const char* pTemplateName);

	/**
	* Decode barcodes from intermediate results.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] pIntermediateResultArray The intermediate result array for decoding.
	* @param [in] pTemplateName  The template name.
	*
	* @return Returns error code. Returns 0 if the function operates successfully. You can call
	* 		  DBR_GetErrorString() to get detailed error message.
	*
	*/
	DBR_API int DBR_DecodeIntermediateResults(void* barcodeReader, const IntermediateResultArray* pIntermediateResultArray, const char* pTemplateName);

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
	DBR_API int DBR_InitFrameDecodingParameters(void *barcodeReader, FrameDecodingParameters* pParameters);

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
	 */
	DBR_API int DBR_AppendFrame(void *barcodeReader, unsigned char *pBufferBytes);

	/**
	 * Gets current length of the inner frame queue.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 *
	 * @return Returns the length of the inner frame queue.
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
	  *
	  * @par Remarks:
	  *		Check @ref ModesArgument for available argument settings
	  *
	  */
	DBR_API int DBR_SetModeArgument(void *barcodeReader, const char *pModesName, const int index, const char *pArgumentName, const char *pArgumentValue, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Gets the optional argument for a specified mode in Modes parameters.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	* @param [in] pModesName The mode parameter name to get argument.
	* @param [in] index The array index of mode parameter to indicate a specific mode.
	* @param [in] pArgumentName The name of the argument to get.
	* @param [in,out] valueBuffer The buffer is allocated by caller and the recommended length is 480. The argument value would be copied to the buffer.
	* @param [in] valueBufferLen The length of allocated buffer.
	* @param [in,out] errorMsgBuffer The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
	* @param [in] errorMsgBufferLen The length of the allocated buffer.
	*
	* @return Returns error code. Returns 0 if the function operates successfully, otherwise call
	* 		   DBR_GetErrorString to get detail message. Possible returns are:
	* 		   DBR_OK;
	* 		   DBRERR_GET_MODE_ARGUMENT_ERROR;
	*
	* @par Remarks:
	*		Check @ref ModesArgument for available argument settings
	*
	*/
	DBR_API int DBR_GetModeArgument(void *barcodeReader, const char *pModesName, const int index, const char *pArgumentName, char valueBuffer[], const int valueBufferLen, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	 * Gets current settings and save them into a struct.
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in,out] pSettings The struct of template settings.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
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
	 */
	DBR_API int DBR_UpdateRuntimeSettings(void* barcodeReader, PublicRuntimeSettings *pSettings, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	 * Resets all parameters to default values.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
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
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_AppendTplFileToRuntimeSettings(void* barcodeReader, const char* pFilePath, const ConflictMode conflictMode, char errorMsgBuffer[], const int errorMsgBufferLen);

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
	*
	* @sa CFunctions PublicRuntimeSettings
	*/
	DBR_API int  DBR_AppendTplStringToRuntimeSettings(void* barcodeReader, const char* content, const ConflictMode conflictMode, char errorMsgBuffer[], const int errorMsgBufferLen);

	/**
	* Gets count of parameter templates.
	*
	* @param [in] barcodeReader Handle of the barcode reader instance.
	*
	* @return Returns the count of parameter templates. Returns -1 if DBRERR_NULL_POINTER happens.
	*
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
	*
	*/
	DBR_API int DBR_OutputSettingsToString(void* barcodeReader, char content[], const int contentLen, const char* pSettingsName);

	/**
	 * Outputs runtime settings to a string.
	 *
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in,out] content The output string which stores the contents of current settings.
	 * @param [in] pSettingsName A unique name for declaring current runtime settings.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
	 *
	 */
	DBR_API int DBR_OutputSettingsToStringPtr(void* barcodeReader, char** content, const char* pSettingsName);

	/**
	* Free memory allocated for runtime settings string.
	*
	* @param [in] content The runtime settings string.
	*
	*
	*/
	DBR_API void DBR_FreeSettingsString(char** content);

	/**
	 * Outputs runtime settings and save them into a settings file (JSON file).
	 * X
	 * @param [in] barcodeReader Handle of the barcode reader instance.
	 * @param [in] pFilePath The path of the output file which stores current settings.
	 * @param [in] pSettingsName A unique name for declaring current runtime settings.
	 *
	 * @return Returns error code. Returns 0 if the function operates successfully. You can call
	 * 		   DBR_GetErrorString() to get detailed error message.
	 *
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
	  */
	DBR_API int DBR_GetAllTextResults(void* barcodeReader, TextResultArray **pResults);

	/**
	 * Frees memory allocated for text results.
	 *
	 * @param [in] pResults Text results.
	 *
	 *
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
	 *
	 */
	DBR_API int DBR_GetIntermediateResults(void *barcodeReader, IntermediateResultArray **pResult);

	/**
	 * Frees memory allocated for the intermediate results.
	 *
	 * @param [in] pResults The intermediate results.
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

namespace dynamsoft
{
	namespace dbr
	{
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
			BarcodeReaderInner * m_pBarcodeReader;

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
			  *
			  */
			static const char* GetErrorString(const int iErrorCode);

			/**
			 * Returns the version info of the SDK.
			 *
			 * @return The version info string.
			 *
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
			* Initializes a DM_LTSConnectionParameters struct with default values. Deprecated, use InitDLSConnectionParameters instead.
			*
			* @param [in,out] pLTSConnectionParameters The struct of DM_LTSConnectionParameters.
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			static int InitLTSConnectionParameters(DM_LTSConnectionParameters *pLTSConnectionParameters);

			/**
			* Initializes a DM_DLSConnectionParameters struct with default values.
			*
			* @param [in,out] pDLSConnectionParameters The struct of DM_DLSConnectionParameters.
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			static int InitDLSConnectionParameters(DM_DLSConnectionParameters *pDLSConnectionParameters);

			/**
			* Get available instances count when charging by concurrent instances count.
			*
			* @return Returns available instances count.
			*
			*/
			static int GetIdleInstancesCount();

			/**
			* Initializes the barcode reader license and connects to the specified server for online verification. Deprecated, use InitLicenseFromDLS instead.
			*
			* @param [in] pLTSConnectionParameters The struct DM_LTSConnectionParameters with customized settings.
			* @param [in, out] errorMsgBuffer (Optional) The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
			* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			static int InitLicenseFromLTS(DM_LTSConnectionParameters *pLTSConnectionParameters, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);


			/**
			* Initializes the barcode reader license and connects to the specified server for online verification.
			*
			* @param [in] pDLSConnectionParameters The struct DM_DLSConnectionParameters with customized settings.
			* @param [in, out] errorMsgBuffer (Optional) The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
			* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			static int InitLicenseFromDLS(DM_DLSConnectionParameters *pDLSConnectionParameters, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

			/**
			* Init Intermediate Result.
			*
			* @param [in] intermediateResultType The type of the intermediate result to init.
			* @param [in,out] pIntermediateResult The intermediate result struct.
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			int InitIntermediateResult(IntermediateResultType intermediateResultType, IntermediateResult* pIntermediateResult);

			/**
			 * Reads product key and activates the SDK.
			 *
			 * @param [in] pLicense The product keys.
			 * @param [in, out] errorMsgBuffer The buffer is allocated by caller and the recommending length is 256. The error message will be copied to the buffer.
			 * @param [in] errorMsgBufferLen The length of allocated buffer.
			 *
			 * @return Returns error code. Returns 0 if the function operates successfully. You can call
			 * 		   GetErrorString() to get detailed error message.
			 *
			 */
			static int InitLicense(const char* pLicense, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

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
			 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
			 *
			 * @param [in, out] content The output string which stores the content of license.
			 *
			 * @return Returns error code. Returns 0 if the function operates successfully. You can call
			 * 		   GetErrorString() to get detailed error message.
			 * @par Remarks:
			 *	    InitLicenseFromServer() has to be successfully called before calling this method.
			 */
			int OutputLicenseToStringPtr(char** content);

			/**
			 *Frees memory allocated for the license string.
			 *
			 * @param [in] content The output string which stores the content of license.
			 *
			 * @par Remarks:
			 *		OutputLicenseToStringPtr() has to be successfully called before calling this method.
			 */
			void FreeLicenseString(char** content);

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
			 *
			 * @par Remarks:
			 * If no template name is specified, current runtime settings will be used.
			 */
			int DecodeDIB(const HANDLE  hDIB, const char* pszTemplateName = "");

			/**
			* Decode barcodes from intermediate results.
			*
			* @param [in] pIntermediateResultArray The intermediate results.
			* @param [in] pTemplateName (optional) The template name.
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		  DBR_GetErrorString() to get detailed error message.
			*
			*/
			int DecodeIntermediateResults(const IntermediateResultArray* pIntermediateResultArray, const char* pTemplateName = "");

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
			 *
			 */
			int AppendFrame(unsigned char *pBufferBytes);

			/**
			 * Gets current length of the inner frame queue.
			 *
			 * @return Returns the length of the inner frame queue.
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
			 *
			 */
			int UpdateRuntimeSettings(PublicRuntimeSettings *pSettings, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

			/**
			* Resets all parameters to default values.
			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			 * 		   GetErrorString() to get detailed error message.
			*
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
			 *
			 * @par Remarks:
			 *		Check @ref ModesArgument for available argument settings
			 *
			 */
			int SetModeArgument(const char *pModesName, const int index, const char *pArgumentName, const char *pArgumentValue, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

			/**
			* Gets the optional argument for a specified mode in Modes parameters.
			*
			* @param [in] pModesName The mode parameter name to get argument.
			* @param [in] index The array index of mode parameter to indicate a specific mode.
			* @param [in] pArgumentName The name of the argument to get.
			* @param [in,out] valueBuffer The buffer is allocated by caller and the recommended length is 480. The argument value would be copied to the buffer.
			* @param [in] valueBufferLen The length of allocated buffer.
			* @param [in,out] errorMsgBuffer (Optional) The buffer is allocated by the caller and the recommended length is 256. The error message will be copied to the buffer.
			* @param [in] errorMsgBufferLen (Optional) The length of the allocated buffer.
			*
			* @return Returns error code. Returns 0 if the function operates successfully, otherwise call
			* 		   GetErrorString to get detail message. Possible returns are:
			* 		   DBR_OK;
			* 		   DBRERR_GET_MODE_ARGUMENT_ERROR;
			*
			* @par Remarks:
			*		Check @ref ModesArgument for available argument settings
			*
			*/
			int GetModeArgument(const char *pModesName, const int index, const char *pArgumentName, char valueBuffer[], const int valueBufferLen, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);
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
			*
			* @sa CBarcodeReader PublicRuntimeSettings
			*/
			int  AppendTplStringToRuntimeSettings(const char* content, const ConflictMode conflictMode, char errorMsgBuffer[] = NULL, const int errorMsgBufferLen = 0);

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
			* @param [in] index The index of the parameter template array.
			* @param [in,out] nameBuffer The buffer is allocated by caller and the recommended
			* 				   nameBufferLen is 256. The template name will be copied to the buffer.
			* @param [in] nameBufferLen The length of allocated buffer.

			*
			* @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		   GetErrorString() to get detailed error message.
			*
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
			*
			*/
			int OutputSettingsToString(char content[], const int contentLen, const char* pSettingsName);

			/**
			 * Outputs runtime settings to a string.
			 *
			 * @param [in,out] content The output string which stores the contents of current settings.
			 * @param [in] pSettingsName A unique name for declaring current runtime settings.
			 *
			 * @return Returns error code. Returns 0 if the function operates successfully. You can call
			* 		   GetErrorString() to get detailed error message.
			 *
			 */
			int OutputSettingsToStringPtr(char** content, const char* pSettingsName);

			/**
			* Free memory allocated for runtime settings string.
			*
			* @param [in] content The runtime settings string.
			*
			*
			*/
			void FreeSettingsString(char** content);

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
			  *
			  */
			int GetAllTextResults(TextResultArray **pResults);

			/**
			 * Frees memory allocated for text results.
			 *
			 * @param [in] pResults Text results.
			 *
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
			 *
			 */
			int GetIntermediateResults(IntermediateResultArray **pResults);

			/**
			 * Frees memory allocated for the intermediate results.
			 *
			 * @param [in] pResults The intermediate results.
			 *
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

	}
}
#endif // endif of __cplusplus.



#pragma endregion

#endif
