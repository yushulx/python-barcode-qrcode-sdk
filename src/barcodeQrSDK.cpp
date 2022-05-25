// Python includes
#include <Python.h>

// STD includes
#include <stdio.h>

#include "dynamsoft_barcode_reader.h"

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
  {NULL, NULL, 0, NULL}       
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
