FROM ubuntu:19.04 as build

MAINTAINER Stefan Lemme <stefan.lemme@dfki.de>

RUN apt-get update && \
  apt-get install -y cmake make g++ git libpng-dev python3-dev python3-pip && \
  apt-get install -y llvm-8-dev clang-8 llvm clang libclang-8-dev libedit-dev && \
  apt-get install -y vim git-svn cmake-curses-gui libopenctm-dev && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone https://github.com/stlemme/RV.git --recursive -b standalone_80 rv_src && \
  mkdir rv_build && \
  cd rv_build && \
  cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=14 ../rv_src && \
  make

RUN git clone https://github.com/AnyDSL/anydsl.git -b cmake-based-setup anydsl_src && \
  mkdir anydsl_build && \
  cd anydsl_build && \
  cmake -DCMAKE_BUILD_TYPE=Release -DRUNTIME_JIT=ON -DBUILD_TESTING=ON -DAnyDSL_DEFAULT_BRANCH=llvm-cmake -DRV_INCLUDE_DIR=/opt/rv_src/include -DRV_LIBRARY=/opt/rv_build/src/libRV.a -DRV_SLEEF_LIBRARY=/opt/rv_build/vecmath/libgensleef.a ../anydsl_src && \
  make

RUN git clone https://github.com/pybind/pybind11 -b stable && \
  pip3 install pytest && \
  cd pybind11 && \
  cmake -DCMAKE_BUILD_TYPE=Release . && \
  make install

COPY ./requirements*.txt /opt/rendering-support-service/

RUN pip3 install -r /opt/rendering-support-service/requirements.txt && \
    pip3 install -r /opt/rendering-support-service/requirements-dev.txt

COPY . /opt/rendering-support-service

RUN mkdir rss_build && \
    cd rss_build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DAnyDSL_runtime_DIR=/opt/anydsl_build/share/anydsl/cmake -DPYTHON_EXECUTABLE=/usr/bin/python3 ../rendering-support-service && \
    make dist

# compose final image
FROM ubuntu:19.04

RUN apt-get update && \
    apt-get install -y libopenctm-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/rss_build/dist/GloBiE /opt/rendering-support-service/GloBiE

WORKDIR /opt/rendering-support-service

CMD ["/opt/rendering-support-service/GloBiE"]

EXPOSE 8080

