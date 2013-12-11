from llvm.core import *

import rados
import struct
import socket
import pickle
import marshal

import numpy as np

# TODO: write some comments

class CephArray:
    manifest = []
    ceph_config = '/home/oren/code/ceph-private/src/ceph.conf'

    def __init__(self, oid, filename = None):
        self.oid = oid
        self._from_file(filename) if filename else self._no_file()

    @classmethod
    def config(cls, config_file, pool_name='data'):
        cls.ceph_config = config_file
        cluster = rados.Rados(conffile=cls.ceph_config)
        cluster.connect()
        if not cluster.pool_exists(pool_name):
            cluster.create_pool(pool_name)
        cluster.shutdown()
        cls.pool_name = pool_name

    @classmethod
    def execute(cls):
        host = 'localhost'
        port = 50000
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host,port))
        size = 2**31 - 1
        cls.manifest.append({'action':'exec'})
        s.send(pickle.dumps(cls.manifest))
        data = pickle.loads(s.recv(size))
        s.close()
        cls.manifest = []
        return data

    # TODO: smooth out the dims getting, which is now unnecessary client-side
    def _from_file(self, filename):
        dims = np.load(filename).shape
        CephArray.manifest.append({
                'action': 'init', 
                'oid': self.oid, 
                'dims': dims, 
                'file': filename
                })
        
    def _no_file(self):
        dims = self._get_dims()
        CephArray.manifest.append({
                'action': 'init', 
                'oid': self.oid, 
                'dims': dims, 
                })

    def _get_dims(self):
        cluster = rados.Rados(conffile=CephArray.ceph_config)
        cluster.connect()
        ioctx = cluster.open_ioctx(CephArray.pool_name)
        dim_dict = {}
        dims = []
        
        try:
            for attr in ioctx.get_xattrs(self.oid):
                dim_dict[attr[0]] = struct.unpack('<L', attr[1])[0]
        except:
            raise LookupError("Object [%s] not found" % self.oid)

        for idx,v in enumerate(dim_dict.items()):
            k = "d%d" % idx
            dims.append(dim_dict[k])

        ioctx.close()
        cluster.shutdown()
        return tuple(dims)

    def fold(self, f, init):
        func_string = marshal.dumps(f.func_code)
        CephArray.manifest.append({
                'action': 'fold', 
                'oid': self.oid, 
                'func': func_string, 
                'init': init, 
                })
        
    def write(self):
        try:
            self._get_dims()
        except:
            CephArray.manifest.append({
                    'action': 'write', 
                    'oid': self.oid
                    })
