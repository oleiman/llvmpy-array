#include "cls_llvm_ops.hpp"

using namespace std;

void encode_eval_op(const cls_llvm_eval_op call, ceph::bufferlist &bl)
{
  // encode by hand because why the hell not
  uint32_t bc_len = call.bitcode.length();
  uint32_t fn_len = call.function.length();
  uint32_t in_len = call.input.length();
  uint8_t struct_v = 1;
  uint8_t struct_compat = 1;
  uint32_t struct_len = 0;

  // open struct
  bl.append((char*) &struct_v, sizeof(struct_v));
  bl.append((char*) &struct_compat, sizeof(struct_compat));
  bl.append((char*) &struct_len, sizeof(struct_len));
  ceph::bufferlist::iterator struct_len_it = bl.end();
  struct_len_it.advance(-4);  

  // the actual data
  bl.append((char*) &bc_len, sizeof(bc_len));
  bl.append(call.bitcode);
  bl.append((char*) &fn_len, sizeof(fn_len));
  bl.append(call.function.data(), fn_len);
  bl.append((char*) &in_len, sizeof(in_len));
  bl.append(call.input);
  
  // close struct
  struct_len = bl.length() - struct_len_it.get_off() - sizeof(struct_len);
  struct_len_it.copy_in(4, (char *)&struct_len);
}
