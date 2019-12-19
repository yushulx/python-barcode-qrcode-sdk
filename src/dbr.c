#include <Python.h>
#include "DynamsoftBarcodeReader.h"
#include <ndarraytypes.h>
#include <structmember.h>

#ifndef DEBUG
#define DEBUG 0
#endif

#if PY_MAJOR_VERSION >= 3
#ifndef IS_PY3K
#define IS_PY3K 1
#endif
#endif

struct module_state
{
    PyObject *error;
};

#if defined(IS_PY3K)
#define GETSTATE(m) ((struct module_state *)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject *
error_out(PyObject *m)
{
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

#define DBR_NO_MEMORY 0
#define DBR_SUCCESS 1

// #define LOG_OFF

#ifdef LOG_OFF

#define printf(MESSAGE, __VA_ARGS__)

#endif

#define DEFAULT_MEMORY_SIZE 4096

typedef struct
{
    PyObject_HEAD
    PyObject *COLOR_CLUTERING_MODE;
    PyObject *COLOR_CONVERSION_MODE;
    PyObject *GRAY_SCALE_TRANSFORMATION_MODE;
    PyObject *REGION_PREDETECTION_MODE;
    PyObject *IMAGE_PREPROCESSING_MODE;
    PyObject *TEXTURE_DETECTION_MODE;
    PyObject *TEXTURE_FILTER_MODE;
    PyObject *TEXT_ASSISTED_CORRECTION_MODE;
    PyObject *DPM_CODE_READING_MODE;
    PyObject *DEFORMATION_RESISTING_MODE;
    PyObject *BARCODE_COMPLEMENT_MODE;
    PyObject *BARCODE_COLOR_MODE;
    // GRAY_SCALE_TRANSFORMATION_MODE
    int GTM_INVERTED;
    int GTM_ORIGINAL;
    int GTM_SKIP;
    // Barcode formats
    int BF_ALL;
    int BF_ONED;
    int BF_GS1_DATABAR;
    int BF_POSTALCODE;
    int BF_CODE_39;
    int BF_CODE_128;
    int BF_CODE_93;
    int BF_CODABAR;
    int BF_ITF;
    int BF_EAN_13;
    int BF_EAN_8;
    int BF_UPC_A;
    int BF_UPC_E;
    int BF_INDUSTRIAL_25;
    int BF_CODE_39_EXTENDED;
    int BF_GS1_DATABAR_OMNIDIRECTIONAL;
    int BF_GS1_DATABAR_TRUNCATED;
    int BF_GS1_DATABAR_STACKED;
    int BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL;
    int BF_GS1_DATABAR_EXPANDED;
    int BF_GS1_DATABAR_EXPANDED_STACKED;
    int BF_GS1_DATABAR_LIMITED;
    int BF_PATCHCODE;
    int BF_USPSINTELLIGENTMAIL;
    int BF_POSTNET;
    int BF_PLANET;
    int BF_AUSTRALIANPOST;
    int BF_UKROYALMAIL;
    int BF_PDF417;
    int BF_QR_CODE;
    int BF_DATAMATRIX;
    int BF_AZTEC;
    int BF_MAXICODE;
    int BF_MICRO_QR;
    int BF_MICRO_PDF417;
    int BF_GS1_COMPOSITE;
    int BF_NULL;
    // Barcode reader handler
    void *hBarcode;
    // Callback function for video mode
    PyObject *py_callback;
} DynamsoftBarcodeReader;

void ToHexString(unsigned char* pSrc, int iLen, char* pDest)
{
	const char HEXCHARS[16] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };

	int i;
	char* ptr = pDest;

	for(i = 0; i < iLen; ++i)
	{
		snprintf(ptr, 4, "%c%c ", HEXCHARS[ ( pSrc[i] & 0xF0 ) >> 4 ], HEXCHARS[ ( pSrc[i] & 0x0F ) >> 0 ]);
		ptr += 3;
	}
}

/**
 * Set Dynamsoft Barcode Reader license.  
 * To get valid license, please contact support@dynamsoft.com
 * Invalid license is acceptable. With an invalid license, SDK will return an imcomplete result.
 */
static PyObject *
initLicense(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicense;
    if (!PyArg_ParseTuple(args, "s", &pszLicense))
    {
        return NULL;
    }

    int ret = DBR_InitLicense(self->hBarcode, pszLicense);
    return Py_BuildValue("i", ret);
}

