CXX=clang++
CC=clang
LIBS=-ldl -lpthread

LLVM_CXXFLAGS=$(shell llvm-config --cxxflags)
LLVM_LDFLAGS=$(shell llvm-config --ldflags)
LLVM_LIBS=$(shell llvm-config --libs)

all: get_libs.s arraysum.bc run-bitcode writearrays ceph.bc

arraysum.bc: arraysum.s
	llvm-as arraysum.s -o arraysum.bc

arraysum.s: arraysum.c
	clang -S -emit-llvm arraysum.c

ceph.bc: ceph.s
	llvm-as ceph.s -o ceph.bc

ceph.s: llvm_client.so ceph.py ceph_client.py
	ceph_client.py

llvm_client.so: cls_llvm_py_client.cc setup.py
	python setup.py build
	cp build/lib.*/llvm_client.so .

get_libs.s: get_libs.cc
	clang++ -Wall -S -emit-llvm get_libs.cc

writearrays: writearrays.c
	gcc writearrays.c -o writearrays -std=gnu99
	# ./writearrays

run-bitcode: run-bitcode.cc
	$(CXX) -rdynamic $(LLVM_CXXFLAGS) $(LLVM_LDFLAGS) -DV3 $< -o $@ $(LLVM_LIBS) $(LIBS) -fexceptions

run: run-bitcode arraysum.bc ceph.bc
	@echo "reference implementation (arraysum.c):"
	@./run-bitcode < arraysum.bc
	@echo "current state of programmatically generated code (ceph.py):"
	@./run-bitcode < ceph.bc

clean:
	-rm run-bitcode *.bc *.s *.so
