# python -u 启动，禁用stdout缓冲功能，不然打印有延时。

import RPi.GPIO as GPIO
from mylogger import *  # 导入日志库
# 导入读动作数据的库
from read_action import *
import serial
import time
import sys
import gc


def ByteToInt(recvH: bytes, recvL: bytes) -> int:
    """
    将串口收到的两个字节unsigned int数据转为python中的整型数
    :param recvH: 高8位
    :param recvL: 低8位
    :return: 整型数
    """
    valH = ord(recvH)
    res = (valH << 8) | ord(recvL)
    if valH > 127:
        res = -((~(res - 1)) & 0x7F)

    return res


class UART():
    order = {
        "停止": b'\x00\r\n', "关闭照明": b'\x01\r\n', "开启照明": b'\x02\r\n',
        "关闭红外": b'\x03\r\n', "开启红外": b'\x04\r\n', "动作初始化": b'\x05\r\n',
        "前进": b'\x06\r\n', "执行校准": b'\x08\r\n', "立正": b'\x09\r\n',
        "循环前进": b'\x0A\r\n', "循环后退": b'\x0B\r\n', "左转": b'\x0C\r\n',
        "右转": b'\x0E\r\n', "前滚翻": b'\x0F\r\n', "后滚翻 ": b'\x10\r\n',
        "俯卧撑": b'\x11\r\n', "仰卧起坐": b'\x12\r\n', "挥手": b'\x13\r\n',
        "鞠躬": b'\x14\r\n', "左侧滑": b'\x15\r\n', "右侧滑": b'\x16\r\n',
        "大鹏展翅": b'\x17\r\n', "蹲下": b'\x18\r\n', "开怀大大笑": b'\x19\r\n',
        "街舞": b'\x1A\r\n', "江南style舞蹈": b'\x1B\r\n', "小苹果舞蹈": b'\x1C\r\n',
        "La Song舞蹈": b'\x1D\r\n', "倍儿爽舞蹈": b'\x1E\r\n', "左右摇头": b'\x20\r\n',
        "体感功能关闭": b'\xFD\r\n', "体感功能打开": b'\xFE\r\n', "初始化并打开体感功能": b'\xFF\r\n'
    }

    def __init__(self, devName, BaudRate=115200):
        """
        串口初始化
        :param devName: 串口设备名称（具体路径）
        :param BaudRate: 波特率
        """
        self.BaudRate = BaudRate
        # 打开串口
        self.ser = serial.Serial(devName, self.BaudRate)

    def __del__(self):
        self.ser.close()

    def sendData(self, data):
        """
        发送指定数据
        :param data: 要发送的数据
        :return: None
        """
        self.ser.write(data)

    def run(self):
        """
        串口类运行及测试函数
        :return: None
        """
        while True:
            # 获得接收缓冲区字符	
            count = self.ser.inWaiting()
            if count != 0:
                # 读取内容并回显	
                recv = self.ser.read(count)
                self.sendData(recv)
            # ser.write(b"Debug1500")
            # 清空接收缓冲区	
            self.ser.flushInput()
            # 必要的软件延时	
            time.sleep(0.1)


