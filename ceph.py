# Import the llvmpy modules.
from llvm import *
from llvm.core import *
from llvm_cbuilder import *
import llvm_cbuilder.shortnames as C

def gen_sumA(module):
    ty_sumA = Type.function(C.int, [C.char_p, C.int])
    f_sumA  = module.add_function(ty_sumA, "sumA")
    cb = CBuilder(f_sumA)

    a    = cb.args[0]
    size = cb.args[1]
    i    = cb.var(C.int)
    res  = cb.var(C.int)

    # some constants for later
    false = O_RDONLY = zero = cb.constant(C.int, 0)
    true  = one = cb.constant(C.int, 1)
    int_size_bytes = cb.sizeof(C.int).cast(C.int)
    read_size = size * int_size_bytes

    # buf = cb.constant_null(C.void_p)
    buf = cb.array(C.int, size)
    buf_p = buf.reference()
    fd = cb.open(a, O_RDONLY)
    bytes_read = cb.read(fd.value, buf_p.cast(C.void_p), read_size)

    # add it up baby
    res.assign(zero)
    i.assign(zero)
    with cb.loop() as loop:
        with loop.condition() as setcond:
            setcond(i < size)

        with loop.body():
            res += buf[i]
            i += one
    
    # cb.ret(bytes_read.value.cast(C.int))
    cb.ret(res)
    cb.close()
    
    return f_sumA

def gen_sum(module):
    ty_sum = Type.function(C.int, [C.char_p, C.char_p, C.int, C.int])
    f_sum  = module.add_function(ty_sum, "sum")

    cb = CBuilder(f_sum)

    # aliases for function arguments
    a1    = cb.args[0]
    a2    = cb.args[1]
    size1 = cb.args[2]
    size2 = cb.args[3]

    f_sumA = cb.get_function_named("sumA")
    sum1   = f_sumA(a1, size1)
    sum2   = f_sumA(a2, size2)
    total  = sum1 + sum2

    cb.ret(total)
    cb.close()

    return f_sum

def arraylib_init():
    module = Module.new('ceph')

    # declare and define the sumA function, which is called by sum
    f_sumA = gen_sumA(module)
    f_sum  = gen_sum(module)

    # we could execute these functions here if we wanted to

    module.verify()

    f = open("ceph.s", 'w')
    module_str = str(module)
    f.write(module_str)
