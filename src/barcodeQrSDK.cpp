// Python includes
#include <Python.h>

// STD includes
#include <stdio.h>

#include "DynamsoftCommon.h"
#include "DynamsoftBarcodeReader.h"


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

//-----------------------------------------------------------------------------
static PyMethodDef barcodeQrSDK_methods[] = {
  {"initLicense", initLicense, METH_VARARGS, "Set license to activate the SDK"},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};

//-----------------------------------------------------------------------------
#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC init_barcodeQrSDK(void)
{
  (void) Py_InitModule("barcodeQrSDK", device_methods);
}
#else /* PY_MAJOR_VERSION >= 3 */
static struct PyModuleDef barcodeQrSDK_module_def = {
  PyModuleDef_HEAD_INIT,
  "barcodeQrSDK",
  "Internal \"barcodeQrSDK\" module",
  -1,
  barcodeQrSDK_methods
};

PyMODINIT_FUNC PyInit_barcodeQrSDK(void)
{
  return PyModule_Create(&barcodeQrSDK_module_def);
}
#endif /* PY_MAJOR_VERSION >= 3 */
