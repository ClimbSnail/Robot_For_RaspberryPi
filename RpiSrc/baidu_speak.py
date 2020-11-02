# encoding: utf-8

#	本程序为百度语音识别、语音合成

import os
import wave
import json
import time
import pyaudio
from platform import system
from mylogger import *	# 导入日志库
from playsound import PlaySound	# 请在工程总找到playsound.py文件放到本程序同级目录
from aip import AipSpeech  # pip install baidu-aip

if system().lower() == "linux":
	import pygame

# 注意!!!
# 原始 PCM 的录音参数必须符合 8k/16k 采样率、16bit 位深、单声道，
# 支持的格式有：pcm（不压缩）、wav（不压缩，pcm编码）、amr（压缩格式）。
class BaiduSpeak():

	# 语音识别错误码
	asr_error_msg = {"3300": "输入参数不正确",
					 "3301": "音频质量过差", "3302": "鉴权失败",
					 "3303": "语音服务器后端问题", "3304": "用户的请求QPS超限",
					 "3305": "用户的日pv（日请求量）超限",
					 "3307": "语音服务器后端识别出错问题", "3308": "音频过长",
					 "3309": "音频数据问题", "3310": "输入的音频文件过大",
					 "3311": "采样率rate参数不在选项里", "3312": "音频格式format参数不在选项里",
					 }
	# 语音合成错误码
	synthesis_error_msg = {
		"500": "不支持的输入", "501": "输入参数不正确",
		"502": "token验证失败", "503": "合成后端错误",
	}

	infoJson = {}

	# 类的构造函数
	def __init__(self, app_id, api_key, secret_key, cache_path = "./BaiduSpeak" ):
		"""
		:param app_id: 你的百度App ID
		:param api_key: 你的百度Api Key
		:param secret_key: 你的百度Secret Key
		:param cache_path: 对象的所有文件总缓存目录
		"""
		self.client = AipSpeech(app_id, api_key, secret_key)  # 客户端连接key
		self.format = "wav"  # 录音格式
		self.cache_path = cache_path
		self.network_disconnect = self.cache_path + "/network_disconnect.mp3"
		self.sendPath = self.cache_path + "/sendToBaidu.%s" % self.format  # 要发送的录音文件
		self.receivePath = self.cache_path + "/receiveAuido.mp3"  # 接收到的语音文件
		self.speakcfg = self.cache_path + "/speak.conf"  # 语音配置文件
		self.spd = 5  # 语速 0-9  默认为5中语速
		self.pit = 5  # 音调 0-9  默认为5中音调
		self.vol = 5  # 音量 0-15   默认为5中音量
		self.per = 1  # 发音人选择, 0为女声，1为男声，
		# 3为情感合成-度逍遥，4为情感合成-度丫丫，默认为普通女
		self.dev_pid = 1536  # 1536普通话(支持简单的英文识别)		1537普通话(纯中文识别)
		self.rate = 16000  # 录音的采样频率 采样率16k不改
		# 检查并创建baidu语音文件目录
		BaiduSpeak.createDir(self.cache_path)
		self.cfgRead()  # 读取配置文件

	# 类的析构函数
	def __del__(self):
		"""
		将设置的信息保存到配置文件中
		:return: None
		"""
		self.cfgWrite(self.speakcfg)

	# 保存配置文件
	def cfgWrite(self, file):
		dat = {
			"infoJson": BaiduSpeak.infoJson,
		}
		dat = str(dat).replace(",", ",\n").replace("},", "},\n")
		with open(file, 'w') as fp:
			fp.write(dat)

	# 读配置文件
	def cfgRead(self):
		fileFlag = True		# 配置文件存在标志位
		
		# 查看是否有配置文件
		if os.path.exists(self.speakcfg):
			dat = {}
			with open(self.speakcfg, 'r') as f_obj:
				dat = f_obj.read().replace("'", '"')
			if dat == "":		# 配置文件为空
				fileFlag = False
			else:
				dat = json.loads(dat.replace(",\n", ",").replace("},\n", "},"))

				BaiduSpeak.infoJson = dat["infoJson"]
				self.format = BaiduSpeak.infoJson["format"]
				self.spd = BaiduSpeak.infoJson["spd"]
				self.pit = BaiduSpeak.infoJson["pit"]
				self.vol = BaiduSpeak.infoJson["vol"]
				self.per = BaiduSpeak.infoJson["per"]
				self.dev_pid = BaiduSpeak.infoJson["dev_pid"]
				self.rate = BaiduSpeak.infoJson["rate"]
		else:
			fileFlag = False
		
		if fileFlag == False:		# 配置文件为空
			BaiduSpeak.infoJson = {
				"format": self.format, "spd": self.spd,
				"pit": self.pit, "vol": self.vol,
				"per": self.per, "dev_pid": self.dev_pid,
				"rate": self.rate
			}

	@classmethod
	def createDir(self, path):
		"""
		检测目录是否存在 若不存在则创建目录
		:param path: 目录路径
		:return:
		"""
		location = "."
		floors = path.split("/")
		for floor in floors:
			location = location + "/" + floor
			if not os.path.exists(location):
				os.mkdir(location)  ## 创建目录操作函数

	def recording(self, Time):
		"""
		录音
		:param Time: 录音时间
		:return: 录音所保存的音频文件路径
		"""
		CHUNK = 1024  # wav文件是由若干个CHUNK组成的，CHUNK我们就理解成数据包或者数据片段.
		FORMAT = pyaudio.paInt16  # 这个参数后面写的pyaudio.paInt16表示我们使用量化位数 16位来进行录音。
		CHANNELS = 1  # 代表的是声道，这里使用的单声道。
		RECORD_SECONDS = Time  # 采样时间

		p = pyaudio.PyAudio()

		stream = p.open(format=FORMAT, channels=CHANNELS,
						rate=self.rate, input=True, frames_per_buffer=CHUNK)

		# print("* 录音开始\n")
		myPrint("* 录音开始\n", "green", "", 1)

		frames = []
		for i in range(0, int(self.rate / CHUNK * RECORD_SECONDS)):
			data = stream.read(CHUNK)
			frames.append(data)

		# print("* 录音结束\n")
		myPrint("* 录音结束\n", "green", "", 1)

		stream.stop_stream()
		stream.close()
		p.terminate()
		wf = wave.open(self.sendPath, 'wb')
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(p.get_sample_size(FORMAT))
		wf.setframerate(self.rate)
		wf.writeframes(b''.join(frames))
		wf.close()
		return self.sendPath

	# 读取音频文件流
	@classmethod
	def getFileDat(self, filePath):
		if not os.path.exists(filePath):
			print("Could not found %s" % filePath)
		else:
			with open(filePath, 'rb') as fp:
				return fp.read()

	def getTextByAudio(self, audio_path):
		"""
		语音识别
		:param audio_path: 要识别语音的语音文件路径
		:return: 识别到的文本
		"""
		# 识别本地文件 dev_pid 1536:普通话(支持简单的英文识别)
		#   dev_pid 1537:普通话(纯中文识别)
		ret = {"err_msg": ""}
		try:
			ret = self.client.asr(self.getFileDat(audio_path),
								  self.format, 16000, {'dev_pid': self.dev_pid, })
		# result字段返回的时1-5个候选结果 string类型 utf-8编码
		except Exception as err:
			print("网络出现了点问题，请检查网络!\n")
			# 播放音频
			if os.path.exists(self.network_disconnect):
				# 出错时报错 构建一个假的返回数据
				ret["err_msg"] = "Network not connected."
				ret["network_audio"] = self.network_disconnect  # 网络错误语音文件路径
			else:
				print(""""未找到"网络连接错误的"播报的语音文件""")
		return ret

	def getAudioPathByText(self, text):
		"""
		语音合成 成功返回True 否则False，并且将音频存在self.receivePath目录下
		:param text: 要合成语音的文本
		:return: 返回合成后的语音文件路径
		"""
		try:
			ret = self.client.synthesis(text, 'zh', 1, {
				'vol': self.vol, })
			# 识别正确返回语音二进制 错误则返回dict 参照下面错误码
			if not isinstance(ret, dict):
				with open(self.receivePath, 'wb') as f:
					f.write(ret)
				print("Audio was already download and save in %s!\n"%self.receivePath)
				return self.receivePath #返回语音路径
			else:
				print("Audio was download failed !\n")
				print("Error is: " + BaiduSpeak.synthesis_error_msg[dict["err_no"]])
				return None
		except Exception as err:
			print("网络出现了点问题，请检查网络!\n")
			# 播放音频
			if os.path.exists(self.network_disconnect):
				# 出错时报错 构建一个假的返回数据
				ret["err_msg"] = "Network not connected."
				ret["network_audio"] = self.network_disconnect  # 网络错误语音文件路径
			else:
				print(""""未找到"网络连接错误的"播报的语音文件""")
		return ret


