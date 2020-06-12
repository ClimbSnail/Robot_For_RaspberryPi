# encoding: utf-8

#	本程序为机器人的主程序  各个二级py程序中
#	例如语音识别、图像识别、图灵机器人
import os
import sys
import time
import json
import signal  # 导入信号量模块
import requests
import threading  # 导入线程库
import snowboydecoder	# 使用snowboy离线唤醒
from platform import system
from GPIO import *		# 导入拓展版的类库
from read_action import *		# 导入读动作数据的库
from baidu_speak import *
from turing_robot import *
from face_recognition import *
from config import ConfigManager
from multiprocessing import Process, Queue, Value, Lock, Manager  # 多进程库 队列 pip install multiprocessing

# import commands  # 执行系统命令模块
# getstatusoutput执行系统命令（即shell命令），返回两个结果，第一个是状态，成功则为0，第二个是执行成功或失败的输出信息
# cmd_status, cmd_result = commands.getstatusoutput(data)


"""
# 不繁忙信号的回调
def noPlayBusy(signum):
	global playBusy
	playBusy = False


# 繁忙信号的回调
def playBusy(signum):
	global playBusy
	playBusy = True


#   注册信号回调
signal.signal(signal.SIGTSTP, noPlayBusy)
#   注册信号回调
signal.signal(signal.SIGCONT, playBusy)

"""

stream = None
Running = False
bytes = b''

# 相机对象
capture = None

order_V = {
	"人脸识别": "fd",
	"图像识别":"fd",
	"关闭摄像头": "guanbi",
	"训练模型":"tm",
	"加载模型":"im",
	"获取训练数据":"fde",
}

noSpeakJson = [
	"小杰小杰",
	"初始化体感",
	"人脸识别",
	"图像识别",
	"关闭摄像头",
	"训练模型",
	"加载模型",
	"获取训练数据",
	"晚安",
]

# 暂时不用了
actionOrder = [
		"停止",	"关闭照明",	"开启照明",
		"关闭红外",	"开启红外",	"动作初始化",
		"前进",	"执行校准",	"立正",
		"循环前进",	"循环后退",	"左转",
		"右转",	"前滚翻",	"后滚翻 ",
		"俯卧撑",	"仰卧起坐",	"挥手",
		"鞠躬",	"左侧滑",	"右侧滑",
		"大鹏展翅",	"蹲下",	"开怀大大笑",
		"街舞",	"江南style舞蹈",	"小苹果舞蹈",
		"La Song舞蹈",	"倍儿爽舞蹈",	"左右摇头",
		"体感功能关闭",	"体感功能打开",	"初始化并打开体感功能"
		]	

# 播放器
def Player(q, d):
	play = Play(system = d["system"])
	while True:
		info = q.get()
		play.playMusic(info)
		while q.empty() != True:
			q.get()
		# print( q.qsize() )
		time.sleep(0.3)

		
# 秒计数器
def timerCnt(d ):
	while True:
		if d["awakeUpCnt"] > 0:
			d["awakeUpCnt"] -= 1	#语音交互计数值
		time.sleep(1)
		
		
interrupted = False


# 控制拓展版的动作线程
def Action(q, d):
	IOCtrler = RPI_EXB(devName = "/dev/ttyAMA0", baudrate = 115200)
	IOCtrler.RGB( Duty = [50,60,0] )
	IOCtrler.POWER("open")
	# 对应型号总线舵机通电一定时间后 自身才完成初始化,所以需要延时后再送数据
	time.sleep(0.05)
	LeA = LeServo()
	arrNum = [1, 3]
	posNum = 0
	# 电压查询计数器
	BatteryCnt = 0
	while True:
		if d["RobotOrder"] != "":
			print( d["RobotOrder"] )
			# arrs, res = LeA.readActionArr(actionNum = arrNum[posNum])
			# 通过动作名读取动作组的动作数据
			arrs, res = LeA.readActionArr(actionName = d["RobotOrder"])
			posNum = int((posNum+1)%len(arrNum))
			if res["flag"] == False:
				print(res["errorInfo"])
			else:
				print(arrs)
				# 遍历此动作组
				for arr in arrs:
					BusStr = LeA.arrToStr_b(arr["data"],arr["runtime"])
					#print( BusStr ,end = "\n")
					IOCtrler.BusCtrl( BusStr )
					time.sleep( arr["runtime"]/1000+0.1 )
			d["RobotOrder"] = ""
		else:
			time.sleep(0.2)
		
		# 获取电压值
		adc = IOCtrler.GetADC()
		print("电压的值为: "+str(adc) )
		if BatteryCnt<1 and adc<IOCtrler.ADC_threshold:
			print("电压的值为: "+str(adc) )
			# 电量不足
			q.put("./resources/InsufficientElectricity.mp3")
			# 已关闭电机供电
			# q.put("./resources/CloseBattery.mp3")
			# 休眠 让语音播放完
			time.sleep(2)
			BatteryCnt = 100
		# 电量查询计数器
		if BatteryCnt<1:
			BatteryCnt = 0
		else:
			BatteryCnt -= 1
		time.sleep(0.05)

