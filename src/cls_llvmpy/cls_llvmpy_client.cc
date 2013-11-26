#include "cls_llvmpy_client.hpp"
#include "cls_llvm_ops.hpp"
#include "rados/buffer.h"

using namespace std;
using namespace ceph;
using namespace librados;

#define STRIPE_SIZE 16777216

void CLSLLVMpyClient::init(const char *conf_file)
{
  
  char *id = getenv("CEPH_CLIENT_ID");
  if (id) std::cerr << "Client id is: " << id << std::endl;
  
  cluster = new librados::Rados();
  ioctx   = new librados::IoCtx();

  int ret;
  ret = cluster->init(id);
  if (ret) {
    cerr << "cluster->init failed with error " << ret << endl;
    return;
  }
  ret = cluster->conf_read_file(conf_file);
  if (ret) {
    cluster->shutdown();
    cerr << "cluster->conf_read_file failed with error " << ret << endl;
    return;
  }
  cluster->conf_parse_env(NULL);
  ret = cluster->connect();
  if (ret) {
    cluster->shutdown();
    cerr << "cluster->connect failed with error " << ret << endl;
    return;
  }
  cluster->ioctx_create("data", *ioctx);
}

CLSLLVMpyClient::CLSLLVMpyClient(const char *conf_file)
{
  init(conf_file);
  
}

CLSLLVMpyClient::~CLSLLVMpyClient()
{
  ioctx->close();
  cluster->shutdown();
  delete ioctx;
  delete cluster;
}

int 
CLSLLVMpyClient::cls_llvm_exec(const char *bc, boost::python::list arr,
                               string oid, string function)
{
  int ret;
  int len(boost::python::len(arr));
  int *vals = (int*) malloc(len * sizeof(int));
  int init = 0;

  cls_llvm_eval_op call;
  cls_llvm_eval_reply reply;

  bufferlist bitcode;
  bufferptr bcp(bc, strlen(bc));
  bitcode.push_back(bcp);
  call.bitcode = bitcode;

  call.function = function;

  for (int i = 0; i < len; ++i) {
    boost::python::extract<int> item(arr[i]);
    vals[i] = item;
    if (((i+1) * sizeof(int)) % STRIPE_SIZE == 0) {
      ret = pack_and_ship(oid, (char*) &(vals[init]), STRIPE_SIZE, call);
      init = i + 1;
    }
  }
  ret = pack_and_ship(oid, (char*) &(vals[init]), (len * sizeof(int)) % STRIPE_SIZE, call);
  
  return ret;
}

int CLSLLVMpyClient::pack_and_ship(const string& oid, char *vals, int size, cls_llvm_eval_op &call)
{

  bufferlist inbl, outbl, input;
  input.append(vals, size);

  call.input = input;
  encode_eval_op(call, inbl);
  
  return ioctx->exec(oid, "llvm", "eval", inbl, outbl);
}

BOOST_PYTHON_MODULE(llvm_client)
{
  using namespace boost::python;
  using namespace ceph;
  class_<CLSLLVMpyClient>("CLSLLVMpyClient", init<const char*>())
    .def("llvm_exec", &CLSLLVMpyClient::cls_llvm_exec);
}
