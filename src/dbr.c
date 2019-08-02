#include <Python.h>
#include "DynamsoftBarcodeReader.h"
#include <ndarraytypes.h>

#ifndef DEBUG
#define DEBUG 0
#endif

#if PY_MAJOR_VERSION >= 3
#ifndef IS_PY3K
#define IS_PY3K 1
#endif
#endif

struct module_state {
    PyObject *error;
};

#if defined(IS_PY3K)
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject *
error_out(PyObject *m) {
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

#define DBR_NO_MEMORY 0
#define DBR_SUCCESS   1

// #define LOG_OFF

#ifdef LOG_OFF

    #define printf(MESSAGE, __VA_ARGS__)

#endif

#define CHECK_DBR() {if (!createDBR()) {return NULL;}}

// Barcode reader handler
static void* hBarcode = NULL; 
static PyObject *py_callback = NULL;

/**
 * Create DBR instance
 */
static int createDBR() 
{
    if (!hBarcode) {
        hBarcode = DBR_CreateInstance();
        const char* versionInfo = DBR_GetVersion();
        printf("Dynamsoft Barcode Reader %s\n", versionInfo);
        if (!hBarcode)
        {
            printf("Cannot allocate memory!\n");
            return DBR_NO_MEMORY;
        }
    }

    return DBR_SUCCESS;
}

/**
 * Destroy DBR instance
 */
static void destroyDBR()
{
    if (hBarcode) {
        DBR_DestroyInstance(hBarcode);
    }
}

static PyObject *
create(PyObject *self, PyObject *args)
{
    int ret = createDBR();
    return Py_BuildValue("i", ret);
}

static PyObject *
destroy(PyObject *self, PyObject *args)
{
    destroyDBR();
    return Py_BuildValue("i", 0);
}

/**
 * Set Dynamsoft Barcode Reader license.  
 * To get valid license, please contact support@dynamsoft.com
 * Invalid license is acceptable. With an invalid license, SDK will return an imcomplete result.
 */
static PyObject *
initLicense(PyObject *self, PyObject *args)
{
    CHECK_DBR();

    char *pszLicense;
    if (!PyArg_ParseTuple(args, "s", &pszLicense)) {
        return NULL;
    }

	int ret = DBR_InitLicense(hBarcode, pszLicense);
    return Py_BuildValue("i", ret);
}

static PyObject *createPyResults(TextResultArray *paryResult)
{
    if (!paryResult)
    {
        printf("No barcode detected\n");
        return NULL;
    }
    // Get barcode results
    int count = paryResult->resultsCount;

    // Create a Python object to store results
    PyObject* list = PyList_New(count); 
    // printf("count: %d\n", count);
    PyObject* result = NULL;
    int i = 0;
    for (; i < count; i++)
    {
        LocalizationResult* pLocalizationResult = paryResult->results[i]->localizationResult;
        int x1 = pLocalizationResult->x1;
        int y1 = pLocalizationResult->y1;
        int x2 = pLocalizationResult->x2;
        int y2 = pLocalizationResult->y2;
        int x3 = pLocalizationResult->x3;
        int y3 = pLocalizationResult->y3;
        int x4 = pLocalizationResult->x4;
        int y4 = pLocalizationResult->y4;

        PyObject* pyObject = Py_BuildValue("ssiiiiiiii", paryResult->results[i]->barcodeFormatString, paryResult->results[i]->barcodeText
        , x1, y1, x2, y2, x3, y3, x4, y4);
        PyList_SetItem(list, i, pyObject); // Add results to list

        // Print out PyObject if needed
        if (DEBUG)
        {
            #if defined(IS_PY3K)
                PyObject* objectsRepresentation = PyObject_Repr(list);
                const char* s = PyUnicode_AsUTF8(objectsRepresentation);
                printf("Results: %s\n", s);
            #else
                PyObject* objectsRepresentation = PyObject_Repr(list);
                const char* s = PyString_AsString(objectsRepresentation);
                printf("Results: %s\n", s);
            #endif
        }
    }

    // Release memory
    DBR_FreeTextResults(&paryResult);

    return list;
}

void updateFormat(int format)
{
    // Update DBR params
	PublicRuntimeSettings pSettings = {0};
	DBR_GetRuntimeSettings(hBarcode, &pSettings);
	pSettings.barcodeFormatIds = format;
    char szErrorMsgBuffer[256];
	DBR_UpdateRuntimeSettings(hBarcode, &pSettings, szErrorMsgBuffer, 256);
}

/**
 * Decode barcode from a file 
 */
static PyObject *
decodeFile(PyObject *self, PyObject *args)
{
    #if defined(_WIN32)
    printf("Windows\n");
    #elif defined(__linux__)
    printf("Linux\n");
    #elif defined(__APPLE__)
    printf("MacOS\n");
    #else
    printf("Unknown Operating System.\n");
    #endif

    CHECK_DBR();

    char *pFileName; // File name
    int iFormat;     // Barcode formats
    if (!PyArg_ParseTuple(args, "si", &pFileName, &iFormat)) {
        return NULL;
    }

	updateFormat(iFormat);

    TextResultArray *paryResult = NULL;

    // Barcode detection
    int ret = DBR_DecodeFile(hBarcode, pFileName, "");
    if (ret) 
	{
		printf("Detection error: %s\n", DBR_GetErrorString(ret));
	}
    DBR_GetAllTextResults(hBarcode, &paryResult);

    // Wrap results
    PyObject *list = createPyResults(paryResult);
    return list;
}

/**
 * Decode barcode from an image buffer. 
 */
static PyObject *
decodeBuffer(PyObject *self, PyObject *args)
{
    CHECK_DBR();

    PyObject *o;
    int iFormat;
    if (!PyArg_ParseTuple(args, "Oi", &o, &iFormat))
        return NULL;

    updateFormat(iFormat);
    
    #if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL) {
        PyErr_Clear();
        return NULL;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    char *buffer = (char*)view->buf;
    nd = view->ndim;
    int len = view->len;
    int stride = view->strides[0];
    int width = view->strides[0] / view->strides[1];
    int height = len / stride;
    #else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao)) {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        return NULL;
    }

    PyArrayInterface *pai = (PyArrayInterface*)PyCObject_AsVoidPtr(ao);
    
    if (pai->two != 2) {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
        return NULL;
    }

    // Get image information
    char *buffer = (char*)pai->data; // The address of image data
    int width = (int)pai->shape[1];       // image width
    int height = (int)pai->shape[0];      // image height
    int stride = (int)pai->strides[0]; // image stride
    #endif

    // Initialize Dynamsoft Barcode Reader
    TextResultArray *paryResult = NULL;

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

    PyObject *list = NULL;
    int ret = DBR_DecodeBuffer(hBarcode, buffer, width, height, stride, format, "");
    if (ret) 
	{
		printf("Detection error: %s\n", DBR_GetErrorString(ret));
	}
    // Wrap results
    DBR_GetAllTextResults(hBarcode, &paryResult);
    list = createPyResults(paryResult);
    
    #if defined(IS_PY3K)
    Py_DECREF(memoryview);
    #else
    Py_DECREF(ao);
    #endif

    return list;
}

