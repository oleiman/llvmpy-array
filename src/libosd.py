from llvm import *
from llvm.core import *
from llvm_cbuilder import *
import llvm_cbuilder.shortnames as C

class LibOSD(CExternal):
    cls_read          = Type.function(C.int, [C.void_p, C.int, 
                                             C.int, C.char_pp, 
                                             C.pointer(C.int)])
    cls_write         = Type.function(C.int, [C.void_p, C.int, 
                                             C.int, C.char_p])
    cls_write_bl      = Type.function(C.int, [C.void_p, C.int, 
                                             C.int, C.void_p])
    cls_write_bl_full = Type.function(C.int, [C.void_p, C.int, 
                                             C.void_p])
    cls_write_full    = Type.function(C.int, [C.void_p, C.char_p])
    cls_map_get_val   = Type.function(C.int, [C.void_p, C.char_p,
                                             C.char_pp, C.pointer(C.int)])
    cls_setxattr      = Type.function(C.int, [C.void_p, C.char_p,
                                             C.char_p, C.int])
    cls_map_get_keys  = Type.function(C.int, [C.void_p, C.char_p, C.int64,
                                             C.pointer(C.char_pp), 
                                             C.pointer(C.pointer(C.int))])
    cls_stat          = Type.function(C.int, [C.void_p, C.pointer(C.int), 
                                             C.pointer(C.int64)])
    cls_log           = Type.function(C.int, [C.int, C.char_p], True)