# 语音唤醒进程
def VoiceAwakeUp(q, d ):

	def signal_handler(signal, frame):
		global interrupted
		interrupted = True

	def interrupt_callback():
		global interrupted
		return interrupted
	# 启动秒计数器
	Cnt = threading.Thread(target=timerCnt, args=(d, ) ) 
	Cnt.start()  # 启动所有线程对象
	# Cnt.join()  # 将会阻塞主进程的运行,直到子线程运行完
	
	models, modelNames = snowboydecoder.readModel("./resources")
	# capture SIGINT signal, e.g., Ctrl+C
	signal.signal(signal.SIGINT, signal_handler)

	sensitivity = [0.5]*len(models)
	detector = snowboydecoder.HotwordDetector(models, modelNames=modelNames, sensitivity=sensitivity)

	callbacks = [lambda: snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING) for i in range(len(models)) ]

	print('Listening... Press Ctrl+C to exit')
	# main loop
	# make sure you have the same numbers of callbacks and models
	detector.start(detected_callback=callbacks,
				   interrupt_check=interrupt_callback,
				   sleep_time=0.03, d=d, q=q)

	# detector.terminate()

# 语音交互
def Voice(q, d):

	global order_V
	global noSpeakJson

	# 定义一个图灵机器人对话对象
	TR = TuringRobot("填写你的图灵apikey")
	# 获取一个百度语音对象
	baidu = BaiduSpeak(APP_ID, API_KEY, SECRET_KEY, )

	while True:
		if d["awakeUpCnt"] > 6:
			q.put("./BaiduSpeak/qingshuo.mp3")
			time.sleep(1.5)
			# 录音4s
			baidu.luYin(4)
			# 语音识别
			ret = baidu.getText()
			# result字段返回的时1-5个候选结果 string类型 utf-8编码

			if ret["err_msg"] == "success.":
				ask_text = ret["result"][0]  # 获取识别出来的结果
				d["awakeUpCnt"] = 20	# 定时计数器清零
				# 将数据传输一份给动作线程
				d["RobotOrder"] = ask_text
				# 判断是否在不回答的内容列表里
				if ask_text in noSpeakJson:
					d["faceOrder"] = order_V[ask_text]
					print( "Voice: "+ask_text+"  "+ order_V[ask_text] )
				# 判断是否在动作数据里
				# elif ask_text in actionOrder:
				#	d["RobotOrder"] = ask_text
						
				else:
					req = TR.getTalk(ask_text)["results"][0]["values"]["text"]  # 获取回答
					print('你: %s' % ask_text)
					print('Turing的回答：%s' % req)
					# 语音合成
					path = baidu.getAudio(req)
					q.put(path)
					# 休眠 让语音播放完
					time.sleep(3)
			else:
				print(ret["err_msg"])
		else:
			time.sleep(0.5)
			# 将设置的信息保存到配置文件中
			baidu.confWrite()

