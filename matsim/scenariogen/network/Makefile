
# Setup the sumo environment
# Deprecated: You can install sumo via pip

export SUMO_HOME="env"

PREFIX=$(abspath env)

.ONESHELL: # Applies to every targets in the file!
.DEFAULT_GOAL := all

download:
	mkdir -p build
	mkdir -p env

	cd build

	wget -nc https://sumo.dlr.de/releases/1.17.0/sumo-src-1.17.0.tar.gz
	tar -xf sumo-src-1.17.0.tar.gz

	wget -nc https://dlcdn.apache.org//xerces/c/3/sources/xerces-c-3.2.4.tar.gz
	tar -xf xerces-c-3.2.4.tar.gz

	wget -nc https://src.fedoraproject.org/repo/pkgs/fox/fox-1.6.57.tar.gz/sha512/e7b91054a9ea674818803415284cb61572935d22466e446cb37ef68344e2684e8acd567f7c8a6912f939dcbcc37455119ad6a01ac30513f460d0b3937b7e6087/fox-1.6.57.tar.gz
	tar -xf fox-1.6.57.tar.gz

	wget -nc https://github.com/OSGeo/gdal/releases/download/v3.7.0/gdal-3.7.0.tar.gz
	tar -xf gdal-3.7.0.tar.gz

	wget -nc https://download.osgeo.org/proj/proj-9.2.1.tar.gz
	tar -xf proj-9.2.1.tar.gz

	wget -nc https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz
	tar -xf sqlite-autoconf-3420000.tar.gz

sqlite:
	cd build/sqlite-autoconf-3420000

	SQLITE_ENABLE_COLUMN_METADATA=1 ./configure --prefix=$(PREFIX)
	SQLITE_ENABLE_COLUMN_METADATA=1 make install

xerces:
	cd build/xerces-c-3.2.4

	./configure --prefix=$(PREFIX)
	make install

fox:
	cd build/fox-1.6.57

	./configure --prefix=$(PREFIX)
	make install

proj:
	cd build/proj-9.2.1

	mkdir -p cmake-build && cd cmake-build
	cmake -DCMAKE_INSTALL_PREFIX=$(PREFIX) -DCMAKE_PREFIX_PATH=$(PREFIX)\
	 ../
	make install

gdal: sqlite proj
	cd build/gdal-3.7.0

	mkdir -p cmake-build && cd cmake-build
	cmake -DCMAKE_INSTALL_PREFIX=$(PREFIX) -DCMAKE_PREFIX_PATH=$(PREFIX)\
	 -DSQLite3_INCLUDE_DIR=$(PREFIX)/include -DSQLite3_LIBRARY=$(PREFIX)/lib/libsqlite3.so\
	 -DPROJ_INCLUDE_DIR=$(PREFIX)/include -DPROJ_LIBRARY=$(PREFIX)/lib64/libproj.so.25\
	 ../
	make install

sumo: gdal fox xerces
	cd build/sumo-1.17.0

	mkdir -p cmake-build && cd cmake-build
	cmake -DCMAKE_INSTALL_PREFIX=$(PREFIX) -DCMAKE_PREFIX_PATH=$(PREFIX)\
	 -DSQLite3_INCLUDE_DIR=$(PREFIX)/include -DSQLite3_LIBRARY=$(PREFIX)/lib/libsqlite3.so\
	 -DGDAL_INCLUDE_DIR=$(PREFIX)/include -DGDAL_LIBRARY=$(PREFIX)/lib64/libgdal.so\
	 -DPROJ_INCLUDE_DIR=$(PREFIX)/include -DPROJ_LIBRARY=$(PREFIX)/lib64/libproj.so.25\
	 ../
	make install

all: download sumo