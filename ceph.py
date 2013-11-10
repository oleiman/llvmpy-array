# Import the llvmpy modules.
from llvm import *
from llvm.core import *
from llvm_cbuilder import *
import llvm_cbuilder.shortnames as C

import numpy as np
from ctypes import *

# TODO: write some comments

class LibOSD(CExternal):
    cls_read = Type.function(C.int, [C.void_p, C.int, 
                                     C.int, C.char_pp, 
                                     C.pointer(C.int)])
    cls_write = Type.function(C.int, [C.void_p, C.int, 
                                      C.int, C.char_p])
    cls_write_full = Type.function(C.int, [C.void_p, C.char_p])

class CBuilderOSD(CBuilder):

    def __init__(self, function):
        CBuilder.__init__(self, function)
        self.zero = self.constant(C.int, 0)
        self.one  = self.constant(C.int, 1)

    def cls_read(self, hctx, ofs, len, outdata, outdatalen):
        '''cls_read from libosd
        
        hctx : execution context
        ofs  : offset at which to begin read
        len  : number of bytes to read
        outdata : buffer for output data (char**)
        outdatalen : actual length of read
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_read(hctx, ofs, len, outdata, outdatalen)
        return CTemp(self, ret)

    def cls_write(self, hctx, ofs, len, indata):
        '''cls_write() from libosd
        
        hctx : execution context
        ofs  : offset at which to begin read
        len  : number of bytes to read
        indata : buffer containing input data (char*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_write(hctx, ofs, len, indata)
        return CTemp(self, ret)

    # TODO: implement this in object class on OSD
    # def cls_write_full(self, hctx, indata):
    #     '''cls_write_full() from libosd
        
    #     hctx : execution context
    #     indata : buffer containing input data (char*)
    #     '''
    #     libosd = LibOSD(self)
    #     ret = libosd.cls_write_full(hctx, indata)
    #     return CTemp(self, ret)

class CephArray:

    array_count = 0
    module = Module.new('ceph')
    
    def __init__(self, oid, dims, array = None):
        self.oid = oid
        self.dims = dims
        self.array = array
        self.func_n = CephArray.array_count
        CephArray.array_count += 1

    def _make_type(self, ndim, cb):
        return C.int if ndim == 1 else C.pointer(self._make_type(ndim-1, cb))

    def _allocate_read_buf(self, ndim, buf, cb):
        s0 = self.dims[len(self.dims)-ndim]
        if ndim == 1: 
            return 
        ty = self._make_type(ndim-1, cb)
        s1 = self.dims[len(self.dims)-ndim+1]
        d = cb.constant(C.int, s1)
        for s in range(0, s0):
            buf[s] = cb.array(ty, d)
            self._allocate_read_buf(ndim-1, buf[s], cb)

    def _allocate_write_buf(self, ndim, cb):
        length = reduce(lambda x,y: x*y, self.dims, 1)
        size = cb.constant(C.int, length)
        flat_arr = self.array.reshape((length));
        flat_arr = [cb.constant(C.int, x) for x in flat_arr];
        buf = cb.array(C.int, length)
        i = cb.var(C.int)
        i.assign(cb.zero)
        idx = 0
        with cb.loop() as loop:
            with loop.condition() as setcond:
                setcond (i < size)
            with loop.body():
                buf[i] = flat_arr[idx]
                i += cb.one
                idx + 1
        return buf

    def _write_array(self, buf, cb):
        hctx = cb.args[0]
        int_size_bytes = cb.sizeof(C.int).cast(C.int)
        length = cb.constant(C.int, reduce(lambda x,y: x*y, self.dims, 1))
        write_size = length * int_size_bytes
        bytes_written = cb.cls_write(hctx, cb.zero, write_size, buf.cast(C.void_p))

    def _read_array(self, ndim, buf, off, cb):
        int_size_bytes = cb.sizeof(C.int).cast(C.int)
        inner_dim = cb.constant(C.int, self.dims[-1])
        read_size = inner_dim * int_size_bytes
        hctx = cb.args[0]

        # open the array file when testing
        # O_RDONLY = cb.zero
        # fd = cb.open(cb.constant_string("foo.arr"), O_RDONLY)

        if ndim == 1:
            dltmp = cb.var(C.int).reference()
            buf_p = buf.reference().cast(C.char_pp)

            # for testing
            # bytes_read = cb.read(fd.value, buf.cast(C.void_p), read_size)

            bytes_read_osd = cb.cls_read(hctx, off, read_size, buf_p, dltmp)
            off += read_size
            return

        q = cb.var(C.int)
        q.assign(cb.zero)
        d_raw = self.dims[len(self.dims)-ndim]
        d = cb.constant(C.int, d_raw)
        with cb.loop() as loop:
            with loop.condition() as setcond:
                setcond(q < d)
            with loop.body():
                self._read_array(ndim-1, buf[q], off, cb)
                q += cb.one

    def _fold_loop(self, f, init, ndim, buf, cb):
        q = cb.var(C.int)
        q.assign(cb.zero)
        d_raw = self.dims[len(self.dims)-ndim]
        d = cb.constant(C.int, d_raw)
        with cb.loop() as loop:
            with loop.condition() as setcond:
                setcond(q < d)
            with loop.body():
                if ndim == 1:
                    init.assign(f(init, buf[q]))
                    q += cb.one
                else:
                    self._fold_loop(f, init, ndim-1, buf[q], cb)
                    q += cb.one

    def _gen_fold(self, module, func, init, name):
        ty_fold = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        self.fold_name = "%s_%d" % (name, self.func_n)
        f_fold  = module.add_function(ty_fold, self.fold_name)

        cb = CBuilderOSD(f_fold)

        # some constants for later
        false = cb.zero 
        true  = cb.one

        res  = cb.var(C.int)

        buf = cb.array(self._make_type(len(self.dims), cb), self.dims[0])
        self._allocate_read_buf(len(self.dims), buf, cb)

        offset = cb.var(C.int)
        offset.assign(cb.zero)
        fd = self._read_array(len(self.dims), buf, offset, cb)

        # define an addition function and generate the summation fold loop
        res.assign(cb.constant(C.int, init))
        self._fold_loop(func, res, len(self.dims), buf, cb)
    
        cb.ret(res)
        cb.close()

    def _gen_write(self, module):
        ty_write = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        self.write_name = "write_%d" % self.func_n
        f_write = module.add_function(ty_write, self.write_name)
        cb = CBuilderOSD(f_write)

        buf = self._allocate_write_buf(len(self.dims), cb)
        ret = self._write_array(buf, cb)

        cb.ret(cb.zero)
        cb.close()

    def fold(self, f, init, name):
        self._gen_fold(CephArray.module, f, init, name)

    def write(self):
        self._gen_write(CephArray.module)

    @classmethod
    def execute(cls):
        cls.module.verify()
        f = open("ceph.s", 'w')
        module_str = str(cls.module)
        f.write(module_str)
        # generate manifest here
        # ship off to osd with the IR

    @classmethod
    def from_npy_file(cls, oid, filename):
        npy_arr = np.load(filename)
        arr = cls(oid, npy_arr.shape, npy_arr)
        return arr
