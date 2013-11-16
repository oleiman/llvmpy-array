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
    cls_map_get_val = Type.function(C.int, [C.void_p, C.char_p,
                                            C.char_pp, C.pointer(C.int)])
    cls_setxattr = Type.function(C.int, [C.void_p, C.char_p,
                                            C.char_p, C.int])
    cls_map_get_keys = Type.function(C.int, [C.void_p, C.char_p, C.int64,
                                             C.pointer(C.char_pp), 
                                             C.pointer(C.pointer(C.int))])

class CBuilderOSD(CBuilder):

    def __init__(self, function):
        CBuilder.__init__(self, function)
        self.zero = self.constant(C.int, 0)
        self.one  = self.constant(C.int, 1)

    def cls_read(self, hctx, ofs, length, outdata, outdatalen):
        '''cls_read from libosd
        
        hctx : execution context
        ofs  : offset at which to begin read
        length  : number of bytes to read
        outdata : buffer for output data (char**)
        outdatalen : actual length of read
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_read(hctx, ofs, length, outdata, outdatalen)
        return CTemp(self, ret)

    def cls_write(self, hctx, ofs, length, indata):
        '''cls_write() from libosd
        
        hctx : execution context
        ofs  : offset at which to begin read
        length  : number of bytes to read
        indata : buffer containing input data (char*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_write(hctx, ofs, length, indata)
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


    def cls_setxattr(self, hctx, key, indata, length):
        '''cls_setxattr() from libosd
        
        hctx : execution context
        key  : key into object map
        indata : buffer containing input data (char*)
        length  : length of the input value value
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_setxattr(hctx, key, indata, length)
        return CTemp(self, ret)
    
    def cls_map_get_val(self, hctx, key, outdata, outdatalen):
        '''cls_map_get_val() from libosd

        hctx : execution context
        key  : key into object map
        outdata : buffer for output data (char**)
        outdatalen : actual length of object map value
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_map_get_val(hctx, key, outdata, outdatalen)
        return CTemp(self, ret)

    def cls_map_get_keys(self, hctx, prefix, max_to_get, keys, key_lens):
        '''wrapper for cls_map_get_keys() from libosd

        hctx       : method context
        prefix     : key prefix
        max_to_get : maximum number of keys to read
        keys       : pointer to buffer-array to store the keys (char***)
        key_lens   : pointer to array to hold the length of each key (int**)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_map_get_keys(hctx, prefix, max_to_get, keys, key_lens)
        return CTemp(self, ret)

class CephArray:

    module = Module.new('ceph')
    manifest = []
    methods = []
    ceph_config = '/home/oren/code/ceph-private/src/ceph.conf'
    cls_client = llvm_client.CLSLLVMpyClient(ceph_config)
    
    def __init__(self, oid, dims = None, array = None):
        self.oid = oid
        self.dims = dims
        self.array = array
        self.contents = []

    @classmethod
    def from_npy_file(cls, oid, filename):
        npy_arr = np.load(filename)
        return cls(oid, npy_arr.shape, npy_arr)

    @classmethod
    def no_file(cls, oid):
        dims = cls._get_dims(oid)
        return cls(oid, dims)

    def _make_type(self, ndim, cb):
        return C.int if ndim == 1 else C.pointer(self._make_type(ndim-1, cb))

    def _parse_llvm_int(self, val):
        return int(str(val.value).split()[1])


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

    def _write_array(self, buf, cb):
        self._write_dims(cb)
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

        if ndim == 1:
            dltmp = cb.var(C.int).reference()
            buf_p = buf.reference().cast(C.char_pp)
            bytes_read_osd = cb.cls_read(hctx, off, read_size, buf_p, dltmp)
            off += read_size
        else:
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

    def _gen_handle(self, name):
        return "%s_%s" % (name, self.oid)

    def _gen_fold(self, module, func, init, name):
        handle = self._gen_handle(name)
        if handle in CephArray.methods:
            return handle
        CephArray.methods.append(handle)
        ty_fold = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        f_fold  = module.add_function(ty_fold, handle)

        cb = CBuilderOSD(f_fold)

        res  = cb.var(C.int)

        buf = cb.array(self._make_type(len(self.dims), cb), self.dims[0])
        self._allocate_read_buf(len(self.dims), buf, cb)

        offset = cb.var(C.int)
        offset.assign(cb.zero)
        fd = self._read_array(len(self.dims), buf, offset, cb)

        # define an fold function and generate the fold loop
        res.assign(cb.constant(C.int, init))
        self._fold_loop(func, res, len(self.dims), buf, cb)
    
        cb.ret(res)
        cb.close()
        return handle

    def _gen_write(self, module):
        handle = self._gen_handle("write")
        if handle in self.methods:
            return handle
        CephArray.methods.append(handle)
        ty_write = Type.function(C.int, [C.void_p, C.void_p, C.void_p])
        f_write = module.add_function(ty_write, handle)
        cb = CBuilderOSD(f_write)

        buf = self._allocate_write_buf(len(self.dims), cb)
        ret = self._write_array(buf, cb)

        cb.ret(cb.zero)
        cb.close()
        return handle

    def fold(self, f, init, name):
        CephArray.add_to_manifest(self.oid, self._gen_handle(name))
        if name not in self.contents:
            self._gen_fold(CephArray.module, f, init, name)
            self.contents.append(name)

    def write(self):
        CephArray.add_to_manifest(self.oid, self._gen_handle("write"))
        if "write" not in self.contents:
            self._gen_write(CephArray.module)
            self.contents.append("write")

    @classmethod
    def execute(cls):
        cls.module.verify()
        irstr = str(cls.module)
        cls.manifest.append(irstr)

        responses = []
        host = 'localhost'
        port = 50000
        size = 2**16
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host,port))
        sys.stdout.write('%')

        s.send(pickle.dumps(cls.manifest))
        data = pickle.loads(s.recv(size))
        print data
        s.close()

    @classmethod
    def write_manifest(cls):
        f = open("manifest", 'wb')
        for req in cls.manifest:
            f.write("%s,%s\n" % (req[0], req[1]))
            
    @classmethod
    def add_to_manifest(cls, oid, handle):
        CephArray.manifest.append([oid, handle])