static PyObject *createPyResults(TextResultArray *pResults, const char* encoding)
{
    if (!pResults)
    {
        printf("No barcode detected\n");
        return NULL;
    }
    // Get barcode results
    int count = pResults->resultsCount;

    // Create a Python object to store results
    PyObject *list = PyList_New(count);
    // printf("count: %d\n", count);
    PyObject *result = NULL;
    int i = 0;
    for (; i < count; i++)
    {
        LocalizationResult *pLocalizationResult = pResults->results[i]->localizationResult;
        int x1 = pLocalizationResult->x1;
        int y1 = pLocalizationResult->y1;
        int x2 = pLocalizationResult->x2;
        int y2 = pLocalizationResult->y2;
        int x3 = pLocalizationResult->x3;
        int y3 = pLocalizationResult->y3;
        int x4 = pLocalizationResult->x4;
        int y4 = pLocalizationResult->y4;
        PyObject *pyObject = NULL;
        if (encoding) {
            pyObject = PyList_New(10);
        #ifdef IS_PY3K
            PyObject *format = PyUnicode_FromString(pResults->results[i]->barcodeFormatString);
        #else
            PyObject *format = PyString_FromString(pResults->results[i]->barcodeFormatString);
        #endif
            PyList_SetItem(pyObject, 0, format);
            
            PyObject *result = PyUnicode_Decode(pResults->results[i]->barcodeBytes, pResults->results[i]->barcodeBytesLength, encoding, "strict");
            if (result == NULL) 
            {
                char *hex = (char*)malloc(pResults->results[i]->barcodeBytesLength * 3 + 1);
                ToHexString(pResults->results[i]->barcodeBytes, pResults->results[i]->barcodeBytesLength, hex);
                printf("Hex Data: %s\n", hex);
                free(hex);

                PyErr_SetString(PyExc_TypeError, "Incorrect character set! Failed to decode barcode results!");
                DBR_FreeTextResults(&pResults);
                return NULL;
            }
            PyList_SetItem(pyObject, 1, result);

            PyObject *x1_pyobj = Py_BuildValue("i", x1);
            PyList_SetItem(pyObject, 2, x1_pyobj);

            PyObject *y1_pyobj = Py_BuildValue("i", y1);
            PyList_SetItem(pyObject, 3, y1_pyobj);

            PyObject *x2_pyobj = Py_BuildValue("i", x2);
            PyList_SetItem(pyObject, 4, x2_pyobj);

            PyObject *y2 = Py_BuildValue("i", y2);
            PyList_SetItem(pyObject, 5, y2);

            PyObject *x3_pyobj = Py_BuildValue("i", x3);
            PyList_SetItem(pyObject, 6, x3_pyobj);

            PyObject *y3_pyobj = Py_BuildValue("i", y3);
            PyList_SetItem(pyObject, 7, y3_pyobj);

            PyObject *x4_pyobj = Py_BuildValue("i", x4);
            PyList_SetItem(pyObject, 8, x4_pyobj);

            PyObject *y4_pyobj = Py_BuildValue("i", y4);
            PyList_SetItem(pyObject, 9, y4_pyobj);

        }
        else
            pyObject = Py_BuildValue("ssiiiiiiii", pResults->results[i]->barcodeFormatString, pResults->results[i]->barcodeText, x1, y1, x2, y2, x3, y3, x4, y4);
        
        PyList_SetItem(list, i, pyObject); // Add results to list

        // Print out PyObject if needed
        if (DEBUG)
        {
#if defined(IS_PY3K)
            PyObject *objectsRepresentation = PyObject_Repr(list);
            const char *s = PyUnicode_AsUTF8(objectsRepresentation);
            printf("Results: %s\n", s);
#else
            PyObject *objectsRepresentation = PyObject_Repr(list);
            const char *s = PyString_AsString(objectsRepresentation);
            printf("Results: %s\n", s);
#endif
        }
    }

    // Release memory
    DBR_FreeTextResults(&pResults);

    return list;
}

void updateFormat(DynamsoftBarcodeReader *self, int format)
{
    // Update DBR params
    PublicRuntimeSettings pSettings = {0};
    DBR_GetRuntimeSettings(self->hBarcode, &pSettings);
    pSettings.barcodeFormatIds = format;
    char szErrorMsgBuffer[256];
    DBR_UpdateRuntimeSettings(self->hBarcode, &pSettings, szErrorMsgBuffer, 256);
}

/**
 * Decode barcode from a file 
 */
static PyObject *
decodeFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
#if defined(_WIN32)
    printf("Windows\n");
#elif defined(__linux__)
    printf("Linux\n");
#elif defined(__APPLE__)
    printf("MacOS\n");
#else
    printf("Unknown Operating System.\n");
#endif

    char *pFileName; // File name
    int iFormat;     // Barcode formats
    char *templateName = NULL;
    char *encoding = NULL;
    if (!PyArg_ParseTuple(args, "si|ss", &pFileName, &iFormat, &templateName, &encoding))
    {
        return NULL;
    }

    updateFormat(self, iFormat);

    TextResultArray *pResults = NULL;

    // Barcode detection
    int ret = DBR_DecodeFile(self->hBarcode, pFileName, templateName ? templateName : "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }
    DBR_GetAllTextResults(self->hBarcode, &pResults);

    // Wrap results
    PyObject *list = createPyResults(pResults, encoding);
    return list;
}

/**
 * Decode barcode from an image buffer. 
 */
static PyObject *
decodeBuffer(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *o;
    int iFormat;
    char *templateName = NULL;
    char *encoding = NULL;
    if (!PyArg_ParseTuple(args, "Oi|ss", &o, &iFormat, &templateName, &encoding))
        return NULL;

    updateFormat(self, iFormat);

#if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
        return NULL;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    char *buffer = (char *)view->buf;
    nd = view->ndim;
    int len = view->len;
    int stride = view->strides[0];
    int width = view->strides[0] / view->strides[1];
    int height = len / stride;
    Py_DECREF(memoryview);
#else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao))
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        return NULL;
    }

    PyArrayInterface *pai = (PyArrayInterface *)PyCObject_AsVoidPtr(ao);

    if (pai->two != 2)
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
        return NULL;
    }

    // Get image information
    char *buffer = (char *)pai->data;  // The address of image data
    int width = (int)pai->shape[1];    // image width
    int height = (int)pai->shape[0];   // image height
    int stride = (int)pai->strides[0]; // image stride
    Py_DECREF(ao);
