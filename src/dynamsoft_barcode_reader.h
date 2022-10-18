#ifndef __BARCODE_READER_H__
#define __BARCODE_READER_H__

#include <Python.h>
#include <structmember.h>
#include "DynamsoftCommon.h"
#include "DynamsoftBarcodeReader.h"
#include "barcode_result.h"
#include <thread>
#include <condition_variable>
#include <mutex>
#include <queue>
#include <functional>

#define DEBUG 0

class Task
{
public:
    std::function<void()> func;
    unsigned char* buffer;
};

class WorkerThread
{
public:
    std::mutex m;
    std::condition_variable cv;
    std::queue<Task> tasks = {};
    volatile bool running;
	std::thread t;
};

typedef struct
{
    PyObject_HEAD
    // Barcode reader handler
    void *hBarcode;
    // Callback function for video mode
    PyObject *py_cb_textResult;
    // Callback function for image mode
    PyObject *callback;
    // Worker thread
    WorkerThread *worker;
} DynamsoftBarcodeReader;

void clearTasks(DynamsoftBarcodeReader *self)
{
    if (self->worker->tasks.size() > 0)
    {
        for (int i = 0; i < self->worker->tasks.size(); i++)
        {
            free(self->worker->tasks.front().buffer);
            self->worker->tasks.pop();
        }
    }
}

void clear(DynamsoftBarcodeReader *self)
{
    if (self->callback)
    {
        Py_XDECREF(self->callback);
        self->callback = NULL;
    }

    if (self->py_cb_textResult) 
    {
        Py_XDECREF(self->py_cb_textResult);
        self->py_cb_textResult = NULL;
    }

    if (self->worker)
    {
        std::unique_lock<std::mutex> lk(self->worker->m);
        self->worker->running = false;
        
        clearTasks(self);

        self->worker->cv.notify_one();
        lk.unlock();

        self->worker->t.join();
        delete self->worker;
        self->worker = NULL;
        printf("Quit native thread.\n");
    }
}

static int DynamsoftBarcodeReader_clear(DynamsoftBarcodeReader *self)
{
    clear(self);
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
        self->py_cb_textResult = NULL;
        self->callback = NULL;
        self->worker = NULL;
    }

    return (PyObject *)self;
}

PyObject *createPyList(TextResultArray *pResults)
{
    // Get barcode results
    int count = pResults->resultsCount;

    // Create a Python object to store results
    PyObject *list = PyList_New(count);
    for (int i = 0; i < count; i++)
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

        PyList_SetItem(list, i, (PyObject *)result);

        // Print out PyObject if needed
        if (DEBUG)
        {
			PyObject *objectsRepresentation = PyObject_Repr(list);
            const char *s = PyUnicode_AsUTF8(objectsRepresentation);
            printf("Results: %s\n", s);
        }
    }

    return list;
}

static PyObject *createPyResults(DynamsoftBarcodeReader *self)
{
    TextResultArray *pResults = NULL;
    DBR_GetAllTextResults(self->hBarcode, &pResults);

    if (!pResults)
    {
        printf("No barcode detected\n");
        return NULL;
    }

    PyObject *list = createPyList(pResults);

    // Release memory
    DBR_FreeTextResults(&pResults);

    return list;
}


/**
 * Decode barcode and QR code from image files. 
 * 
 * @param file name
 * 
 * @return BarcodeResult list
 */
