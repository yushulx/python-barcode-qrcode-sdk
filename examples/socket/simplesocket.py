import socket
import selectors

'''
+-+-+-+-+-------+-+-------------+-------------------------------+
|Type (1 byte)                  |   Payload length (4 bytes)    |
|0: text, 1: json 2: webp       |                               |
+-------------------------------+-------------------------------+
|                           Payload Data                        |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
'''
class DataType():
        TEXT = b'0'
        JSON = b'1'
        WEBP = b'2'
        
class SimpleSocket():
    def __init__(self) -> None:
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.callback = None
        
    def registerEventCb(self, callback):
        self.callback = callback
    
    def startClient(self, address, port):
        self.sock.setblocking(False)
        self.sock.connect_ex((address, port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.sock, events, data=self.callback)
        
    def startServer(self, port, number_of_clients=1):
        self.sock.bind(('', port))
        self.sock.listen(number_of_clients)
        print('waiting for a connection at port %s' % port)
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, data=None)
    
    def monitorEvents(self):
        events = self.sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                self.acceptConn(key.fileobj, self.callback)
            else:
                self.serveConn(key, mask)
    
    def acceptConn(self, sock, callback):
        connection, addr = sock.accept()
        print('Connected to %s' % addr[0])
        connection.setblocking(True)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(connection, events, data=callback)
        
    def serveConn(self, key, mask):
        sock = key.fileobj
        callback = key.data
        if callback != None and len(callback) == 2:
            if mask & selectors.EVENT_READ:
                data_type, data = self.receiveData(sock)
                callback[0](data_type, data)
            if mask & selectors.EVENT_WRITE:
                data_type, data = callback[1]()
                if data_type != None and data != None:
                    self.sendData(sock, data_type, data)
      
    def shutdown(self):
        self.sel.unregister(self.sock)
        self.sock.close()
        self.sel.close()
                      
    def disconnect(self, sock):
        self.sel.unregister(sock)
        sock.close()
    
    def sendData(self, sock, data_type, data):
        msg = data_type + len(data).to_bytes(4, 'big') + data
        return self.send(sock, msg)
    
    def receiveData(self, sock):
        data_type = self.receive(sock, 1)
        if data_type == b'':
            return b'', b''
        data_length = self.receive(sock, 4)
        if data_length == b'':
            return b'', b''
        data = self.receive(sock, int.from_bytes(data_length, 'big'))
        return data_type, data

    def send(self, sock, msg):
        try:
            totalsent = 0
            while totalsent < len(msg):
                sent = sock.send(msg[totalsent:])
                if sent == 0:
                    # connection closed
                    return False
                
                totalsent = totalsent + sent
        except Exception as e:
            print(e)
            return False
            
        return True
    
    def receive(self, sock, size):
        try:
            chunks = []
            bytes_recd = 0
            while bytes_recd < size:
                chunk = sock.recv(min(size, 1024))
                if chunk == b'':
                    # connection closed
                    return b''
                
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
                    
        except Exception as e:
            print(e)
            return b''
        
        return b''.join(chunks)
    