#endif

    // Initialize Dynamsoft Barcode Reader
    TextResultArray *pResults = NULL;

    // Detect barcodes
    ImagePixelFormat format = IPF_RGB_888;

    if (width == stride)
    {
        format = IPF_GRAYSCALED;
    }
    else if (width * 3 == stride)
    {
        format = IPF_RGB_888;
    }
    else if (width * 4 == stride)
    {
        format = IPF_ARGB_8888;
    }

    PyObject *list = NULL;
    int ret = DBR_DecodeBuffer(self->hBarcode, buffer, width, height, stride, format, templateName ? templateName : "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }
    // Wrap results
    DBR_GetAllTextResults(self->hBarcode, &pResults);
    list = createPyResults(pResults, encoding);

#if defined(IS_PY3K)
    Py_DECREF(memoryview);
#else
    Py_DECREF(ao);
#endif

    return list;
}

/**
 * Decode file stream. 
 */
static PyObject *
decodeFileStream(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
#if defined(_WIN32)
    printf("Windows\n");
#elif defined(__linux__)
    printf("Linux\n");
#elif defined(__APPLE__)
    printf("MacOS\n");
#else
    printf("Unknown Operating System.\n");
#endif

    PyObject *op; 
    int fileSize;
    int iFormat;     // Barcode formats
    char *templateName = NULL;
    char *encoding = NULL;
    if (!PyArg_ParseTuple(args, "Oii|ss", &op, &fileSize, &iFormat, &templateName, &encoding))
    {
        return NULL;
    }

    updateFormat(self, iFormat);

    TextResultArray *pResults = NULL;
    // https://docs.python.org/2/c-api/bytearray.html
    char *filestream = PyByteArray_AsString(op);
    // Barcode detection
    int ret = DBR_DecodeFileInMemory(self->hBarcode, filestream, fileSize, templateName ? templateName : "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }
    DBR_GetAllTextResults(self->hBarcode, &pResults);

    // Wrap results
    PyObject *list = createPyResults(pResults, encoding);
    return list;
}


void onResultCallback(int frameId, TextResultArray *pResults, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;
    // Get barcode results
    int count = pResults->resultsCount;
    int i = 0;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *list = PyList_New(count);
    for (; i < count; i++)
    {
        LocalizationResult *pLocalizationResult = pResults->results[i]->localizationResult;
        int x1 = pLocalizationResult->x1;
        int y1 = pLocalizationResult->y1;
        int x2 = pLocalizationResult->x2;
        int y2 = pLocalizationResult->y2;
        int x3 = pLocalizationResult->x3;
        int y3 = pLocalizationResult->y3;
        int x4 = pLocalizationResult->x4;
        int y4 = pLocalizationResult->y4;

        PyObject *pyObject = Py_BuildValue("ssiiiiiiii", pResults->results[i]->barcodeFormatString, pResults->results[i]->barcodeText, x1, y1, x2, y2, x3, y3, x4, y4);
        PyList_SetItem(list, i, pyObject); // Add results to list
    }

    PyObject *result = PyObject_CallFunction(self->py_callback, "O", list);
    if (result != NULL)
    	Py_DECREF(result);

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeTextResults(&pResults);
}

/**
 * Read barcodes from continuous video frames
 */
static PyObject *
startVideoMode(PyObject *obj, PyObject *args)
{
    printf("Start the video mode\n");
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *callback = NULL;
    int maxListLength, maxResultListLength, width, height, imageformat, iFormat, stride;
    if (!PyArg_ParseTuple(args, "iiiiiiO", &maxListLength, &maxResultListLength, &width, &height, &imageformat, &iFormat, &callback))
    {
        return NULL;
    }

    updateFormat(self, iFormat);

    if (!PyCallable_Check(callback))
    {
        PyErr_SetString(PyExc_TypeError, "parameter must be callable");
        return NULL;
    }
    else
    {
        Py_XINCREF(callback);    /* Add a reference to new callback */
        Py_XDECREF(self->py_callback); /* Dispose of previous callback */
        self->py_callback = callback;
    }

    ImagePixelFormat format = IPF_RGB_888;

    if (imageformat == 0)
    {
        stride = width;
        format = IPF_GRAYSCALED;
    }
    else
    {
        stride = width * 3;
        format = IPF_RGB_888;
    }

    DBR_SetTextResultCallback(self->hBarcode, onResultCallback, self);

    int ret = DBR_StartFrameDecoding(self->hBarcode, maxListLength, maxResultListLength, width, height, stride, format, "");
    return Py_BuildValue("i", ret);
}

static PyObject *
stopVideoMode(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    printf("Stop the video mode\n");
    if (self->hBarcode)
    {
        int ret = DBR_StopFrameDecoding(self->hBarcode);
        return Py_BuildValue("i", ret);
    }

    return 0;
}

static PyObject *
appendVideoFrame(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *o;
    if (!PyArg_ParseTuple(args, "O", &o))
        return NULL;

#if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
        return NULL;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    unsigned char *buffer = (unsigned char *)view->buf;
    nd = view->ndim;
    int len = view->len;
    int stride = view->strides[0];
    int width = view->strides[0] / view->strides[1];
    int height = len / stride;
    Py_DECREF(memoryview);
#else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao))
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        return NULL;
    }

    PyArrayInterface *pai = (PyArrayInterface *)PyCObject_AsVoidPtr(ao);

    if (pai->two != 2)
    {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
        return NULL;
    }

    // Get image information
    unsigned char *buffer = (unsigned char *)pai->data; // The address of image data
    int width = (int)pai->shape[1];                     // image width
    int height = (int)pai->shape[0];                    // image height
    int stride = (int)pai->strides[0];                  // image stride
	Py_DECREF(ao);
#endif

    // Initialize Dynamsoft Barcode Reader
    TextResultArray *pResults = NULL;

    // Detect barcodes
    ImagePixelFormat format = IPF_RGB_888;

    if (width == stride)
    {
        format = IPF_GRAYSCALED;
    }
    else if (width == stride * 3)
    {
        format = IPF_RGB_888;
    }
    else if (width == stride * 4)
    {
        format = IPF_ARGB_8888;
    }

    int frameId = DBR_AppendFrame(self->hBarcode, buffer);
    return 0;
}

