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
import time

from code_gen import ArrayCodeGen

class ArrayServer: 
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
                    action = req.get('action')
                    oid = req.get('oid')

                    if action == 'init':
                        dims = req.get('dims')
                        fname = req.get('file')

                        # TODO: keeping in mind that the numpy file *must* be
                        #       accessible from wherever the server is running
                        #       ** for now
                        arr = np.load(fname) if fname else None
                        if Client.clients[self.address].get(oid) is None:
                            Client.clients[self.address][oid] = ArrayCodeGen(oid, dims, arr)
 
                    elif action == 'fold':
                        a = Client.clients[self.address][oid]
                        func_code = marshal.loads(req.get('func'))
                        func = types.FunctionType(func_code, globals())
                        name = func.__name__
                        init = req.get('init')
                        handle = a._gen_fold(func, init, name)
                        self.requests.append((a.oid, handle))

                    elif action == 'write':
                        a = Client.clients[self.address][oid]
                        handle = a._gen_write()
                        self.requests.append((a.oid, handle))

                    elif action == 'exec':
                        irstr = ArrayCodeGen.link(Client.clients[self.address])
                        responses = []
                        for req in self.requests:
                            oid = req[0]
                            func = req[1]
                            a = Client.clients[self.address][oid]
                            data = a.flatten()
                            val = ArrayCodeGen.cls_client.llvm_exec(irstr, data, oid, func)
                            responses.append({
                                    'oid': oid,
                                    'called': func, 
                                    'return': val, 
                                    'timestamp': time.ctime()
                                    })
                        self.client.send(pickle.dumps(responses))

            else: 
                self.client.close() 
                running = 0 

if __name__ == "__main__": 
    s = ArrayServer() 
    s.run()