class RPI_EXB(object):
    # 引脚定义
    POWER_EN_PIN = 16
    MOS1_EN_PIN = 38
    MOS2_EN_PIN = 40
    RGB_R_PIN = 37
    RGB_G_PIN = 35
    RGB_B_PIN = 33
    KeyOn = 13
    KeyUp = 15
    KeyDown = 31
    KeyLeft = 29
    KeyRight = 11

    # 按键状态
    KeyOn_Status = False
    KeyUp_Status = False
    KeyDown_Status = False
    KeyLeft_Status = False
    KeyRight_Status = False

    Freq = [10000, 10000, 10000]  # 其中freq是以Hz为单位的新频率
    DutyCycle = [0, 0, 0]  # where 0.0 <= dc <= 100.0

    ADC_Value = 0  # 电压采集
    ADC_scale = 6  # DC输入端电压与采集的ADC的比值
    ADC_Error = 0.0194  # 电压误差
    ADC_threshold = 8  # 电压报警的阈值

    UartBaudrate = 115200  # 串口特率

    def __init__(self, devName="/dev/ttyAMA0", baudrate=UartBaudrate):
        """
        拓展板初始化
        :param devName: 串口设备名称（具体路径）
        :param baudrate: 波特率
        """
        # BOARD编号方式，基于插座引脚编号
        GPIO.setmode(GPIO.BOARD)  # or	GPIO.setmode(GPIO.BCM)

        # Key Setting
        KeyList = [RPI_EXB.KeyOn, RPI_EXB.KeyUp, RPI_EXB.KeyDown, RPI_EXB.KeyLeft, RPI_EXB.KeyRight]
        GPIO.setup(KeyList, GPIO.IN)  # 设置为输入模式

        # POWER输出设置
        GPIO.setup(RPI_EXB.POWER_EN_PIN, GPIO.OUT)
        GPIO.output(RPI_EXB.POWER_EN_PIN, GPIO.HIGH)

        # MOS控制引脚设定
        MosList = [RPI_EXB.MOS1_EN_PIN, RPI_EXB.MOS2_EN_PIN]
        GPIO.setup(MosList, GPIO.OUT)
        GPIO.output(MosList, GPIO.HIGH)

        # RGB(PWM) Setting
        RGBList = [RPI_EXB.RGB_R_PIN, RPI_EXB.RGB_G_PIN, RPI_EXB.RGB_B_PIN]
        GPIO.setup(RGBList, GPIO.OUT)
        RPI_EXB.RGB_R = GPIO.PWM(RPI_EXB.RGB_R_PIN, RPI_EXB.Freq[0])  # 其中Freq是以Hz为单位的新频率
        RPI_EXB.RGB_G = GPIO.PWM(RPI_EXB.RGB_G_PIN, RPI_EXB.Freq[1])
        RPI_EXB.RGB_B = GPIO.PWM(RPI_EXB.RGB_B_PIN, RPI_EXB.Freq[2])
        RPI_EXB.RGB_R.start(100 - RPI_EXB.DutyCycle[0])  # where 0.0 <= dc <= 100.0
        RPI_EXB.RGB_G.start(100 - RPI_EXB.DutyCycle[1])
        RPI_EXB.RGB_B.start(100 - RPI_EXB.DutyCycle[2])

        # 定义一个串口对象
        RPI_EXB.uart = UART(devName=devName, BaudRate=baudrate)

    def RGB(self, Duty=DutyCycle, RGB_Fre=Freq):
        """
        RGB控制函数
        :param Duty: 占空比
        :param RGB_Fre: 频率
        :return: None
        """
        # 保存设置数据到类变量中
        RPI_EXB.DutyCycle = [100 - value for value in Duty]
        RPI_EXB.Freq = RGB_Fre
        # 设置PWM
        RPI_EXB.RGB_R.ChangeFrequency(RGB_Fre[0])  # 其中Freq是以Hz为单位的新频率
        RPI_EXB.RGB_G.ChangeFrequency(RGB_Fre[1])
        RPI_EXB.RGB_B.ChangeFrequency(RGB_Fre[2])
        RPI_EXB.RGB_R.ChangeDutyCycle(RPI_EXB.DutyCycle[0])  # where 0.0 <= dc <= 100.0
        RPI_EXB.RGB_G.ChangeDutyCycle(RPI_EXB.DutyCycle[1])  # where 0.0 <= dc <= 100.0
        RPI_EXB.RGB_B.ChangeDutyCycle(RPI_EXB.DutyCycle[2])  # where 0.0 <= dc <= 100.0

    def POWER(self, stat):
        """
        控制Mos电路开关
        :param stat: 状态
        :return: None
        """
        if stat == "open":
            GPIO.output(RPI_EXB.POWER_EN_PIN, GPIO.LOW)
        elif stat == "close":
            GPIO.output(RPI_EXB.POWER_EN_PIN, GPIO.HIGH)
        else:
            print("Warning: Parameter Error POWER\n")

    def MOS(self, status=["close", "close"]):
        """
        控制两路小mos电路开关
        :param status: 两路mos管的状态列表
        :return: None
        """
        if status[0] == "open":
            GPIO.output(RPI_EXB.MOS1_EN_PIN, GPIO.LOW)
        elif status[0] == "close":
            GPIO.output(RPI_EXB.MOS1_EN_PIN, GPIO.HIGH)
        else:
            print("Warning: Parameter Error MOS1\n")

        if status[1] == "open":
            GPIO.output(RPI_EXB.MOS2_EN_PIN, GPIO.LOW)
        elif status[1] == "close":
            GPIO.output(RPI_EXB.MOS2_EN_PIN, GPIO.HIGH)
        else:
            print("Warning: Parameter Error MOS2\n")

    def GetADC(self):
        """
        读取拓展版电压
        :return: 电压的物理值 单位V
        """
        # 向转接板查询ADC值
        RPI_EXB.uart.sendData(b'ADC?\r\n');
        # 必要的软件延时
        time.sleep(0.05)
        # 获得接收缓冲区字符	
        count = RPI_EXB.uart.ser.inWaiting()
        # print(count)
        if count != 0:
            # 读取内容并回显	
            value = RPI_EXB.uart.ser.read(count)
            RPI_EXB.ADC_Value = (value[4] * 256 + value[5]) / 4096 * 3.32
        # 清空接收缓冲区	
        RPI_EXB.uart.ser.flushInput()

        return (RPI_EXB.ADC_Value - RPI_EXB.ADC_Error) * RPI_EXB.ADC_scale

    def SetKeyHandler(self, ):
        """
        按键检测
        :return: None
        """

        def PressOn(self, ):
            RPI_EXB.KeyOn_Status = True
            print("\nPressOn\n")

        def PressUp(self, ):
            RPI_EXB.KeyUp_Status = True
            print("\nPressUp\n")

        def PressDown(self, ):
            RPI_EXB.KeyDown_Status = True
            print("\nPressDown\n")

        def PressLeft(self, ):
            RPI_EXB.KeyLeft_Status = True
            print("\nPressLeft\n")

        def PressRight(self, ):
            RPI_EXB.KeyRight_Status = True
            print("\nPressRight\n")

        # Key Setting
        # 按键消抖延时
        key_delay_ms = 200
        KeyList = [RPI_EXB.KeyOn, RPI_EXB.KeyUp, RPI_EXB.KeyDown, RPI_EXB.KeyLeft, RPI_EXB.KeyRight]
        # GPIO.add_event_detect(RPI_EXB.KeyOn, GPIO.RISING, callback=led_on, bouncetime=20)
        GPIO.add_event_detect(RPI_EXB.KeyOn, GPIO.FALLING, callback=PressOn, bouncetime=key_delay_ms)
        GPIO.add_event_detect(RPI_EXB.KeyUp, GPIO.FALLING, callback=PressUp, bouncetime=key_delay_ms)
        GPIO.add_event_detect(RPI_EXB.KeyDown, GPIO.FALLING, callback=PressDown, bouncetime=key_delay_ms)
        GPIO.add_event_detect(RPI_EXB.KeyLeft, GPIO.FALLING, callback=PressLeft, bouncetime=key_delay_ms)
        GPIO.add_event_detect(RPI_EXB.KeyRight, GPIO.FALLING, callback=PressRight, bouncetime=key_delay_ms)

    def PwmCtrl(self, actionData):
        """
        控制拓展板上的三路pwm舵机，将数据从通信串口发出
        :param actionData: 动作数据
        :return: None
        """
        RPI_EXB.uart.sendData(actionData)

    def BusCtrl(self, actionData):
        """
        控制拓展板上的总线舵机，将数据从通信串口发出
        :param actionData: 动作数据
        :return: None
        """
        # 拓展板对应的数据转发帧头b'U2T'	 拓展板对应的数据转发帧尾为b'\r\n'
        RPI_EXB.uart.sendData(b'U2T' + actionData + b'\r\n')

    def __del__(self):
        self.POWER("close")
        self.MOS(["close", "close"])
        GPIO.cleanup()  # 释放引脚
        print("A object of RPI_EXB was delete.")


