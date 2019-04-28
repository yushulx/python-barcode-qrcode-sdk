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

// Barcode reader handler
void* hBarcode = NULL; 

/**
 * Create DBR instance
 */
static int createDBR() 
{
    if (!hBarcode) {
        hBarcode = DBR_CreateInstance();
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
    if (!createDBR()) 
    {
        return NULL;
    }

    char *pszLicense;
    if (!PyArg_ParseTuple(args, "s", &pszLicense)) {
        return NULL;
    }

	int ret = DBR_InitLicense(hBarcode, pszLicense);
    return Py_BuildValue("i", ret);
}

static PyObject *createPyResults(STextResultArray *paryResult)
{
    if (!paryResult)
    {
        printf("No barcode detected\n");
        return NULL;
    }
    // Get barcode results
    int count = paryResult->nResultsCount;

    // Create a Python object to store results
    PyObject* list = PyList_New(count); 
    // printf("count: %d\n", count);
    PyObject* result = NULL;
    int i = 0;
    for (; i < count; i++)
    {
        PyObject* pyObject = Py_BuildValue("ss", paryResult->ppResults[i]->pszBarcodeFormatString, paryResult->ppResults[i]->pszBarcodeText);
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

    if (!createDBR()) 
    {
        return NULL;
    }

    char *pFileName; // File name
    int iFormat;     // Barcode formats
    if (!PyArg_ParseTuple(args, "si", &pFileName, &iFormat)) {
        return NULL;
    }

    // Update DBR params
	PublicParameterSettings pSettings = {0};
	DBR_GetTemplateSettings(hBarcode, "", &pSettings);
	pSettings.mBarcodeFormatIds = iFormat;
	char szErrorMsgBuffer[256];
	DBR_SetTemplateSettings(hBarcode, "", &pSettings, szErrorMsgBuffer, 256);

    STextResultArray *paryResult = NULL;

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
    if (!createDBR()) 
    {
        return NULL;
    }

    PyObject *o;
    int iFormat;
    if (!PyArg_ParseTuple(args, "Oi", &o, &iFormat))
        return NULL;

    // Update DBR params
	PublicParameterSettings pSettings = {0};
	DBR_GetTemplateSettings(hBarcode, "", &pSettings);
	pSettings.mBarcodeFormatIds = iFormat;
	char szErrorMsgBuffer[256];
	DBR_SetTemplateSettings(hBarcode, "", &pSettings, szErrorMsgBuffer, 256);
    
    #if defined(IS_PY3K)
    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL) {
        PyErr_Clear();
        return -1;
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
    STextResultArray *paryResult = NULL;

    // Detect barcodes
    ImagePixelFormat format = IPF_RGB_888;

    if (width == stride) 
    {
        format = IPF_GrayScaled;
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

static PyMethodDef dbr_methods[] =
{
    {"create", create, METH_VARARGS, NULL},
    {"destroy", destroy, METH_VARARGS, NULL},
    {"initLicense", initLicense, METH_VARARGS, NULL},
    {"decodeFile", decodeFile, METH_VARARGS, NULL},
    {"decodeBuffer", decodeBuffer, METH_VARARGS, NULL},
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