/**
 * Initializes barcode reader license from the license content on the client machine for offline verification.
 *
 * @param pLicenseKey: The license key of Barcode Reader.
 * @param pLicenseContent: An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method DBR_OutputLicenseToString().
 *
 * @return Return 0 if the function operates successfully, otherwise call
 * 		   DBR_GetErrorString to get detail message.
 */
static PyObject *
initLicenseFromLicenseContent(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicenseKey;
    char *pszLicenseContent;
    if (!PyArg_ParseTuple(args, "ss", &pszLicenseKey, &pszLicenseContent))
    {
        return NULL;
    }

    int ret = DBR_InitLicenseFromLicenseContent(self->hBarcode, pszLicenseKey, pszLicenseContent);
    return Py_BuildValue("i", ret);
}

/**
 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
 *
 * @return if successful, return encypted string. Otherwise return error code. 
 */
static PyObject *
outputLicenseToString(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char content[512];
    int ret = DBR_OutputLicenseToString(self->hBarcode, content, 512);
    if (ret)
    {
        printf("%s\n", DBR_GetErrorString(ret));
        return Py_BuildValue("i", ret);
    }
    else
        return Py_BuildValue("s", content);
}

/**
 * Initializes barcode reader license from the license content on the client machine for offline verification.
 *
 * @param pLicenseKey: The license key of Barcode Reader.
 * @param pLicenseContent: An encrypted string representing the license content (runtime number, expiry date, barcode type, etc.) obtained from the method DBR_OutputLicenseToString().
 *
 * @return Return 0 if the function operates successfully, otherwise call
 * 		   DBR_GetErrorString to get detail message.
 */
static PyObject *
initLicenseFromServer(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pszLicenseKey, *pLicenseServer;
    if (!PyArg_ParseTuple(args, "ss", &pLicenseServer, &pszLicenseKey))
    {
        return NULL;
    }

    int ret = DBR_InitLicenseFromServer(self->hBarcode, pLicenseServer, pszLicenseKey);
    return Py_BuildValue("i", ret);
}

static void setModeValue(DynamsoftBarcodeReader *self, PyObject *iter, char *mode)
{
    PublicRuntimeSettings pSettings = {0};
    DBR_GetRuntimeSettings(self->hBarcode, &pSettings);
    int index = 0;
    pSettings.furtherModes.grayscaleTransformationModes[0] = GTM_INVERTED;

    while (1)
    {
        PyObject *next = PyIter_Next(iter);
        if (!next)
        {
            break;
        }

        // Set attributes for different modes
        int attribute = PyLong_AsLong(next);
        if (!strcmp("grayscaleTransformationModes", mode))
        {
            // printf("Set grayscaleTransformationModes %d\n", attribute);
            pSettings.furtherModes.grayscaleTransformationModes[index] = attribute;
        }
        else if (!strcmp("colourClusteringModes", mode))
        {
            pSettings.furtherModes.colourClusteringModes[index] = attribute;
        }
        else if (!strcmp("colourConversionModes", mode))
        {
            pSettings.furtherModes.colourConversionModes[index] = attribute;
        }
        else if (!strcmp("regionPredetectionModes", mode))
        {
            pSettings.furtherModes.regionPredetectionModes[index] = attribute;
        }
        else if (!strcmp("imagePreprocessingModes ", mode))
        {
            pSettings.furtherModes.imagePreprocessingModes[index] = attribute;
        }
        else if (!strcmp("textureDetectionModes", mode))
        {
            pSettings.furtherModes.textureDetectionModes[index] = attribute;
        }
        else if (!strcmp("textFilterModes", mode))
        {
            pSettings.furtherModes.textFilterModes[index] = attribute;
        }
        else if (!strcmp("dpmCodeReadingModes", mode))
        {
            pSettings.furtherModes.dpmCodeReadingModes[index] = attribute;
        }
        else if (!strcmp("deformationResistingModes ", mode))
        {
            pSettings.furtherModes.deformationResistingModes[index] = attribute;
        }
        else if (!strcmp("barcodeComplementModes ", mode))
        {
            pSettings.furtherModes.barcodeComplementModes[index] = attribute;
        }
        else if (!strcmp("barcodeColourModes ", mode))
        {
            pSettings.furtherModes.barcodeColourModes[index] = attribute;
        }
        else if (!strcmp("textAssistedCorrectionMode", mode))
        {
            pSettings.furtherModes.textAssistedCorrectionMode = attribute;
        }

        ++index;
    }

    char szErrorMsgBuffer[256];
    DBR_UpdateRuntimeSettings(self->hBarcode, &pSettings, szErrorMsgBuffer, 256);
}

