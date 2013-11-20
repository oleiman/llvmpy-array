#ifndef CEPH_CLS_LLVMPY_OPS_H
#define CEPH_CLS_LLVMPY_OPS_H

#include "rados/librados.hpp"

using namespace std;

struct cls_llvm_eval_op {
  ceph::bufferlist bitcode;
  string function;
  ceph::bufferlist input;
};

struct cls_llvm_eval_reply {
  vector<string> log;
  ceph::bufferlist output;
};

void encode_eval_op(const cls_llvm_eval_op, ceph::bufferlist &);

#endif
