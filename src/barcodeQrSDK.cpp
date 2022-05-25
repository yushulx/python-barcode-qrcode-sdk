// Python includes
#include <Python.h>

// STD includes
#include <stdio.h>

#include "DynamsoftCommon.h"
#include "DynamsoftBarcodeReader.h"
#include "barcode_result.h"
#include <structmember.h>

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static PyObject *
error_out(PyObject *m)
{
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

#define DBR_NO_MEMORY 0
#define DBR_SUCCESS 1
#define DEBUG 0
// #define LOG_OFF

#ifdef LOG_OFF

#define printf(MESSAGE, __VA_ARGS__)

#endif

#define DEFAULT_MEMORY_SIZE 4096

typedef struct
{
    PyObject_HEAD
    // Barcode reader handler
    void *hBarcode;
    // Callback function for video mode
    PyObject *py_cb_textResult;
    PyObject *py_cb_intermediateResult;
    PyObject *py_cb_errorCode;
    PyObject *py_UserData;
    IntermediateResultArray * pInnerIntermediateResults;
} DynamsoftBarcodeReader;

static PyObject *initLicense(PyObject *obj, PyObject *args)
{
    char *pszLicense;
    if (!PyArg_ParseTuple(args, "s", &pszLicense))
    {
        return NULL;
    }

    char errorMsgBuffer[512];
	// Click https://www.dynamsoft.com/customer/license/trialLicense/?product=dbr to get a trial license.
	int ret = DBR_InitLicense(pszLicense, errorMsgBuffer, 512);
	printf("DBR_InitLicense: %s\n", errorMsgBuffer);

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
	PyObject *pyObject = NULL;
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
		BarcodeResult* result = PyObject_New(BarcodeResult, &BarcodeResultType);
		result->format = PyUnicode_FromString(pResults->results[i]->barcodeFormatString);
		result->text = PyUnicode_FromString(pResults->results[i]->barcodeText);
		result->x1 = Py_BuildValue("i", x1);
		result->y1 = Py_BuildValue("i", y1);
		result->x2 = Py_BuildValue("i", x2);
		result->y2 = Py_BuildValue("i", y2);
		result->x3 = Py_BuildValue("i", x3);
		result->y3 = Py_BuildValue("i", y3);
		result->x4 = Py_BuildValue("i", x4);
		result->y4 = Py_BuildValue("i", y4);

		// convert BarcodeResult to PyObject
		// pyObject = PyCapsule_New(result, NULL, NULL);
		// pyObject = PyObject_CallObject((PyObject*)&BarcodeResultType, result);
        PyList_SetItem(list, i, (PyObject *)result);

        // Print out PyObject if needed
        if (DEBUG)
        {
			PyObject *objectsRepresentation = PyObject_Repr(list);
            const char *s = PyUnicode_AsUTF8(objectsRepresentation);
            printf("Results: %s\n", s);
        }
    }

    // Release memory
    DBR_FreeTextResults(&pResults);

    return list;
}

static PyObject *decodeFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pFileName; // File name
    char *encoding = NULL;
    if (!PyArg_ParseTuple(args, "s|s", &pFileName, &encoding))
    {
        return NULL;
    }

    TextResultArray *pResults = NULL;

    // Barcode detection
    int ret = DBR_DecodeFile(self->hBarcode, pFileName, "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }
    DBR_GetAllTextResults(self->hBarcode, &pResults);

    // Wrap results
    PyObject *list = createPyResults(pResults, encoding);
    return list;
}

static PyMemberDef instance_members[] = {
    {NULL}
};

static PyMethodDef barcodeQrSDK_methods[] = {
  {"initLicense", initLicense, METH_VARARGS, "Set license to activate the SDK"},
  {NULL, NULL, 0, NULL}       
};

static PyMethodDef instance_methods[] = {
  {"decodeFile", decodeFile, METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}       
};

static int DynamsoftBarcodeReader_clear(DynamsoftBarcodeReader *self)
{
    if (self->hBarcode) Py_XDECREF(self->py_cb_errorCode);
    if (self->py_cb_intermediateResult) Py_XDECREF(self->py_cb_intermediateResult);
    if (self->py_cb_textResult) Py_XDECREF(self->py_cb_textResult);
    if (self->pInnerIntermediateResults) DBR_FreeIntermediateResults(&self->pInnerIntermediateResults);
    if(self->hBarcode) {
		DBR_DestroyInstance(self->hBarcode);
    	self->hBarcode = NULL;
	}
    return 0;
}

static void DynamsoftBarcodeReader_dealloc(DynamsoftBarcodeReader *self)
{
	DynamsoftBarcodeReader_clear(self);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *DynamsoftBarcodeReader_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    DynamsoftBarcodeReader *self;

    self = (DynamsoftBarcodeReader *)type->tp_alloc(type, 0);
    if (self != NULL)
    {
       	self->hBarcode = DBR_CreateInstance();
        self->pInnerIntermediateResults = NULL;
        self->py_cb_errorCode = NULL;
        self->py_cb_intermediateResult = NULL;
        self->py_cb_textResult = NULL;
    }

    return (PyObject *)self;
}

static int DynamsoftBarcodeReader_init(DynamsoftBarcodeReader *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyTypeObject DynamsoftBarcodeReaderType = {
    PyVarObject_HEAD_INIT(NULL, 0) "barcodeQrSDK.DynamsoftBarcodeReader", /* tp_name */
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
    "DynamsoftBarcodeReader",                          /* tp_doc */
    0,                                                           /* tp_traverse */
    0,                                                           /* tp_clear */
    0,                                                           /* tp_richcompare */
    0,                                                           /* tp_weaklistoffset */
    0,                                                           /* tp_iter */
    0,                                                           /* tp_iternext */
    instance_methods,                                                 /* tp_methods */
    instance_members,                                                 /* tp_members */
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

static struct PyModuleDef barcodeQrSDK_module_def = {
  PyModuleDef_HEAD_INIT,
  "barcodeQrSDK",
  "Internal \"barcodeQrSDK\" module",
  -1,
  barcodeQrSDK_methods
};

#define INITERROR return NULL

// https://docs.python.org/3/c-api/module.html
// https://docs.python.org/3/c-api/dict.html
PyMODINIT_FUNC PyInit_barcodeQrSDK(void)
{
  	if (PyType_Ready(&DynamsoftBarcodeReaderType) < 0)
        INITERROR;

	PyObject *module = PyModule_Create(&barcodeQrSDK_module_def);
    if (module == NULL)
        INITERROR;

    Py_INCREF(&DynamsoftBarcodeReaderType);
    PyModule_AddObject(module, "DynamsoftBarcodeReader", (PyObject *)&DynamsoftBarcodeReaderType);
	PyModule_AddStringConstant(module, "version", DBR_GetVersion());
    return module;
}
