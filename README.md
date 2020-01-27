
# GloBiE

## Prerequisites

 - Working [AnyDSL](https://github.com/AnyDSL/anydsl.git) build with [LLVM](http://releases.llvm.org/) including [RV](https://github.com/cdl-saarland/rv.git)
 - [CMake](https://cmake.org/)
 - [Python](https://www.python.org/) including development package
 - [pybind11](https://github.com/pybind/pybind11.git)

## Build instructions

```
$ pip install -r requirements.txt
$ pip install -r requirements-dev.txt
$ mkdir build
$ cd build && cmake -DAnyDSL_runtime_DIR=<path to anydsl_runtime-config.cmake> -Dpybind11_DIR=<path to pybind11-config.cmake> ..
$ cmake --build build
```

## Running the webservice

```
$ python server.py
```

Access to the exposed API via port 8080 by default.
