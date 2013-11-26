from llvm_cbuilder import *
import llvm_cbuilder.shortnames as C

from libosd import LibOSD

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
        ofs  : offset at which to begin write
        length  : number of bytes to write
        indata : buffer containing input data (char*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_write(hctx, ofs, length, indata)
        return CTemp(self, ret)

    def cls_write_bl(self, hctx, ofs, length, indata):
        '''cls_write_bl() from libosd
        
        hctx : execution context
        ofs  : offset at which to begin write
        length  : number of bytes to write
        indata : bufferlist containing input data (void*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_write_bl(hctx, ofs, length, indata)
        return CTemp(self, ret)

    def cls_write_bl_full(self, hctx, ofs, indata):
        '''cls_write_bl() from libosd
        
        hctx : execution context
        ofs  : offset at which to begin write
        indata : bufferlist containing input data (void*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_write_bl_full(hctx, ofs, indata)
        return CTemp(self, ret)

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

    def cls_log(self, log_level, msg, *args):
        '''cls_log() from libosd
        
        log_level : the log level
        msg       : message to be logged
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_log(log_level, msg, *args)
        return CTemp(self, ret)

    def cls_stat(self, hctx, size, mtime):
        '''cls_stat() from libosd
        
        hctx  : method context
        size  : size destination (int*)
        mtime : modified time destination (int64*)
        '''
        libosd = LibOSD(self)
        ret = libosd.cls_stat(hctx, size, mtime)
        return CTemp(self, ret)