/**
 * Set modes for different scenarios.
 *
 * @param mode: The mode name. E.g. dbr.GRAY_SCALE_TRANSFORMATION_MODE
 * @param values: A list of enumeration items. E.g. [dbr.GTM_INVERTED, dbr.GTM_ORIGINAL]
 *
 * @return Return NULL if failed.
 */
static PyObject *
setFurtherModes(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *mode;
    PyObject *value;
    if (!PyArg_ParseTuple(args, "sO", &mode, &value))
    {
        return NULL;
    }

    PyObject *iter = PyObject_GetIter(value);
    if (!iter)
    {
        printf("Please input a list\n");
        return NULL;
    }

    setModeValue(self, iter, mode);
    return Py_BuildValue("i", 0);
}

/**
 * Set public settings with JSON object.
 *
 * @param json: the stringified JSON object.
 * 
 * @return Return 0 if the function operates successfully.
 */
static PyObject *
setParameters(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *json;
    if (!PyArg_ParseTuple(args, "s", &json))
    {
        return NULL;
    }

    char errorMessage[DEFAULT_MEMORY_SIZE];
    int ret = DBR_InitRuntimeSettingsWithString(self->hBarcode, json, CM_OVERWRITE, errorMessage, 256);
    if (ret) 
    {
        printf("Returned value: %d, error message: %s\n", ret, errorMessage);
        PyErr_SetString(PyExc_TypeError, "DBR_InitRuntimeSettingsWithString() failed");
        return NULL;
    }
    return Py_BuildValue("i", ret);
}

/**
 * Get public settings.
 *
 * @return Return stringified JSON object.
 */
static PyObject *
getParameters(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char errorMessage[DEFAULT_MEMORY_SIZE];
    char pContent[DEFAULT_MEMORY_SIZE];

    int ret = DBR_OutputSettingsToString(self->hBarcode, pContent, DEFAULT_MEMORY_SIZE, "currentRuntimeSettings");
    // printf("pContent: %s\n, string len: %d", pContent, strlen(pContent));
    if (ret) 
    {
        printf("Returned value: %d, error message: %s\n", ret, errorMessage);
        PyErr_SetString(PyExc_TypeError, "DBR_OutputSettingsToString() failed");
        return NULL;
    }
    return Py_BuildValue("s", pContent);
}

