#ifndef CLS_LLVMPY_CLI_H
#define CLS_LLVMPY_CLI_H

#include "rados/librados.hpp"

using namespace std;
using namespace librados;

struct CLSLLVMpyClient {
  librados::Rados *cluster;
  librados::IoCtx *ioctx;

  CLSLLVMpyClient(const char *);
  ~CLSLLVMpyClient();
  int cls_llvm_exec(const char *, string, string);
};

#endif
