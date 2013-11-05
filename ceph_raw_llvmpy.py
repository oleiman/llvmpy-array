# Import the llvmpy modules.
from llvm import *
from llvm.core import *

def sum(a1, a2, size1, size2):

    # Instantiate an empty module
    module = Module.new('ceph')

    # All the types involved here are "string"s and "int"s. This type is represented
    # by an object of the llvm.core.Type class:
    ty_ptc = Type.pointer(Type.int(8))
    ty_pti = Type.pointer(Type.int(32))
    ty_int = Type.int(32)
    ty_int64 = Type.int(64)
    
    # We need to represent the classes of functions that do our array summing
    # This is represented by an object of the function type (llvm.core.FunctionType)
    ty_sum  = Type.function(ty_int, [ty_ptc, ty_ptc, ty_int, ty_int])
    ty_sumA = Type.function(ty_int, [ty_ptc, ty_int])

    ty_open = Type.function(ty_int, [ty_ptc, ty_int], True)
    ty_read = Type.function(ty_int64, [ty_int, ty_ptc, ty_int]);
    ty_calloc = Type.function(ty_ptc, [ty_int, ty_int]);

    # declare some c functions for I/O use later
    c_open = Function.new(module, ty_open, "open")
    c_read = Function.new(module, ty_read, "read")
    c_calloc = Function.new(module, ty_calloc, "calloc")
    
    # Now we need a function named 'sum' of this type. Functions are not
    # free-standing (in llvmpy); it needs to be contained in a module.
    
    f_sum = module.add_function(ty_sum, "sum")

    # function arguments (two array names as char* and their sizes)
    a1    = f_sum.args[0]; a1.name = "a1"
    a2    = f_sum.args[1]; a2.name = "a2"
    size1 = f_sum.args[2]; size1.name = "size1"
    size2 = f_sum.args[3]; size2.name = "size2"

    # function to sum each individual array
    f_sumA = module.add_function(ty_sumA, "sumA")
    a    = f_sumA.args[0]; a.name = "a"
    size = f_sumA.args[1]; size.name = "size"

    # Our function needs a "basic block" -- a set of instructions that
    # end with a terminator (like return, branch etc.). By convention
    # the first block is called "entry".
    bb_sum = f_sum.append_basic_block("entry")
    
    # Let's add instructions into the block. For this, we need an
    # instruction builder:
    builder_sum = Builder.new(bb_sum)

    # OK, now for the instructions themselves. We'll create an add
    # instruction that returns the sum as a value, which we'll use
    # a ret instruction to return.

    sum1 = builder_sum.call(f_sumA, [a1, size1], "sum1")
    sum2 = builder_sum.call(f_sumA, [a2, size2], "sum2")
    
    tmp = builder_sum.add(sum1, sum2, "tmp")
    builder_sum.ret(tmp)

    ## BASIC BLOCKS FOR sumA(CHAR*, CHAR*, INT, INT)
    
    # entry block and builder
    bb_sumA = f_sumA.append_basic_block("entry")
    builder_sumA = Builder.new(bb_sumA)

    # loop initialization block (happens once)
    bb_loop_init = f_sumA.append_basic_block("loop_init")
    builder_linit = Builder.new(bb_loop_init)

    # loop block (adds array elements to result) and builder
    bb_loop = f_sumA.append_basic_block("loop")
    builder_loop = Builder.new(bb_loop)

    # exit block and builder
    bb_exit = f_sumA.append_basic_block("exit")
    builder_exit = Builder.new(bb_exit)

    ####################################################################

    # instantiate some constants
    zero = Constant.int(ty_int, 0)
    O_RDONLY = zero
    one  = Constant.int(ty_int, 1)
    int_size = Constant.int(ty_int, 4)
    read_size = builder_sumA.mul(int_size, size)

    # allocate memory for the result, initialize to 0
    res = builder_sumA.alloca(ty_int, "res")
    builder_sumA.store(zero, res)

    # open the serialized array file for reading
    fd = builder_sumA.call(c_open, [a, O_RDONLY], "fd")

    # allocate memory for the read buffer, ensuring that we
    bufi = builder_sumA.alloca(ty_pti, "buf")
    memc = builder_sumA.call(c_calloc, [size, int_size])
    
    # cast the char* that came back from calloc to an 32-bit int*
    # and store that pointer back to the pointer to read buffer
    memi = builder_sumA.bitcast(memc, ty_pti)
    builder_sumA.store(memi, bufi)
    
    tmp_buf  = builder_sumA.load(bufi)
    bufc = builder_sumA.bitcast(tmp_buf, ty_ptc)
    
    bytes_read = builder_sumA.call(c_read, [fd, bufc, read_size])
    builder_sumA.branch(bb_loop_init)
    # probably do some error checking here... 
    # ensure correct # of bytes read

    # initialize counter
    ip = builder_linit.alloca(ty_int, "i")
    builder_linit.store(zero, ip)
    arr = builder_linit.load(bufi)
    builder_linit.branch(bb_loop)

    # add arr[i] to result
    # i_tmp = builder_loop.load(ip)
    i = builder_loop.load(ip)
    tmp_res = builder_loop.load(res, "tmp_res")
    eltp = builder_loop.gep(arr, [i])
    elt  = builder_loop.load(eltp)
    tmp  = builder_loop.add(tmp_res, elt)
    builder_loop.store(tmp, res)

    # increment the counter and
    # branch if out of bounds
    i_tmp = builder_loop.add(i, one)
    builder_loop.store(i_tmp, ip)
    done = builder_loop.icmp(ICMP_SLT, i_tmp, size)
    builder_loop.cbranch(done, bb_loop, bb_exit)
    
    # add the file descriptor to result 
    # confirms that the open succeeded
    builder_exit.free(memc)
    builder_exit.ret(tmp)

    # NOTA BENE:
    # Due to a seemingly silly limitation of llvmpy (no string values...)
    # this doesn't work. Doesn't matter, though, since we're doing our osd-side
    # evaluation in C++.
    #
    # we're done building our functions, lets evaluate sum("foo.arr", "bar.arr", 10, 12)
    # ee = ExecutionEngine.new(module)
    # arg1 = <WTF>
    # arg2 = <WTF>
    # arg3 = GenericValue.int(ty_int, 10)
    # arg4 = GenericValue.int(ty_int, 12)
    # ret_val = ee.run_function(f_sum, [arg1, arg2, arg3, arg4])
    # print "returned", ret_val.as_int()

    # we could just use the Module.to_bitcode() method here, but I want to keep the
    # IR around for inspection. I'm building the bitcode in my Makefile
    f = open("ceph.s", 'w')
    module_str = str(module)
    f.write(module_str)