def Face(q, d):

	global order_V
	
	system = d["system"]
	
	# 判断系统类型  linux 与 windows
	if system == "windows":
		os.system("title FaceRecognition")

	# 定义图像来源 Camera 与 MJPEG_Stream, windows上建议参数 Camera
	if d["Image_Source"] == "MJPEG_Stream":
		#	Image_Source 选用 MJPEG_Stream 方式
		cv_continue()
		# MJPEG_Stream图像更新线程
	th1 = threading.Thread(target=get_image, args=(d["Image_Source"], d))
	th1.setDaemon(True)  # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
	th1.start()

	# 获取一个人脸识别的对象
	F = FaceRecognition(fr_name="MyFace", system=system)

	# 获取一个百度语音对象
	baidu = BaiduSpeak()

	# 当前输入的模型名称(等效于标签)
	ModelName = "heqi"
	# 尝试加载模型对象
	modelLoad = F.initModel(modelPath=F.modelPath, modelName="%s_FaceData.xml" % ModelName)  # 初始化相关的检测器和模型检测器

	# 如果模型没加载成功 说明模型文件有问题
	if modelLoad == False:
		# 尝试重新通过训练数据得到模型
		modelReady = F.trainingModel(F.imageSavePath, F.modelPath, "%s_FaceData.xml" % ModelName)
		if modelReady == False:
			isFinish = False	# 完成标志位
			while isFinish == False:
				if d["ret"] == False:
					break
				isFinish = F.faceDataExtraction(d["frame"], F.imageSavePath + "/heqi", ".jpg")
				c = cv.waitKey(20)  # 等待操作
				if c == 27:  # 如果按看下esc按键
					break
				time.sleep(0.3)
			# 重新尝试训练模型
			F.trainingModel(F.imageSavePath, F.modelPath, "%s_FaceData.xml" % ModelName)

		# 重新初始化相关的检测器和模型检测器
		F.initModel(modelPath=F.modelPath, modelName="%s_FaceData.xml" % ModelName)

	while True:
		while d["faceOrder"] == "":	# 等待指令不为空
			time.sleep(0.3)
		# 获取指令的共享变量
		faceOrder = str(d["faceOrder"])
		
		if faceOrder == "fd":
			count = 50
			while count >0 :
				while d["ret"] == False:
					pass
				count -= 1
				d["ret"] = False
				frame = d["frame"]
				frame = cv.flip(frame, 1)  # 左右图像对换
				#frame = cv.resize(frame, (120, 90))  # 将兴趣域size为150 * 150
				#cv.imshow('Capture',frame)
				# 获取人脸检查与识别的结果
				info = F.face_decete(frame)
				# 人脸检查与识别的结果不为空
				if info != None:
					print(info)
					path = baidu.getAudio(info)
					q.put(path)
				c = cv.waitKey(20)  # 等待操作
				if c == 27:  # 如果按看下esc按键
					break
				time.sleep(0.03)
			d["faceOrder"] = ""	# 指令清空

		if faceOrder == "im":
			# 尝试加载模型对象
			# 初始化相关的检测器和模型检测器
			modelLoad = F.initModel(modelPath=F.modelPath, modelName="%s_FaceData.xml" % ModelName)
			if modelLoad == True:
				path = baidu.getAudio(modelLoad)
			else:
				path = baidu.getAudio(modelLoad)
			q.put(path)
			d["faceOrder"] = ""	# 指令清空

		if faceOrder == "tm":
			# 重新尝试训练模型
			modelReady = F.trainingModel(F.imageSavePath, F.modelPath, "%s_FaceData.xml" % ModelName)
			if modelReady == True:
				path = baidu.getAudio(modelLoad)
			else:
				path = baidu.getAudio(modelLoad)
			q.put(path)
			d["faceOrder"] = ""	# 指令清空

		if faceOrder == "fde":	# 获取训练数据
			isFinish = False	# 完成标志位
			while isFinish == False:
				while d["ret"]==False:
					pass
				frame = d["frame"]
				d["ret"] = False
				isFinish = F.faceDataExtraction(frame, F.imageSavePath + "/heqi", ".jpg")
				time.sleep(0.3)
			d["faceOrder"] = ""	# 指令清空

	if d["Image_Source"] == "Camera":
		capture.release()  # 释放摄像头资源
	cv.destroyAllWindows()  # 释放窗口资源


# 继续信号的回调
def cv_continue():
	global stream
	global Running
	global bytes
	if Running is False:
		# 开关一下连接
		if stream:
			stream.close()
		stream = urllib.request.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
		bytes = b''
		Running = True


