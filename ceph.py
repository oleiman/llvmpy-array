#!/usr/bin/env python

# Import the llvmpy modules.
from llvm import *
from llvm.core import *
from llvm.ee import *
from ctypes import *

module = None

def sum(a1, a2, size1, size2):

    # Instantiate an empty module
    module = Module.new('ceph')

    # All the types involved here are "string"s and "int"s. This type is represented
    # by an object of the llvm.core.Type class:
    ty_ptr = Type.pointer(Type.int(8))
    ty_int = Type.int()     # by default 32 bits
    
    # We need to represent the classes of functions that do our array summing
    # This is represented by an object of the function type (llvm.core.FunctionType)
    ty_sum  = Type.function(ty_int, [ty_ptr, ty_ptr, ty_int, ty_int])
    ty_sumA = Type.function(ty_int, [ty_ptr, ty_int])
    
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

    bb_sumA = f_sumA.append_basic_block("entry")
    builder_sumA = Builder.new(bb_sumA)
    
    # allocate memory for an int
    res = builder_sumA.alloca(ty_int, "res")
    
    # instantiate a constant 'zero'
    zero = Constant.int(ty_int, 0)
    
    # store 'zero' in 'res'
    builder_sumA.store(zero, res)

    # load the contents of 'res' into a virtual register
    tmp2 = builder_sumA.load(res, "tmp2")
    
    # now do whatever the hell we want with it
    # currently just returning the size of the array in question
    # because it's too late to work on control flow
    tmp3 = builder_sumA.add(tmp2, size, "tmp3")
    builder_sumA.ret(tmp3)

    # NOTA BENE:
    # Due to a seemingly silly limitation of llvmpy (no string values...)
    # this doesn't work. Doesn't matter, though, since we're doing our osd-side
    # evaluation in C++. This 
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