static PyObject *decodeFile(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *pFileName; // File name
    if (!PyArg_ParseTuple(args, "s", &pFileName))
    {
        return NULL;
    }

    // Barcode detection
    int ret = DBR_DecodeFile(self->hBarcode, pFileName, "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }

    PyObject *list = createPyResults(self);
    return list;
}

/**
 * Decode barcode and QR code from OpenCV Mat. 
 * 
 * @param Mat image
 * 
 * @return BarcodeResult list
 */
static PyObject *decodeMat(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *o;
    if (!PyArg_ParseTuple(args, "O", &o))
        return NULL;

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

    int ret = DBR_DecodeBuffer(self->hBarcode, (const unsigned char*)buffer, width, height, stride, format, "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }


    PyObject *list = createPyResults(self);

    Py_DECREF(memoryview);

    return list;
}

void onResultReady(DynamsoftBarcodeReader *self)
{
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();
    PyObject *list = createPyResults(self);
    PyObject *result = PyObject_CallFunction(self->callback, "O", list);
    if (result != NULL)
        Py_DECREF(result);

    PyGILState_Release(gstate);
}

void scan(DynamsoftBarcodeReader *self, unsigned char *buffer, int width, int height, int stride, ImagePixelFormat format, int len)
{
    int ret = DBR_DecodeBuffer(self->hBarcode, (const unsigned char*)buffer, width, height, stride, format, "");
    if (ret)
    {
        printf("Detection error: %s\n", DBR_GetErrorString(ret));
    }

    free(buffer);

    if (self->callback != NULL)
    {
        onResultReady(self);
    }
}

void queueTask(DynamsoftBarcodeReader *self, unsigned char* barcodeBuffer, int width, int height, int stride, int imageformat, int len)
{
    ImagePixelFormat format = IPF_RGB_888;

    if (imageformat == 0)
    {
        format = IPF_GRAYSCALED;
    }
    else
    {
        format = IPF_RGB_888;
    }
    
    unsigned char *data = (unsigned char *)malloc(len);
    memcpy(data, barcodeBuffer, len);

    std::unique_lock<std::mutex> lk(self->worker->m);
    clearTasks(self);
    std::function<void()> task_function = std::bind(scan, self, data, width, height, stride, format, len);
    Task task;
    task.func = task_function;
    task.buffer = data;
    self->worker->tasks.push(task);
    self->worker->cv.notify_one();
    lk.unlock();
}

/**
 * Decode barcode and QR code from OpenCV Mat asynchronously.
 *
 * @param Mat image
 *
 */
static PyObject *decodeMatAsync(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    if (self->worker == NULL)
    {
        return Py_BuildValue("i", -1);
    }
    PyObject *o;
    if (!PyArg_ParseTuple(args, "O", &o))
        return Py_BuildValue("i", -1);

    Py_buffer *view;
    int nd;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
        return Py_BuildValue("i", -1);
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    char *buffer = (char *)view->buf;
    nd = view->ndim;
    int len = view->len;
    int stride = view->strides[0];
    int width = view->strides[0] / view->strides[1];
    int height = len / stride;

    queueTask(self, (unsigned char*)buffer, width, height, stride, nd, len);
    
    Py_DECREF(memoryview);
    return Py_BuildValue("i", 0);
}

/**
 * Decode barcode and QR code from byte array asynchronously.
 *
 * @param bytes, width, height, stride, imageformat
 *
 */
static PyObject *decodeBytesAsync(PyObject * obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;  
    if (self->worker == NULL)
    {
        return Py_BuildValue("i", -1);
    }

    PyObject *o;
    int len, width, height, stride, imageformat;
    if (!PyArg_ParseTuple(args, "Oiiiii", &o, &len, &width, &height, &stride, &imageformat))
		return Py_BuildValue("i", -1);

    char * barcodeBuffer = NULL;
    if(PyByteArray_Check(o))
    {
        barcodeBuffer = PyByteArray_AsString(o);
    }
    else if(PyBytes_Check(o))
    {
        barcodeBuffer = PyBytes_AsString(o);
    }
    else
    {
        printf("The first parameter should be a byte array or bytes object.");
		return Py_BuildValue("i", -1);
    }
    
    queueTask(self, (unsigned char*)barcodeBuffer, width, height, stride, imageformat, len);

    return Py_BuildValue("i", 0);
}

void run(DynamsoftBarcodeReader *self)
{
    while (self->worker->running)
    {
        std::function<void()> task;
        std::unique_lock<std::mutex> lk(self->worker->m);
        self->worker->cv.wait(lk, [&]
                              { return !self->worker->tasks.empty() || !self->worker->running; });
        if (!self->worker->running)
		{
			break;
		}
        task = std::move(self->worker->tasks.front().func);
        self->worker->tasks.pop();
        lk.unlock();

        task();
    }
}

/**
 * Register callback function to receive barcode decoding result asynchronously.
 */
static PyObject *addAsyncListener(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *callback = NULL;
    if (!PyArg_ParseTuple(args, "O", &callback))
    {
        return NULL;
    }

    if (!PyCallable_Check(callback))
    {
        PyErr_SetString(PyExc_TypeError, "parameter must be callable");
        return NULL;
    }
    else
    {
        Py_XINCREF(callback);       /* Add a reference to new callback */
        Py_XDECREF(self->callback); /* Dispose of previous callback */
        self->callback = callback;
    }

    if (self->worker == NULL)
    {
        self->worker = new WorkerThread();
        self->worker->running = true;
        self->worker->t = std::thread(&run, self);
    }

    printf("Running native thread...\n");
    return Py_BuildValue("i", 0);
}

/**
 * Clear native thread and tasks.
 */
static PyObject *clearAsyncListener(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;
    clear(self);
    return Py_BuildValue("i", 0);
}

/**
 * Get runtime settings.
 *
 * @return Return stringified JSON object.
 */
static PyObject *getParameters(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char * pContent = NULL;

    int ret = DBR_OutputSettingsToStringPtr(self->hBarcode, &pContent, "CurrentRuntimeSettings");
    PyObject * content = Py_BuildValue("s", pContent);
    DBR_FreeSettingsString(&pContent);

    return content;
}

/**
 * Set runtime settings with JSON object.
 *
 * @param json string: the stringified JSON object.
 * 
 * @return Return 0 if the function operates successfully.
 */
static PyObject *setParameters(PyObject *obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    char *json;
    if (!PyArg_ParseTuple(args, "s", &json))
    {
        Py_RETURN_NONE;
    }

    char errorMessage[512];
    int ret = DBR_InitRuntimeSettingsWithString(self->hBarcode, json, CM_OVERWRITE, errorMessage, 256);
    if (ret) 
    {
        printf("Returned value: %d, error message: %s\n", ret, errorMessage);
        PyErr_SetString(PyExc_TypeError, "DBR_InitRuntimeSettingsWithString() failed");
    }
    return Py_BuildValue("i", ret);
}

static PyObject *decodeBytes(PyObject * obj, PyObject *args)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;  

    PyObject *o;
    int width, height, stride, imageformat;
    if (!PyArg_ParseTuple(args, "Oiiii", &o, &width, &height, &stride, &imageformat))
		Py_RETURN_NONE;

    char * barcodeBuffer = NULL;
    if(PyByteArray_Check(o))
    {
        barcodeBuffer = PyByteArray_AsString(o);
    }
    else if(PyBytes_Check(o))
    {
        barcodeBuffer = PyBytes_AsString(o);
    }
    else
    {
        printf("The first parameter should be a byte array or bytes object.");
		Py_RETURN_NONE;
    }
    
    ImagePixelFormat format = IPF_RGB_888;

    if (imageformat == 0)
    {
        format = IPF_GRAYSCALED;
    }
    else
    {
        format = IPF_RGB_888;
    }
    
    int ret = DBR_DecodeBuffer(self->hBarcode, (const unsigned char*)barcodeBuffer, width, height, stride, format, "");
    PyObject *list = createPyResults(self);

    return list;
}

void onResultCallback(int frameId, TextResultArray *pResults, void *pUser)
{
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)pUser;

    // https://docs.python.org/2/c-api/init.html
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *list = createPyList(pResults);

    PyObject *result = PyObject_CallFunction(self->py_cb_textResult, "O", list);
    if (result != NULL)
    	Py_DECREF(result);

    PyGILState_Release(gstate);
    /////////////////////////////////////////////

    // Release memory
    DBR_FreeTextResults(&pResults);
}

