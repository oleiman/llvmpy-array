from distutils.core import setup
from distutils.extension import Extension
 
setup(name="llvmpy-array",
    ext_modules=[
        Extension("llvm_client", ["cls_llvmpy_client.cc", "cls_llvm_ops.cc"],
        libraries = ["boost_python", "rados"])
    ])