void onResultCallback(int frameId, TextResultArray *pResults, void * pUser)
{
    // Get barcode results
    int count = pResults->resultsCount;
    int i = 0;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    for (; i < count; i++)
    {
        // https://docs.python.org/2.5/ext/callingPython.html
        PyObject *result = PyObject_CallFunction(py_callback, "ss", pResults->results[i]->barcodeFormatString, pResults->results[i]->barcodeText);
        if (result == NULL) return NULL;
        Py_DECREF(result);
    }

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeTextResults(&pResults);
}

/**
 * Read barcodes from continuous video frames
 */
static PyObject *
startVideoMode(PyObject *self, PyObject *args)
{
    printf("Start the video mode\n");
    CHECK_DBR();

    PyObject *callback = NULL;
    int maxListLength, maxResultListLength, width, height, imageformat, iFormat, stride; 
    if (!PyArg_ParseTuple(args, "iiiiiiO", &maxListLength, &maxResultListLength, &width, &height, &imageformat, &iFormat, &callback)) {
        return NULL;
    }

    updateFormat(iFormat);

    if (!PyCallable_Check(callback)) 
    {
        PyErr_SetString(PyExc_TypeError, "parameter must be callable");
        return NULL;
    }
    else
    {
        Py_XINCREF(callback);         /* Add a reference to new callback */
        Py_XDECREF(py_callback);      /* Dispose of previous callback */
        py_callback = callback;     
    }

    ImagePixelFormat format = IPF_RGB_888;

    if (imageformat == 0)
    {
        stride = width;
        format = IPF_GRAYSCALED;
    }
    else {
        stride = width * 3;
        format = IPF_RGB_888;
    }

    DBR_SetTextResultCallback(hBarcode, onResultCallback, NULL);

    int ret = DBR_StartFrameDecoding(hBarcode, maxListLength, maxResultListLength, width, height, stride, format, "");
    return Py_BuildValue("i", ret);
}