/**
 * Read barcode and QR code from continuous video frames
 */
static PyObject *startVideoMode(PyObject *obj, PyObject *args)
{
    printf("Start the video mode\n");
    DynamsoftBarcodeReader *self = (DynamsoftBarcodeReader *)obj;

    PyObject *callback = NULL;
    int maxListLength, maxResultListLength, width, height, imageformat, iFormat, stride;
    if (!PyArg_ParseTuple(args, "iiiiiO", &maxListLength, &maxResultListLength, &width, &height, &imageformat, &callback))
    {
        return NULL;
    }

    if (!PyCallable_Check(callback))
    {
        PyErr_SetString(PyExc_TypeError, "parameter must be callable");
        return NULL;
    }
    else
    {
        Py_XINCREF(callback);    /* Add a reference to new callback */
        Py_XDECREF(self->py_cb_textResult); /* Dispose of previous callback */
        self->py_cb_textResult = callback;
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

static PyObject *stopVideoMode(PyObject *obj, PyObject *args)
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

    //Refer to numpy/core/src/multiarray/ctors.c
    Py_buffer *view;
    PyObject *memoryview = PyMemoryView_FromObject(o);
    if (memoryview == NULL)
    {
        PyErr_Clear();
        return NULL;
    }

    view = PyMemoryView_GET_BUFFER(memoryview);
    unsigned char *buffer = (unsigned char *)view->buf;
    DBR_AppendFrame(self->hBarcode, buffer);
    Py_DECREF(memoryview);

    return 0;
}

static PyMethodDef instance_methods[] = {
  {"decodeFile", decodeFile, METH_VARARGS, NULL},
  {"decodeMat", decodeMat, METH_VARARGS, NULL},
  {"setParameters", setParameters, METH_VARARGS, NULL},
  {"getParameters", getParameters, METH_VARARGS, NULL},
  {"startVideoMode", startVideoMode, METH_VARARGS, NULL},
  {"stopVideoMode", stopVideoMode, METH_VARARGS, NULL},
  {"appendVideoFrame", appendVideoFrame, METH_VARARGS, NULL},
  {"decodeBytes", decodeBytes, METH_VARARGS, NULL},
  {"addAsyncListener", addAsyncListener, METH_VARARGS, NULL},
  {"decodeMatAsync", decodeMatAsync, METH_VARARGS, NULL},
  {"clearAsyncListener", clearAsyncListener, METH_VARARGS, NULL},
  {"decodeBytesAsync", decodeBytesAsync, METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}       
};

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
    PyObject_GenericGetAttr,                                                           /* tp_getattro */
    PyObject_GenericSetAttr,                                                           /* tp_setattro */
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
    0,                                                 /* tp_members */
    0,                                                           /* tp_getset */
    0,                                                           /* tp_base */
    0,                                                           /* tp_dict */
    0,                                                           /* tp_descr_get */
    0,                                                           /* tp_descr_set */
    0,                                                           /* tp_dictoffset */
    0,                       /* tp_init */
    0,                                                           /* tp_alloc */
    DynamsoftBarcodeReader_new,                                  /* tp_new */
};

#endif
