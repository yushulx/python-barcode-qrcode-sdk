// Python includes
#include <Python.h>

// STD includes
#include <stdio.h>

#include "dynamsoft_barcode_reader.h"

#define INITERROR return NULL

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

// #define LOG_OFF

#ifdef LOG_OFF

#define printf(MESSAGE, __VA_ARGS__)

#endif

#define DEFAULT_MEMORY_SIZE 4096

static PyObject *createInstance(PyObject *obj, PyObject *args)
{
    if (PyType_Ready(&DynamsoftBarcodeReaderType) < 0)
         INITERROR;


    DynamsoftBarcodeReader* reader = PyObject_New(DynamsoftBarcodeReader, &DynamsoftBarcodeReaderType);
    reader->hBarcode = DBR_CreateInstance();
    reader->py_cb_textResult = NULL;

    return (PyObject *)reader;
}

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

static PyMethodDef barcodeQrSDK_methods[] = {
  {"initLicense", initLicense, METH_VARARGS, "Set license to activate the SDK"},
  {"createInstance", createInstance, METH_VARARGS, "Create Dynamsoft Barcode Reader object"},
  {NULL, NULL, 0, NULL}       
};

static struct PyModuleDef barcodeQrSDK_module_def = {
  PyModuleDef_HEAD_INIT,
  "barcodeQrSDK",
  "Internal \"barcodeQrSDK\" module",
  -1,
  barcodeQrSDK_methods
};

// https://docs.python.org/3/c-api/module.html
// https://docs.python.org/3/c-api/dict.html
PyMODINIT_FUNC PyInit_barcodeQrSDK(void)
{
	PyObject *module = PyModule_Create(&barcodeQrSDK_module_def);
    if (module == NULL)
        INITERROR;

    
    if (PyType_Ready(&DynamsoftBarcodeReaderType) < 0)
       INITERROR;

    Py_INCREF(&DynamsoftBarcodeReaderType);
    PyModule_AddObject(module, "DynamsoftBarcodeReader", (PyObject *)&DynamsoftBarcodeReaderType);
    
    if (PyType_Ready(&BarcodeResultType) < 0)
       INITERROR;

    Py_INCREF(&BarcodeResultType);
    PyModule_AddObject(module, "BarcodeResult", (PyObject *)&BarcodeResultType);

	PyModule_AddStringConstant(module, "version", DBR_GetVersion());
    return module;
}