class Play():

	def __init__(self, system = "linux"):
		"""
		:param system:系统平台类型
		"""
		# 定义系统类型  linux 与 windows
		self.__system = system
		if system == "linux":
			pygame.mixer.init()  # 初始化播放器
		if system == "windows":
			self.player = PlaySound()
			pass
	def playMusic(self, musicPath):
		"""
		播放音乐
		:param musicPath: 要播放音乐文件所在的路径
		:return:None
		"""
		# 判断路径是否存在
		if not os.path.exists(musicPath):
			print( "Can not found path !" )
		try:
			if self.__system == "windows":
				if ".mp3" in musicPath:
					self.player.play(musicPath)
					self.player.stop()
					self.player.close()
				elif ".wav" in musicPath:
					# -------------------播放wav格式的音频-------------------#
					CHUNK = 1024
					wf = wave.open(musicPath, 'rb')
					p = pyaudio.PyAudio()

					stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
									channels=wf.getnchannels(),
									rate=wf.getframerate(),
									output=True)

					data = wf.readframes(CHUNK)
					while data != b'':
						stream.write(data)
						data = wf.readframes(CHUNK)
					stream.stop_stream()
					stream.close()
					p.terminate()
				'''
				目前此播放方案已弃用
				# -------------------下面代码将mp3转为wav格式-------------------#
				dat = musicPath.split(".")
				newMusic = "." + dat[1] + ".wav"

				if ".wav" not in musicPath:
					t = time.time()
					# windows命令
					os.system("%s -i %s -y %s" % (self.player, musicPath, newMusic))
					# linux命令
					# os.system("mplayer -ao alsa:device=hw=1.0 %s"%newMusic)
					print(time.time() - t)

				'''

			if self.__system == "linux":
				pygame.mixer.init()
				pygame.mixer.music.load(musicPath)
				pygame.mixer.music.play()
				while pygame.mixer.music.get_busy():
					time.sleep(0.1)

				# time.sleep(5)
				# 可以立即停止播放 但记得要加延时 不然没有声音输出
				# pygame.mixer.music.stop()
		except Exception as err:
			print(err)


# 主函数
if __name__ == "__main__":

	print("This platform is " + system().lower())
	# system = "windows" or "linux"
	player = Play(system = system().lower())
	
	'''
	在运行之前先注册百度的开发者账号 填写以下相关的内容
	'''
	APP_ID = '******'  # 你的 App ID
	API_KEY = '******'  # 你的 Api Key
	SECRET_KEY = '******'  # 你的 Secret Key
	# 获取一个百度语音对象
	baidu = BaiduSpeak(APP_ID, API_KEY, SECRET_KEY)
	
	while True:
		# 录音4s
		audio_path = baidu.recording(4)
		# 语音识别
		ret = baidu.getTextByAudio(audio_path)
		# result字段返回的时1-5个候选结果 string类型 utf-8编码
		if ret["err_msg"] == "success.":
			print(ret["result"][0])
			# 语音合成
			path = baidu.getAudioPathByText(ret["result"][0])
			# 播放音频
			player.playMusic(path)
		elif ret["err_msg"] == "Network not connected.":
			# 播放音频
			player.playMusic(ret["network_audio"])
		else:
			print(ret["err_msg"])
