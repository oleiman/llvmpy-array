#ifndef CLS_LLVMPY_CLI_H
#define CLS_LLVMPY_CLI_H

#include <boost/python.hpp>
#include "rados/librados.hpp"
#include "cls_llvm_ops.hpp"

using namespace std;
using namespace librados;

struct CLSLLVMpyClient {
  librados::Rados *cluster;
  librados::IoCtx *ioctx;

  CLSLLVMpyClient(const char*);
  ~CLSLLVMpyClient();
  int cls_llvm_exec(const char*, boost::python::list, string, string);
  int pack_and_ship(const string&, char*, int, cls_llvm_eval_op&);
private:
  void init(const char *);
};

#endif
