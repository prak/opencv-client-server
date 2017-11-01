import socket
import threading
import sys
import cv2
import pickle
import numpy as np
import struct
import time
import argparse

# Default camera
height = 480
width = 640
dimen = 3

class ThreadedServer(threading.Thread):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.clientnum = 0
        self.framearray = []

        print(host, port)

        # Don't lock up main thread.  Is there a better way to do this
        thread = threading.Thread(target=self.listen, args=())
        thread.daemon = True
        thread.start()
        return

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            # Likely not needed but I feel better preallocating memory
            self.framearray.append(np.zeros((height, width, dimen), np.uint8))
            t = threading.Thread(target = self.listenToClient, args = (client,address))
            t.start()
        return self

    def listenToClient(self, client, address):
        clientindex = self.clientnum
        # Add graceful way to deal with clients leaving later?
        self.clientnum += 1
        # Likely not needed but I feel better preallocating memory, yeah yeah I'm bad at python
        # But seriously, support tracking the loss of a client
        np.append(self.framearray, np.zeros((height, width, dimen), np.uint8))
        print("Client Listening, ", clientindex)
        size = 4096
        data = b''
        payload_size = struct.calcsize(">I")
        while True:
            while len(data) < payload_size:
                data += client.recv(4096)
            packed_msg_size = data[:payload_size]

            data = data[payload_size:]
            msg_size = struct.unpack(">I", packed_msg_size)[0]

            while len(data) < msg_size:
                data += client.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame=pickle.loads(frame_data)

            # Possible race condition
            self.framearray[clientindex] = frame

        return

    def getFrames(self, clientindex):
        # Possible race condition
        return self.framearray[clientindex]

    def maxClients(self):
        return self.clientnum

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", type=str, required=False, default='0.0.0.0')
    ap.add_argument("--port", type=int, required=False, default=8000)
    args = vars(ap.parse_args())

    HOST = args.get("host")
    PORT = args.get("port")

    serv = ThreadedServer(HOST, PORT)

    while True:
        clientnumber = 0
        while clientnumber < serv.maxClients():
#           print(clientnumber, serv.maxClients())
            frame = serv.getFrames(clientnumber)
            # Change later to support one frame per client
            cv2.imshow("Frame", frame)
            clientnumber += 1
#       I clearly don't know how to use cv2.waitKey() correctly
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # Something to stop server threads?
            break

    cv2.destroyAllWindows()
