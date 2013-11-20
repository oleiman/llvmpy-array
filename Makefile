CXX=clang++
CC=clang
LIBS=-ldl -lpthread

LLVM_CXXFLAGS=$(shell llvm-config --cxxflags)
LLVM_LDFLAGS=$(shell llvm-config --ldflags)
LLVM_LIBS=$(shell llvm-config --libs)

all: llvm_client.so

run: run_server run_client

run_server:
	./array_server.py
run_client:
	sleep 1
	./ceph_client.py

ceph_client.py: ceph.py 

array_server.py: ceph_array.py

llvm_client.so: cls_llvmpy_client.cc setup.py
	python setup.py build
	cp build/lib.*/llvm_client.so .

clean:
	-rm *.so
