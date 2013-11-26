# Import the llvmpy modules.
from llvm import *
from llvm.core import *
from llvm_cbuilder import *
import llvm_cbuilder.shortnames as C

import rados
import llvm_client
import struct
import socket
import sys
import pickle
import marshal
import time

import numpy as np
from ctypes import *

from osdbuilder import CBuilderOSD

import inspect
# TODO: write some comments


class CephArray:

    ceph_config = '/home/oren/code/ceph-private/src/ceph.conf'
    cls_client = llvm_client.CLSLLVMpyClient(ceph_config)
    
    def __init__(self, oid, dims = None, array = None):
        self.oid = oid
        self.dims = dims
        self.array = array
        self.contents = []
        self.module = Module.new('ceph')
        self.methods = []


    def _make_type(self, ndim, cb):
        return C.int if ndim == 1 else C.pointer(self._make_type(ndim-1, cb))

    def _write_dims(self, cb):
        hctx = cb.args[0]
        int_size_bytes = cb.sizeof(C.int).cast(C.int)
        native_dims = [cb.constant(C.int, d) for d in self.dims]
        dim = cb.var(C.int)
        for idx, d in enumerate(native_dims):
            dim.assign(d)
            cb.cls_setxattr(hctx, cb.constant_string("d%d" % idx),
                            dim.reference().cast(C.char_p),
                            int_size_bytes)

    def _write_array(self,cb):
        hctx = cb.args[0]
        buf = cb.args[1]
        size = cb.var(C.int)
        mtime = cb.var(C.int64).reference()
        exists = cb.cls_stat(hctx, size.reference(), mtime)

        ret = cb.var(C.int)

        self._write_dims(cb)
        int_size_bytes = cb.sizeof(C.int).cast(C.int)
        raw_len = reduce(lambda x,y: x*y, self.dims, 1)

        with cb.ifelse(exists.value < cb.zero) as ifelse:
            with ifelse.then():
                ret.assign(cb.cls_write_bl_full(hctx, cb.zero, buf).value)
            with ifelse.otherwise():
                ret.assign(cb.cls_write_bl_full(hctx, size, buf).value)

        return ret

    def _fold_loop(self, f, init, cb):
        hctx = cb.args[0]
        raw_length = reduce(lambda x,y: x*y, self.dims, 1)
        length = cb.constant(C.int, raw_length)

        int_size_bytes = cb.sizeof(C.int).cast(C.int)
        read_size = length * int_size_bytes

        buf = cb.var(C.pointer(C.int))
        buf_p = buf.reference().cast(C.char_pp)

        dltmp = cb.var(C.int)
        off = cb.var(C.int).assign(cb.zero)
        cb.cls_read(hctx, off, read_size, buf_p, dltmp.reference())

        i = cb.var(C.int).assign(cb.zero)
        with cb.loop() as loop:
            with loop.condition() as setcond:
                setcond(i < (dltmp / int_size_bytes))
            with loop.body():
                init.assign(f(init, buf[i]))
                i += cb.one

    def _gen_handle(self, name):
        return "%s_%s" % (name, self.oid)

    def _gen_fold(self, func, init, name):
        handle = self._gen_handle(name)
        if handle in self.methods:
            return handle
        self.methods.append(handle)
        ty_fold = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        f_fold  = self.module.add_function(ty_fold, handle)

        cb = CBuilderOSD(f_fold)
        
        res  = cb.var(C.int).assign(cb.constant(C.int, init))
        self._fold_loop(func, res, cb)

        cb.ret(res)
        cb.close()
        return handle

    def _gen_write(self):
        handle = self._gen_handle("write")
        if handle in self.methods:
            return handle
        self.methods.append(handle)
        ty_write = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        f_write = self.module.add_function(ty_write, handle)
        cb = CBuilderOSD(f_write)

        res = self._write_array(cb)

        cb.ret(res)
        cb.close()
        
        return handle

    @classmethod
    def execute(cls, requests, arrays):
        tmp = Module.new('tmp')
        for oid, a in arrays.iteritems():
            tmp.link_in(a.module, True)

        tmp.verify()
        irstr = str(tmp)
        responses = []
        for req in requests:
            oid = req[0]
            func = req[1]
            a = arrays[oid]
            data = []
            if 'write' in func:
                length = reduce(lambda x,y: x*y, a.array.shape, 1)
                data = list(a.array.reshape((length)))
            val = cls.cls_client.llvm_exec(irstr, data, oid, func)
            responses.append({
                    'oid': oid,
                    'called': func, 
                    'return': val, 
                    'timestamp': time.ctime()
                    })
        return responses
