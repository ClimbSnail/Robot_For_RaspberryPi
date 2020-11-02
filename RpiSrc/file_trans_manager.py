# encoding: utf-8
import os
import struct
import codecs
import random
from robotsocket import *


class FileTransManager(object):

    def __init__(self, ):
        self.ContexMaxNum = 256
        self.FileInfoDict = {}
        self.DataRear = b'\x00\xff\x00\xff\x00\xff\x00\xff\x00\xff\x00\xff'  # 帧尾
        # status 文件数据包的状态 DataHeader的第二字节
        self.STATUS_EDLE = b'\x00'  # 文件空闲状态
        self.STATUS_START = b'\x01'  # 文件传输的开始的标志(文件整体的信息)
        self.STATUS_NORMAL = b'\x02'  # 文件的传输
        self.STATUS_END = b'\x03'  # 文件的最后一包

        self.recvBuf = b''
        # 每次读取的包大小
        self.sendPacketMaxSize = 1024*128
        self.time1 = 0

    def deal_recv_data(self, recvDat):
        try:
            self.recvBuf = self.recvBuf + recvDat
            while True:
                nowDat = self.recvBuf.split(self.DataRear)
                if len(nowDat) < 2:
                    return None
                else:
                    nowDat = nowDat[0]
                    self.recvBuf = self.recvBuf[len(nowDat) + len(self.DataRear):]

                crn = nowDat[0].to_bytes(1, byteorder='little')
                status = nowDat[1].to_bytes(1, byteorder='little')
                useData = nowDat[2:]
                if status == self.STATUS_START:  # 判断是否是文件接收状态
                    filename, filesize = struct.unpack('128sl', useData)
                    filename = filename.strip(b'\00').decode()
                    fp = codecs.open("./recv_" + filename, 'wb')
                    self.FileInfoDict[crn] = {"fp": fp, "name": filename, "size": filesize}
                    self.time1 = time.time()
                elif crn in self.FileInfoDict.keys():
                    if status == self.STATUS_NORMAL:
                        self.FileInfoDict[crn]["fp"].write(useData)
                    elif status == self.STATUS_END:
                        self.FileInfoDict[crn]["fp"].close()
                        del self.FileInfoDict[crn]
                        print("File is recv finish.")
                        print(time.time() - self.time1)
        except Exception as err:
            print(err)

    def send_file(self, fileName, send_func, send_finish_func=None):
        # 创建发送任务
        run_thread = threading.Thread(target=create_send_task, args=(fileName, send_func, send_finish_func))
        run_thread.start()

    def create_send_task(self, fileName, send_func, send_finish_func=None):
        # 判断是否为文件
        if os.path.isfile(fileName):
            fp = codecs.open(fileName, "rb")
            crn = int(self.genCrn()).to_bytes(1, byteorder='little')
            # 定义文件头信息，包含文件名和文件大小
            fhead_info = struct.pack('128sl', os.path.basename(fileName).encode('utf-8'), os.stat(fileName).st_size)
            send_func(crn + self.STATUS_START + fhead_info + self.DataRear)
            while True:
                data = fp.read(self.sendPacketMaxSize)
                if data == None or data == b'':
                    send_func(crn + self.STATUS_END + self.DataRear)
                    if None != send_finish_func:
                        send_finish_func("succ")
                    print("Send succ.")
                    break
                else:
                    send_func(crn + self.STATUS_NORMAL + data + self.DataRear)

    def genCrn(self):
        crn = random.randint(0, self.ContexMaxNum - 1)
        while True:
            if len(self.FileInfoDict) == self.ContexMaxNum:
                return None
            if crn not in self.FileInfoDict.keys():
                return crn
            else:
                crn = (crn + 1) % self.ContexMaxNum

    def __del__(self):
        for keys in self.FileInfoDict.keys():
            self.FileInfoDict[keys]["fp"].close()
            del self.FileInfoDict[keys]


if __name__ == "__main__":
    # This is demo

    filemanager = FileTransManager()

    # 服务器端范例
    def mySerRecvHandle(dat, addr):  # 接收函数
        filemanager.deal_recv_data(dat)
        #dat = ("Server recv %s from %s\n" % (dat, addr)).encode(encoding="utf-8")
        #print(dat)

    # 初始化端口并设置接收数据的函数(当接收到数据，自动被调用)
    sersocket = RobotSocketServer("192.168.1.33", 5555, mySerRecvHandle, max_bind=10)
    sersocket.start()  # socket开始工作
    import time
    time.sleep(0.2)

    # 客户端范例
    def myClientRecvHandle(dat):  # 接收函数
        dat = ("Client recv %s\n" % dat).encode(encoding="utf-8")
        print(dat)

    # 初始化端口并设置接收数据的函数(当接收到数据，自动被调用)
    clientsocket = RobotSocketClient("192.168.1.33", 5555, myClientRecvHandle)
    clientsocket.start()    # socket开始工作

    filemanager.create_send_task("./MalhamStars.jpg", clientsocket.send_to_ser)