static PyMemberDef dbr_members[] = {
    {"COLOR_CLUTERING_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, COLOR_CLUTERING_MODE), 0,
     NULL},
    {"COLOR_CONVERSION_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, COLOR_CONVERSION_MODE), 0,
     NULL},
    {"GRAY_SCALE_TRANSFORMATION_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, GRAY_SCALE_TRANSFORMATION_MODE), 0,
     NULL},
    {"REGION_PREDETECTION_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, REGION_PREDETECTION_MODE), 0,
     NULL},
    {"IMAGE_PREPROCESSING_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, IMAGE_PREPROCESSING_MODE), 0,
     NULL},
    {"TEXTURE_DETECTION_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, TEXTURE_DETECTION_MODE), 0,
     NULL},
    {"TEXTURE_FILTER_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, TEXTURE_FILTER_MODE), 0,
     NULL},
    {"TEXT_ASSISTED_CORRECTION_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, TEXT_ASSISTED_CORRECTION_MODE), 0,
     NULL},
    {"DPM_CODE_READING_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, DPM_CODE_READING_MODE), 0,
     NULL},
    {"DEFORMATION_RESISTING_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, DEFORMATION_RESISTING_MODE), 0,
     NULL},
    {"BARCODE_COMPLEMENT_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, BARCODE_COMPLEMENT_MODE), 0,
     NULL},
    {"BARCODE_COLOR_MODE", T_OBJECT_EX, offsetof(DynamsoftBarcodeReader, BARCODE_COLOR_MODE), 0,
     NULL},
    {"GTM_INVERTED", T_INT, offsetof(DynamsoftBarcodeReader, GTM_INVERTED), 0,
     NULL},
    {"GTM_ORIGINAL", T_INT, offsetof(DynamsoftBarcodeReader, GTM_ORIGINAL), 0,
     NULL},
    {"GTM_SKIP", T_INT, offsetof(DynamsoftBarcodeReader, GTM_SKIP), 0,
     NULL},
     {"BF_ALL", T_INT, offsetof(DynamsoftBarcodeReader, BF_ALL), 0,
     NULL},
     {"BF_ONED", T_INT, offsetof(DynamsoftBarcodeReader, BF_ONED), 0,
     NULL},
     {"BF_GS1_DATABAR", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR), 0,
     NULL},
     {"BF_POSTALCODE", T_INT, offsetof(DynamsoftBarcodeReader, BF_POSTALCODE), 0,
     NULL},
     {"BF_CODE_39", T_INT, offsetof(DynamsoftBarcodeReader, BF_CODE_39), 0,
     NULL},
     {"BF_CODE_128", T_INT, offsetof(DynamsoftBarcodeReader, BF_CODE_128), 0,
     NULL},
     {"BF_CODE_93", T_INT, offsetof(DynamsoftBarcodeReader, BF_CODE_93), 0,
     NULL},
     {"BF_CODABAR", T_INT, offsetof(DynamsoftBarcodeReader, BF_CODABAR), 0,
     NULL},
     {"BF_ITF", T_INT, offsetof(DynamsoftBarcodeReader, BF_ITF), 0,
     NULL},
      {"BF_EAN_13", T_INT, offsetof(DynamsoftBarcodeReader, BF_EAN_13), 0,
     NULL},
     {"BF_EAN_8", T_INT, offsetof(DynamsoftBarcodeReader, BF_EAN_8), 0,
     NULL},
     {"BF_UPC_A", T_INT, offsetof(DynamsoftBarcodeReader, BF_UPC_A), 0,
     NULL},
     {"BF_UPC_E", T_INT, offsetof(DynamsoftBarcodeReader, BF_UPC_E), 0,
     NULL},
     {"BF_INDUSTRIAL_25", T_INT, offsetof(DynamsoftBarcodeReader, BF_INDUSTRIAL_25), 0,
     NULL},
     {"BF_CODE_39_EXTENDED", T_INT, offsetof(DynamsoftBarcodeReader, BF_CODE_39_EXTENDED), 0,
     NULL},
     {"BF_GS1_DATABAR_OMNIDIRECTIONAL", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_OMNIDIRECTIONAL), 0,
     NULL},
     {"BF_GS1_DATABAR_TRUNCATED", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_TRUNCATED), 0,
     NULL},
     {"BF_GS1_DATABAR_STACKED", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_STACKED), 0,
     NULL},
     {"BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL), 0,
     NULL},
      {"BF_GS1_DATABAR_EXPANDED", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_EXPANDED), 0,
     NULL},
     {"BF_GS1_DATABAR_EXPANDED_STACKED", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_EXPANDED_STACKED), 0,
     NULL},
     {"BF_GS1_DATABAR_LIMITED", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_DATABAR_LIMITED), 0,
     NULL},
     {"BF_PATCHCODE", T_INT, offsetof(DynamsoftBarcodeReader, BF_PATCHCODE), 0,
     NULL},
     {"BF_USPSINTELLIGENTMAIL", T_INT, offsetof(DynamsoftBarcodeReader, BF_USPSINTELLIGENTMAIL), 0,
     NULL},
     {"BF_PLANET", T_INT, offsetof(DynamsoftBarcodeReader, BF_PLANET), 0,
     NULL},
     {"BF_AUSTRALIANPOST", T_INT, offsetof(DynamsoftBarcodeReader, BF_AUSTRALIANPOST), 0,
     NULL},
     {"BF_UKROYALMAIL", T_INT, offsetof(DynamsoftBarcodeReader, BF_UKROYALMAIL), 0,
     NULL},
     {"BF_PDF417", T_INT, offsetof(DynamsoftBarcodeReader, BF_PDF417), 0,
     NULL},
      {"BF_QR_CODE", T_INT, offsetof(DynamsoftBarcodeReader, BF_QR_CODE), 0,
     NULL},
     {"BF_DATAMATRIX", T_INT, offsetof(DynamsoftBarcodeReader, BF_DATAMATRIX), 0,
     NULL},
     {"BF_AZTEC", T_INT, offsetof(DynamsoftBarcodeReader, BF_AZTEC), 0,
     NULL},
     {"BF_MAXICODE", T_INT, offsetof(DynamsoftBarcodeReader, BF_MAXICODE), 0,
     NULL},
     {"BF_MICRO_QR", T_INT, offsetof(DynamsoftBarcodeReader, BF_MICRO_QR), 0,
     NULL},
     {"BF_MICRO_PDF417", T_INT, offsetof(DynamsoftBarcodeReader, BF_MICRO_PDF417), 0,
     NULL},
     {"BF_GS1_COMPOSITE", T_INT, offsetof(DynamsoftBarcodeReader, BF_GS1_COMPOSITE), 0,
     NULL},
     {"BF_NULL", T_INT, offsetof(DynamsoftBarcodeReader, BF_NULL), 0,
     NULL},
    {NULL} /* Sentinel */
};

static PyMethodDef dbr_methods[] = {
    {"initLicense", initLicense, METH_VARARGS, NULL},
    {"decodeFile", decodeFile, METH_VARARGS, NULL},
    {"decodeBuffer", decodeBuffer, METH_VARARGS, NULL},
    {"startVideoMode", startVideoMode, METH_VARARGS, NULL},
    {"stopVideoMode", stopVideoMode, METH_VARARGS, NULL},
    {"appendVideoFrame", appendVideoFrame, METH_VARARGS, NULL},
    {"initLicenseFromLicenseContent", initLicenseFromLicenseContent, METH_VARARGS, NULL},
    {"outputLicenseToString", outputLicenseToString, METH_VARARGS, NULL},
    {"initLicenseFromServer", initLicenseFromServer, METH_VARARGS, NULL},
    {"setFurtherModes", setFurtherModes, METH_VARARGS, NULL},
    {"setParameters", setParameters, METH_VARARGS, NULL},
    {"getParameters", getParameters, METH_VARARGS, NULL},
    {"decodeFileStream", decodeFileStream, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}};

static PyMethodDef module_methods[] =
    {
        {NULL}};