static PyObject *
stopVideoMode(PyObject *self, PyObject *args)
{
    printf("Stop the video mode\n");
    if (hBarcode) 
    {
        int ret = DBR_StopFrameDecoding(hBarcode);
        return Py_BuildValue("i", ret);
    }

    return 0;
}

static PyObject *
appendVideoFrame(PyObject *self, PyObject *args)
{
    CHECK_DBR();

    PyObject *o;
    if (!PyArg_ParseTuple(args, "O", &o))
        return NULL;
    
    #if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL) {
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
    #else

    PyObject *ao = PyObject_GetAttrString(o, "__array_struct__");

    if ((ao == NULL) || !PyCObject_Check(ao)) {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        return NULL;
    }

    PyArrayInterface *pai = (PyArrayInterface*)PyCObject_AsVoidPtr(ao);
    
    if (pai->two != 2) {
        PyErr_SetString(PyExc_TypeError, "object does not have array interface");
        Py_DECREF(ao);
        return NULL;
    }

    // Get image information
    unsigned char *buffer = (unsigned char *)pai->data; // The address of image data
    int width = (int)pai->shape[1];       // image width
    int height = (int)pai->shape[0];      // image height
    int stride = (int)pai->strides[0]; // image stride
    #endif

    // Initialize Dynamsoft Barcode Reader
    TextResultArray *paryResult = NULL;

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

    int frameId = DBR_AppendFrame(hBarcode, buffer);
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
initLicenseFromLicenseContent(PyObject *self, PyObject *args)
{
    if (!createDBR()) 
    {
        return NULL;
    }

    char *pszLicenseKey; 
    char* pszLicenseContent;
    if (!PyArg_ParseTuple(args, "ss", &pszLicenseKey, &pszLicenseContent)) {
        return NULL;
    }

    int ret = DBR_InitLicenseFromLicenseContent(hBarcode, pszLicenseKey, pszLicenseContent);
    return Py_BuildValue("i", ret);
}

/**
 * Outputs the license content as an encrypted string from the license server to be used for offline license verification.
 *
 *
 * @return if successful, return encypted string. Otherwise return error code. 
 */
static PyObject *
outputLicenseToString(PyObject *self, PyObject *args)
{
    if (!createDBR()) 
    {
        return NULL;
    }

    char content[512];
    int ret = DBR_OutputLicenseToString(hBarcode, content, 512);
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
initLicenseFromServer(PyObject *self, PyObject *args)
{
    if (!createDBR()) 
    {
        return NULL;
    }

    char *pszLicenseKey, *pLicenseServer;
    if (!PyArg_ParseTuple(args, "ss", &pLicenseServer, &pszLicenseKey)) {
        return NULL;
    }

    int ret = DBR_InitLicenseFromServer(hBarcode, pLicenseServer, pszLicenseKey);
    return Py_BuildValue("i", ret);
}

static PyMethodDef dbr_methods[] =
{
    {"create", create, METH_VARARGS, NULL},
    {"destroy", destroy, METH_VARARGS, NULL},
    {"initLicense", initLicense, METH_VARARGS, NULL},
    {"decodeFile", decodeFile, METH_VARARGS, NULL},
    {"decodeBuffer", decodeBuffer, METH_VARARGS, NULL},
    {"startVideoMode", startVideoMode, METH_VARARGS, NULL},
    {"stopVideoMode", stopVideoMode, METH_VARARGS, NULL},
    {"appendVideoFrame", appendVideoFrame, METH_VARARGS, NULL},
    {"initLicenseFromLicenseContent", initLicenseFromLicenseContent, METH_VARARGS, NULL},
    {"outputLicenseToString", outputLicenseToString, METH_VARARGS, NULL},
    {"initLicenseFromServer", initLicenseFromServer, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

#if defined(IS_PY3K)

static int dbr_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int dbr_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "dbr",
    NULL,
    sizeof(struct module_state),
    dbr_methods,
    NULL,
    dbr_traverse,
    dbr_clear,
    NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_dbr(void)

#else
#define INITERROR return
void
initdbr(void)
#endif
{
#if defined(IS_PY3K)
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("dbr", dbr_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("dbr.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if defined(IS_PY3K)
    return module;
#endif
}