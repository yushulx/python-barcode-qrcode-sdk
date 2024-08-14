#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "bridge.h"
#include <thread>

using namespace std;

callback_t callback = NULL;
thread t;

ResultList *dbr_get_results(void *barcodeReader)
{
    TextResultArray *pResults;
    int ret = DBR_GetAllTextResults(barcodeReader, &pResults);
    int count = pResults->resultsCount;
    TextResult **results = pResults->results;

    ResultInfo **pResultInfo = (ResultInfo **)malloc(sizeof(ResultInfo *) * count);
    ResultList *resultList = (ResultList *)malloc(sizeof(ResultList));
    resultList->size = count;
    resultList->pResultInfo = pResultInfo;

    for (int i = 0; i < count; i++)
    {
        TextResult *pResult = results[i];
        ResultInfo *pInfo = (ResultInfo *)malloc(sizeof(ResultInfo));
        pInfo->format = NULL;
        pInfo->text = NULL;
        pResultInfo[i] = pInfo;
        // printf("Barcode format: %s, text: %s\n", pResult->barcodeFormatString, pResult->barcodeText);
        pInfo->format = (char *)calloc(strlen(pResult->barcodeFormatString) + 1, sizeof(char));
        strncpy(pInfo->format, pResult->barcodeFormatString, strlen(pResult->barcodeFormatString));
        pInfo->text = (char *)calloc(strlen(pResult->barcodeText) + 1, sizeof(char));
        strncpy(pInfo->text, pResult->barcodeText, strlen(pResult->barcodeText));
    }

    DBR_FreeTextResults(&pResults);

    return resultList;
}

void dbr_free_results(ResultList *resultList)
{
    int count = resultList->size;
    ResultInfo **pResultInfo = resultList->pResultInfo;

    for (int i = 0; i < count; i++)
    {
        ResultInfo *resultList = pResultInfo[i];
        if (resultList)
        {
            if (resultList->format != NULL)
                free(resultList->format);
            if (resultList->text != NULL)
                free(resultList->text);

            free(resultList);
        }
    }

    if (pResultInfo != NULL)
        free(pResultInfo);
}

void thread_func(void *barcodeReader, const char *fileName)
{
    DBR_DecodeFile(barcodeReader, fileName, "");

    TextResultArray *pResults;
    int ret = DBR_GetAllTextResults(barcodeReader, &pResults);
    int count = pResults->resultsCount;
    TextResult **results = pResults->results;

    ResultInfo **pResultInfo = (ResultInfo **)malloc(sizeof(ResultInfo *) * count);
    ResultList *resultList = (ResultList *)malloc(sizeof(ResultList));
    resultList->size = count;
    resultList->pResultInfo = pResultInfo;

    for (int i = 0; i < count; i++)
    {
        TextResult *pResult = results[i];
        ResultInfo *pInfo = (ResultInfo *)malloc(sizeof(ResultInfo));
        pInfo->format = NULL;
        pInfo->text = NULL;
        pResultInfo[i] = pInfo;
        // printf("Barcode format: %s, text: %s\n", pResult->barcodeFormatString, pResult->barcodeText);
        pInfo->format = (char *)calloc(strlen(pResult->barcodeFormatString) + 1, sizeof(char));
        strncpy(pInfo->format, pResult->barcodeFormatString, strlen(pResult->barcodeFormatString));
        pInfo->text = (char *)calloc(strlen(pResult->barcodeText) + 1, sizeof(char));
        strncpy(pInfo->text, pResult->barcodeText, strlen(pResult->barcodeText));
    }

    DBR_FreeTextResults(&pResults);

    if (callback)
    {
        int res = callback(resultList);
    }
}

void thread_decode(void *barcodeReader, const char *fileName)
{
    t = thread(thread_func, barcodeReader, fileName);
    t.join();
}

int registerCallback(callback_t foo)
{
    callback = foo;
    return 0;
}