static int
DynamsoftBarcodeReader_clear(DynamsoftBarcodeReader *self)
{
    PyObject *tmp;

    tmp = self->COLOR_CLUTERING_MODE;
    self->COLOR_CLUTERING_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->COLOR_CONVERSION_MODE;
    self->COLOR_CONVERSION_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->GRAY_SCALE_TRANSFORMATION_MODE;
    self->GRAY_SCALE_TRANSFORMATION_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->REGION_PREDETECTION_MODE;
    self->REGION_PREDETECTION_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->IMAGE_PREPROCESSING_MODE;
    self->IMAGE_PREPROCESSING_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->TEXTURE_DETECTION_MODE;
    self->TEXTURE_DETECTION_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->TEXTURE_FILTER_MODE;
    self->TEXTURE_FILTER_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->TEXT_ASSISTED_CORRECTION_MODE;
    self->TEXT_ASSISTED_CORRECTION_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->DPM_CODE_READING_MODE;
    self->DPM_CODE_READING_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->DEFORMATION_RESISTING_MODE;
    self->DEFORMATION_RESISTING_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->BARCODE_COMPLEMENT_MODE;
    self->BARCODE_COMPLEMENT_MODE = NULL;
    Py_XDECREF(tmp);

    tmp = self->BARCODE_COLOR_MODE;
    self->BARCODE_COLOR_MODE = NULL;
    Py_XDECREF(tmp);

    DBR_DestroyInstance(self->hBarcode);

    return 0;
}

static void
DynamsoftBarcodeReader_dealloc(DynamsoftBarcodeReader *self)
{
#if defined(IS_PY3K)
    DynamsoftBarcodeReader_clear(self);
    Py_TYPE(self)->tp_free((PyObject *)self);
#else
    DynamsoftBarcodeReader_clear(self);
    self->ob_type->tp_free((PyObject *)self);
#endif
}

static PyObject *
DynamsoftBarcodeReader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    DynamsoftBarcodeReader *self;

    self = (DynamsoftBarcodeReader *)type->tp_alloc(type, 0);
    if (self != NULL)
    {
        self->hBarcode = DBR_CreateInstance();
        const char *versionInfo = DBR_GetVersion();
        printf("Dynamsoft Barcode Reader %s\n", versionInfo);
        if (!self->hBarcode)
        {
            printf("Cannot allocate memory!\n");
            return NULL;
        }

#ifdef IS_PY3K
        self->COLOR_CLUTERING_MODE = PyUnicode_FromString("colourClusteringModes");
        self->COLOR_CONVERSION_MODE = PyUnicode_FromString("colourConversionModes");
        self->GRAY_SCALE_TRANSFORMATION_MODE = PyUnicode_FromString("grayscaleTransformationModes");
        self->REGION_PREDETECTION_MODE = PyUnicode_FromString("regionPredetectionMode");
        self->IMAGE_PREPROCESSING_MODE = PyUnicode_FromString("imagePreprocessingModes");
        self->TEXTURE_DETECTION_MODE = PyUnicode_FromString("textureDetectionModes");
        self->TEXTURE_FILTER_MODE = PyUnicode_FromString("textFilterModes");
        self->TEXT_ASSISTED_CORRECTION_MODE = PyUnicode_FromString("textAssistedCorrectionMode ");
        self->DPM_CODE_READING_MODE = PyUnicode_FromString("dpmCodeReadingModes");
        self->DEFORMATION_RESISTING_MODE = PyUnicode_FromString("deformationResistingModes");
        self->BARCODE_COMPLEMENT_MODE = PyUnicode_FromString("barcodeComplementModes");
        self->BARCODE_COLOR_MODE = PyUnicode_FromString("barcodeColourModes");
#else
        self->COLOR_CLUTERING_MODE = PyString_FromString("colourClusteringModes");
        self->COLOR_CONVERSION_MODE = PyString_FromString("colourConversionModes");
        self->GRAY_SCALE_TRANSFORMATION_MODE = PyString_FromString("grayscaleTransformationModes");
        self->REGION_PREDETECTION_MODE = PyString_FromString("regionPredetectionMode");
        self->IMAGE_PREPROCESSING_MODE = PyString_FromString("imagePreprocessingModes");
        self->TEXTURE_DETECTION_MODE = PyString_FromString("textureDetectionModes");
        self->TEXTURE_FILTER_MODE = PyString_FromString("textFilterModes");
        self->TEXT_ASSISTED_CORRECTION_MODE = PyString_FromString("textAssistedCorrectionMode ");
        self->DPM_CODE_READING_MODE = PyString_FromString("dpmCodeReadingModes");
        self->DEFORMATION_RESISTING_MODE = PyString_FromString("deformationResistingModes");
        self->BARCODE_COMPLEMENT_MODE = PyString_FromString("barcodeComplementModes");
        self->BARCODE_COLOR_MODE = PyString_FromString("barcodeColourModes");
#endif
        self->GTM_INVERTED = 0x01;
        self->GTM_ORIGINAL = 0x02;
        self->GTM_SKIP = 0x00;
        // Barcode formats
        self->BF_ALL = BF_ALL;
        self->BF_ONED = BF_ONED;
        self->BF_GS1_DATABAR = BF_GS1_DATABAR;
        self->BF_POSTALCODE = BF_POSTALCODE;
        self->BF_CODE_39 = BF_CODE_39;
        self->BF_CODE_128 = BF_CODE_128;
        self->BF_CODE_93 = BF_CODE_93;
        self->BF_CODABAR = BF_CODABAR;
        self->BF_ITF = BF_ITF;
        self->BF_EAN_13 = BF_EAN_13;
        self->BF_EAN_8 = BF_EAN_8;
        self->BF_UPC_A = BF_UPC_A;
        self->BF_UPC_E = BF_UPC_E;
        self->BF_INDUSTRIAL_25 = BF_INDUSTRIAL_25;
        self->BF_CODE_39_EXTENDED = BF_CODE_39_EXTENDED;
        self->BF_GS1_DATABAR_OMNIDIRECTIONAL = BF_GS1_DATABAR_OMNIDIRECTIONAL;
        self->BF_GS1_DATABAR_TRUNCATED = BF_GS1_DATABAR_TRUNCATED;
        self->BF_GS1_DATABAR_STACKED = BF_GS1_DATABAR_STACKED;
        self->BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL = BF_GS1_DATABAR_STACKED_OMNIDIRECTIONAL;
        self->BF_GS1_DATABAR_EXPANDED = BF_GS1_DATABAR_EXPANDED;
        self->BF_GS1_DATABAR_EXPANDED_STACKED = BF_GS1_DATABAR_EXPANDED_STACKED;
        self->BF_GS1_DATABAR_LIMITED = BF_GS1_DATABAR_LIMITED;
        self->BF_PATCHCODE = BF_PATCHCODE;
        self->BF_USPSINTELLIGENTMAIL = BF_USPSINTELLIGENTMAIL;
        self->BF_POSTNET = BF_POSTNET;
        self->BF_PLANET = BF_PLANET;
        self->BF_AUSTRALIANPOST = BF_AUSTRALIANPOST;
        self->BF_UKROYALMAIL = BF_UKROYALMAIL;
        self->BF_PDF417 = BF_PDF417;
        self->BF_QR_CODE = BF_QR_CODE;
        self->BF_DATAMATRIX = BF_DATAMATRIX;
        self->BF_AZTEC = BF_AZTEC;
        self->BF_MAXICODE = BF_MAXICODE;
        self->BF_MICRO_QR = BF_MICRO_QR;
        self->BF_MICRO_PDF417 = BF_MICRO_PDF417;
        self->BF_GS1_COMPOSITE = BF_GS1_COMPOSITE;
        self->BF_NULL = BF_NULL;

        if (self->GRAY_SCALE_TRANSFORMATION_MODE == NULL)
        {
            Py_DECREF(self);
            return NULL;
        }
    }

    return (PyObject *)self;
}

