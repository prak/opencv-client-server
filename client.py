import cv2
import numpy as np
import socket
import sys
import pickle
import struct
from threading import Thread
import argparse
# Not currently used; optimizations possible
# from multiprocessing import Process, Queue

#class CameraThread(threading.Thread):
class CameraThread():
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        (self.ret, self.frame) = self.cap.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.cap.release()
                return
            (self.ret, self.frame) = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

ap = argparse.ArgumentParser()
ap.add_argument("--host", type=str, required=True)
ap.add_argument("--port", type=int, required=False, default=8000)
args = vars(ap.parse_args())

HOST = args.get("host")
PORT = args.get("port")
print(HOST, PORT)

# Thread for video
vidstream = CameraThread(src=0)
vidstream.start()

# Network in main
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect((HOST, PORT))

while True:
    # Get frame from video thread
    frame = vidstream.read()

    # Displaying just for sanity check
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        vidstream.stop()
        break

    # Network write
    data = pickle.dumps(frame)
    # Currently just size and data, might need to support command information
    clientsocket.sendall(struct.pack(">I", len(data)) + data)

cv2.destroyAllWindows()
