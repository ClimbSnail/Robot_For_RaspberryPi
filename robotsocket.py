# encoding: utf-8
import threading
import socket   # socket模块

class RobotSocket(object):

    def __init__(self, ip, port, callback_func = None, name="RobotSocket"):
        """
        RobotSocket类对象的初始化
        :param ip: 点分十进制的ip字符串
        :param port: 端口号整型数据(0-65535)
        :param recv_func: 接收处理函数
        :param name: socket实例名称
        """
        self.name = name
        self.__ip = ip
        self.__port = port
        self.__callback_func = callback_func
        self.__sersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 定义socket类型，网络通信，TCP
        self.__sersocket.bind((self.__ip, self.__port))  # 套接字绑定的IP与端口
        self.__sersocket.listen(1)  # 开始TCP监听
        self.connfd = None

    @property
    def callback_func(self):
        return self.__callback_func
    @callback_func.setter
    def callback_func(self, callback):
        self.__callback_func = callback

    def start(self):
        '''
        启动socket实例
        :return:
        '''
        def scanner():
            while True:
                self.connfd, addr = self.__sersocket.accept()  # 接受TCP连接，并返回新的套接字与IP地址
                print('Connected by', addr) # 输出客户端的IP地址
                run_thread = threading.Thread(target=self.clientrecv, args=(self.connfd, addr))
                run_thread.start()

        run_thread = threading.Thread(target=scanner, args=())
        run_thread.start()


    def clientrecv(self, connfd, addr):
        """
        客户端连接状态的数据处理
        :param connfd: 连接客户端的文件句柄
        :param addr: 客户端的地址
        :return: 
        """""
        try:
            while True:
                recv = connfd.recv(1024)  # 把接收的数据实例化
                if recv == b'': # 断开连接
                    break
                if self.callback_func != None:
                    self.callback_func(recv)
        except Exception as err:
            print(err)

    def clientsend(self, dat):
        """
        向本次连接的客户端发送数据
        :param dat: 要发送的数据（bytes类型）
        :return:
        """
        try:
            self.connfd.sendall(dat)
        except Exception as err:
            print(err)

    def close(self):
        try:
            self.connfd.close() # 关闭连接
            self.connfd = None
        except Exception as err:
            print(err)

    def __del__(self):
        try:
            self.connfd.close() # 关闭连接
            del self.connfd
            self.connfd = None
        except Exception as err:
            print(err)

if __name__ == "__main__":
    # This is demo
    def clientHandle(dat):  # 接收函数
        mysocket.clientsend(dat)
        dat = ("recv %s\n"%dat).encode(encoding="utf-8")
        print(dat)

    # 初始化端口并设置接收数据的函数(当接收到数据，自动被调用)
    mysocket = RobotSocket("192.168.123.135", 5555, clientHandle)
    mysocket.start()    # socket开始工作
    import time
    while True:
        time.sleep(1)
        mysocket.clientsend(b'running\n')