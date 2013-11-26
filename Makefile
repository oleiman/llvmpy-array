CXX=clang++
CC=clang
LIBS=-ldl -lpthread

SRC = ./src
CLS_LLVM_PRE = ./src/cls_llvmpy
CLS_LLVM_SRC = $(CLS_LLVM_PRE)/*.cc
CLS_LLVM_SETUP = $(CLS_LLVM_PRE)/setup.py

SERVER = $(SRC)/array_server.py
CLIENT = $(SRC)/ceph_client.py

LLVM_CXXFLAGS=$(shell llvm-config --cxxflags)
LLVM_LDFLAGS=$(shell llvm-config --ldflags)
LLVM_LIBS=$(shell llvm-config --libs)

all: llvm_client.so arrays

test: run_server run_client 

arrays:
	python $(SRC)/gen_arrays.py
	cp *.npy $(SRC)

run_server:
	$(SERVER)
run_client:
	sleep 1
	$(CLIENT)

ceph_client.py: ceph.py 

array_server.py: ceph_array.py

llvm_client.so: $(CLS_LLVM_SRC) $(CLS_LLVM_SETUP)
	python $(CLS_LLVM_SETUP) build
	cp $(CLS_LLVM_PRE)/build/lib.*/llvm_client.so $(SRC)

clean:
	-rm $(CLS_LLVM_PRE)/build/lib.*/llvm_client.so *.npy $(SRC)/*.npy