if __name__ == '__main__':

    IOCtrler = RPI_EXB(devName="/dev/ttyAMA0", baudrate=115200)
    IOCtrler.RGB(Duty=[50, 60, 0])
    IOCtrler.POWER("open")

    # 对应型号总线舵机通电一定时间后 自身才完成初始化,所以需要延时后再送数据
    time.sleep(0.05)

    LeA = LeServo()

    arrNum = [2, 3]
    posNum = 0
    # 开启按键检测 其他程序可随时查询5个按键的状态
    IOCtrler.SetKeyHandler()

    while True:
        # 通过动作编号读取动作组的动作数据
        arrs, res = LeA.readActionArr(actionNum=arrNum[posNum])
        # 通过动作名读取动作组的动作数据
        # arrs, res = LeA.readActionArr(actionName = "蹲下")
        posNum = int((posNum + 1) % len(arrNum))
        if res["flag"] == False:
            print(res["errorInfo"])
        else:
            print(arrs)
            # 遍历此动作组
            for arr in arrs:
                BusStr = LeA.arrToStr_b(arr["data"], arr["runtime"])
                # print( BusStr ,end = "\n")
                IOCtrler.BusCtrl(BusStr)
                time.sleep(arr["runtime"] / 1000 + 0.1)

        # 获取电压值
        adc = IOCtrler.GetADC()
        print("电压的值为: " + str(adc))
        print(str(IOCtrler.KeyOn_Status))
        time.sleep(0.05)

    del IOCtrler
    gc.collect()  # 显式进⾏垃圾回收， 可以输⼊参数
    '''
    IOCtrler.PwmCtrl(b'U2T\x55\x55\x01\x07\x01\xFE\x01\xE8\x03\x0C\r\n' )
    time.sleep(0.05)
    IOCtrler.PwmCtrl(b'D3 2500 2500 1500 1000ms 500 500 1500 1000ms 1500 1500 1500 200ms\r\n' )
    time.sleep(0.3)
    IOCtrler.PwmCtrl(b'U2T\x55\x55\x01\x07\x01\xFE\x01\xE8\x03\x0C\r\n' )
    time.sleep(0.2)
    '''
