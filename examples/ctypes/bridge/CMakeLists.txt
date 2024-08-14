cmake_minimum_required(VERSION 3.0.0)

project(bridge VERSION 0.1.0)

INCLUDE_DIRECTORIES("${CMAKE_CURRENT_SOURCE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}/../../../include")
if (CMAKE_HOST_WIN32)
    LINK_DIRECTORIES("${CMAKE_CURRENT_SOURCE_DIR}/../../../lib/Win")
else()
    LINK_DIRECTORIES("${CMAKE_CURRENT_SOURCE_DIR}/../../../lib/linux")
endif()
add_library(${PROJECT_NAME} SHARED bridge.cpp)

if(CMAKE_HOST_WIN32)
    target_link_libraries (${PROJECT_NAME} "DBRx64")
else()
    target_link_libraries (${PROJECT_NAME} "DynamsoftBarcodeReader")
endif()