static int
DynamsoftBarcodeReader_init(DynamsoftBarcodeReader *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyTypeObject DynamsoftBarcodeReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0) "dbr.DynamsoftBarcodeReader", /* tp_name */
    sizeof(DynamsoftBarcodeReader),                              /* tp_basicsize */
    0,                                                           /* tp_itemsize */
    (destructor)DynamsoftBarcodeReader_dealloc,                  /* tp_dealloc */
    0,                                                           /* tp_print */
    0,                                                           /* tp_getattr */
    0,                                                           /* tp_setattr */
    0,                                                           /* tp_reserved */
    0,                                                           /* tp_repr */
    0,                                                           /* tp_as_number */
    0,                                                           /* tp_as_sequence */
    0,                                                           /* tp_as_mapping */
    0,                                                           /* tp_hash  */
    0,                                                           /* tp_call */
    0,                                                           /* tp_str */
    0,                                                           /* tp_getattro */
    0,                                                           /* tp_setattro */
    0,                                                           /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,                    /*tp_flags*/
    "Dynamsoft Barcode Reader objects",                          /* tp_doc */
    0,                                                           /* tp_traverse */
    0,                                                           /* tp_clear */
    0,                                                           /* tp_richcompare */
    0,                                                           /* tp_weaklistoffset */
    0,                                                           /* tp_iter */
    0,                                                           /* tp_iternext */
    dbr_methods,                                                 /* tp_methods */
    dbr_members,                                                 /* tp_members */
    0,                                                           /* tp_getset */
    0,                                                           /* tp_base */
    0,                                                           /* tp_dict */
    0,                                                           /* tp_descr_get */
    0,                                                           /* tp_descr_set */
    0,                                                           /* tp_dictoffset */
    (initproc)DynamsoftBarcodeReader_init,                       /* tp_init */
    0,                                                           /* tp_alloc */
    DynamsoftBarcodeReader_new,                                  /* tp_new */
};

#if defined(IS_PY3K)
static int dbr_traverse(PyObject *m, visitproc visit, void *arg)
{
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int dbr_clear(PyObject *m)
{
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "dbr",
    "Extension with Dynamsoft Barcode Reader.",
    -1,
    NULL, NULL, NULL, NULL, NULL};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_dbr(void)

#else
#define INITERROR return
void initdbr(void)
#endif
{
    if (PyType_Ready(&DynamsoftBarcodeReaderType) < 0)
        INITERROR;

#if defined(IS_PY3K)
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("dbr", module_methods);
#endif
    if (module == NULL)
        INITERROR;

    Py_INCREF(&DynamsoftBarcodeReaderType);
    PyModule_AddObject(module, "DynamsoftBarcodeReader", (PyObject *)&DynamsoftBarcodeReaderType);
#if defined(IS_PY3K)
    return module;
#endif
}
