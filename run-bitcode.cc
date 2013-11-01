#include <stdio.h>

#include <string>
#include <memory>
#include <iostream>

#ifdef V3
#include <llvm/LLVMContext.h>
#include <llvm/Module.h>
#else
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#endif

#include <llvm/Support/system_error.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/Bitcode/ReaderWriter.h>
#include <llvm/ExecutionEngine/ExecutionEngine.h>
#include <llvm/ADT/OwningPtr.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/ExecutionEngine/JIT.h>

using namespace std;
using namespace llvm;

extern "C" {
void my_function(void)
{
  printf("in my_function\n");
}
}

int main()
{
    InitializeNativeTarget();
    llvm_start_multithreaded();
    LLVMContext context;
    string error;
    OwningPtr<MemoryBuffer> buf;
    error_code status = MemoryBuffer::getSTDIN(buf);
    if (status != 0) {
      cerr << status.message() << "\n";
      exit(1);
    }
    Module *m = ParseBitcodeFile(buf.get(), context, &error);
    if (!m) cout << "fucker\n";
    
    ExecutionEngine *ee = ExecutionEngine::create(m);
    Function* func = ee->FindFunctionNamed("sum");
      
    typedef int (*PFN)(const char* a1, const char* a2, int size1, int size2);
    PFN pfn = reinterpret_cast<PFN>(ee->getPointerToFunction(func));
    int ret = pfn(string("foo.arr").c_str(), string("bar.arr").c_str(), 10, 12);
    cout << "foo + bar: " << ret << endl;
    
    delete ee;
}
