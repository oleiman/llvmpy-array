#!/usr/bin/env python

import select 
import socket 
import sys 
import threading
from multiprocessing.managers import SyncManager
import pickle
import marshal
import types
import numpy as np

from ceph_array import CephArray

class Server: 
    def __init__(self): 
        self.host = '' 
        self.port = 50000 
        self.backlog = 5 
        self.size = 2**31 - 1
        self.server = None 
        self.threads = [] 

    def open_socket(self): 
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            self.server.bind((self.host,self.port)) 
            self.server.listen(5) 
        except socket.error, (value,message): 
            if self.server: 
                self.server.close() 
            print "Could not open socket: " + message 
            sys.exit(1) 

    def run(self): 
        self.open_socket() 
        input = [self.server,sys.stdin] 
        running = 1 
        while running: 
            inputready,outputready,exceptready = select.select(input,[],[]) 

            for s in inputready: 

                if s == self.server: 
                    # handle the server socket 
                    c = Client(self.server.accept()) 
                    c.start() 
                    self.threads.append(c) 

                elif s == sys.stdin: 
                    # handle standard input 
                    junk = sys.stdin.readline() 
                    running = 0 

        # close all threads 

        self.server.close() 
        for c in self.threads: 
            c.join() 

class Client(threading.Thread):
    clients = {}
    def __init__(self,(client,address)): 
        threading.Thread.__init__(self) 
        self.client = client 
        self.address = address
        self.requests = []
        self.methods = []
        self.size = 2**31 - 1
        Client.clients[address] = {}

    def run(self): 
        running = 1 
        while running: 
            data = self.client.recv(self.size)
            if data:
                manifest = pickle.loads(data)
                for req in manifest:
                    action = req[0]

                    if action == 'init':
                        oid = req[1]
                        dims = req[2]
                        
                        # TODO: keeping in mind that the numpy file *must* be
                        #       accessible from wherever the server is running
                        #       ** for now
                        arr = np.load(req[3]) if req[3] else None
                        if Client.clients[self.address].get(oid) is None:
                            Client.clients[self.address][oid] = CephArray(oid, dims, arr)

                    elif action == 'fold':
                        oid = req[1]
                        a = Client.clients[self.address][oid]
                        func = marshal.loads(req[2])
                        init = req[3]
                        name = req[4]
                        func = types.FunctionType(func, globals())
                        handle = a._gen_fold(CephArray.module, func, init, name)
                        self.requests.append([a.oid, handle])

                    elif action == 'write':
                        oid = req[1]
                        a = Client.clients[self.address][oid]
                        handle = a._gen_write(CephArray.module)
                        self.requests.append([a.oid, handle])

                    elif action == 'exec':
                        CephArray.module.verify()
                        irstr = str(CephArray.module)
                        responses = []
                        for req in self.requests:
                            responses.append(CephArray.cls_client.llvm_exec(irstr, req[0], req[1]))
                        self.client.send(pickle.dumps(responses))

            else: 
                self.client.close() 
                running = 0 

if __name__ == "__main__": 
    s = Server() 
    s.run()