def get_image(image_src, share):
	"""
	image_src定义图像来源 Camera 与 MJPEG_Stream, windows上建议参数Camera
	:param image_src: 图像来源
	:param share: 多进程多线程的共享变量
	:return:
	"""
	global Running
	global orgframe, minframe
	global capture	  # 摄像头对象
	global bytes
	if image_src == "Camera":
		capture = cv.VideoCapture(0)  # 获取摄像头对象
		capture.set(3, 720)  # 设置分辨率
		capture.set(4, 480)
	while True:
		if Running and image_src == "MJPEG_Stream":
			try:
				bytes += stream.read(2048)  # 接收数据
				a = bytes.find(b'\xff\xd8')  # 找到帧头
				b = bytes.find(b'\xff\xd9')  # 找到帧尾
				if a != -1 and b != -1:
					jpg = bytes[a:b + 2]  # 取出图片数据
					bytes = bytes[b + 2:]  # 去除已经取出的数据
					orgframe = cv.imdecode(np.fromstring(jpg, dtype=np.uint8), cv.IMREAD_COLOR)  # 对图片进行解码
					minframe = cv.resize(orgframe, (720, 480), interpolation=cv.INTER_LINEAR)  # 将图片缩放到 320*240
					share["frame"] = minframe
					share["ret"] = True
			except Exception as e:
				print(e)
				continue
		elif Image_Source == "Camera" and capture.isOpened():
			ret, frame = capture.read()  # 读取摄像头图像数据
			share["frame"] = frame
			share["ret"] = ret
			time.sleep(0.03)
			key = cv.waitKey(50)  # 等待操作
			if key & 0x00FF == ord('q'):  # 按下ESC
				break  # 释放资源和关闭窗口
		else:
			time.sleep(0.01)


# 主函数
if __name__ == "__main__":

	# This is a example
	print("This platform is " + system().lower())
	# 启动模式 thread:多线程	process:多进程
	model = "process"
	cfg = ConfigManager("default.cfg")
	# 多线程模式
	if model == "thread":
		os.system("title Robat")
		# 父进程创建Queue，并传给各个子进程 共享播放声音使用
		q = Queue()
		d_share = dict()
		d_share["faceOrder"] = ""
		d_share["frame"] = None
		d_share["ret"] = False
		# 定义系统类型  linux 与 windows
		d_share["system"] = system().lower()
		# 定义图像来源 Camera 与 MJPEG_Stream, windows上建议参数Camera
		d_share["Image_Source"] = "Camera"
		d_share["Voice_EN"] = True	#语音交互使能标志位
		d_share["awakeUpCnt"] = 0	#语音交互计数值
		d_share["RobotOrder"] = ""	# 判断机器人控制信号
		d_share["cfg"] = cfg	# 配置文件
		thread_object = []
		# 语音交互线程
		thread_object.append(threading.Thread(target=Voice, args=(q, d_share) ))
		# 摄像头线程
		thread_object.append(threading.Thread(target=Face, args=(q, d_share) ))
		# 播放器线程
		thread_object.append(threading.Thread(target=Player, args=(q, d_share) ) )
		# 离线语音唤醒线程
		thread_object.append(threading.Thread(target=VoiceAwakeUp, args=(q, d_share, ) ) )
		# 机器人控制线程
		thread_object.append(threading.Thread(target=Action, args=(q, d_share) ) )
		
		for i in range(0, len(thread_object), 1):
			thread_object[i].start()  # 启动所有线程对象
		for i in range(0, len(thread_object), 1):
			thread_object[i].join()  # 将会阻塞主进程的运行,直到子线程运行完

	# 多进程模式
	if model == "process":
		# 父进程创建Queue，并传给各个子进程 共享播放声音使用
		q = Queue()
		mgr = Manager()
		d_share = mgr.dict()
		d_share["faceOrder"] = ""
		d_share["frame"] = None
		d_share["ret"] = False
		# 定义系统类型  linux 与 windows
		d_share["system"] = system().lower()
		# 定义图像来源 Camera 与 MJPEG_Stream, windows上建议参数Camera
		d_share["Image_Source"] = "Camera"
		d_share["Voice_EN"] = True	#语音交互使能标志位
		d_share["awakeUpCnt"] = 0	#语音交互计数值
		d_share["RobotOrder"] = ""	# 判断机器人控制信号
		d_share["cfg"] = cfg	# 配置文件

		process_object = []
		# 语音交互进程
		process_object.append(Process(target=Voice, args=(q, d_share,) ) )
		# 摄像头进程
		process_object.append(Process(target=Face, args=(q, d_share,) ) )
		# 播放器进程
		process_object.append(Process(target=Player, args=(q, d_share,) ) )
		# 离线语音唤醒进程
		process_object.append(Process(target=VoiceAwakeUp, args=(q, d_share, ) ) )
		# 机器人控制进程
		process_object.append(Process(target=Action, args=(q, d_share) ) )
		
		for i in range(0, len(process_object), 1):
			process_object[i].start()  # 启动所有线程对象
		process_object[0].join()  # 等待子线程
