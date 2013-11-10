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
    Function* write = ee->FindFunctionNamed("write_0");
    Function* sum1 = ee->FindFunctionNamed("sumA_0");
    Function* sum2 = ee->FindFunctionNamed("sumA_1");
      
    typedef int (*PFN)(const void* a1, const void* a2, void *a3);

    if (write) {
      PFN write_fn = reinterpret_cast<PFN>(ee->getPointerToFunction(sum1));
      int write_ret = write_fn(NULL, NULL, NULL);
      cout << write_ret << endl;
    }

    PFN pfn1 = reinterpret_cast<PFN>(ee->getPointerToFunction(sum1));
    int ret1  = pfn1(NULL, NULL, NULL);
    

    PFN pfn2 = reinterpret_cast<PFN>(ee->getPointerToFunction(sum2));
    int ret2 = pfn2(NULL, NULL, NULL);
    
    cout << "foo + bar: " << ret1 + ret2 << endl;
    // cout << "foo + bar: " << ret1 << endl;
    
    delete ee;
}
