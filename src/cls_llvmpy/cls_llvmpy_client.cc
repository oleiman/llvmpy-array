#include <boost/python.hpp>
#include "cls_llvmpy_client.hpp"
#include "cls_llvm_ops.hpp"

using namespace std;
using namespace ceph;
using namespace librados;

CLSLLVMpyClient::CLSLLVMpyClient(const char *conf_file)
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

CLSLLVMpyClient::~CLSLLVMpyClient()
{
  ioctx->close();
  cluster->shutdown();
  delete ioctx;
  delete cluster;
}

int 
CLSLLVMpyClient::cls_llvm_exec(const char *bc, 
                               string oid, string function)
{
  int ret;
  bufferlist inbl, outbl, input;

  cls_llvm_eval_op call;
  cls_llvm_eval_reply reply;

  bufferlist bitcode;
  bufferptr bcp(bc, strlen(bc));
  bitcode.push_back(bcp);

  call.bitcode = bitcode;
  call.function = function;
  call.input = input;
  encode_eval_op(call, inbl);

  ret = ioctx->exec(oid, "llvm", "eval", inbl, outbl);
  
  return ret;
}

BOOST_PYTHON_MODULE(llvm_client)
{
  using namespace boost::python;
  class_<CLSLLVMpyClient>("CLSLLVMpyClient", init<const char*>())
    .def("llvm_exec", &CLSLLVMpyClient::cls_llvm_exec);
  
}
