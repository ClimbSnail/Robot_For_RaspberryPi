import codecs
import time
import os

class LeServo:
	
	prefname = "LeAction"	# 表示乐幻的舵机动作文件	LeActionDemo为动作范例
	actionNumMark = "ActionNum"	# 动作编号标识
	actionFPaths = []		# 以prefname字符串打头的动作文件路径(str)
	
	allNumInfo = {}			# 文件中的所有动作保存信息字点  ps:动作编号(int)->{"filePath":件路径(str), "startPos":所在行下标(int), "endPos":在行下标(int)}
	prestrain = []			# 常注内存的动作编号(int)
	inMemDict = {}			# 常驻内存的动作字典	ps:动作编号(int)->[动作数据1,动作数据2,动作数据3....]
	errorData = []			# 舵机安装数据的误差
	name_num = {}			# 通过动作组的名字寻找动作的编号
	
	def __init__(self, folder = "./action", saveNum = "1-5,6,9-10" ):
		"""
		LeServo初始化
		:param folder: 动作文件夹的路径
		:param saveNum: 要保存到内存中的动作组编号所标识的范围
		"""
		# 解析长期存放内存中的动作编号
		self.prestrain = self.analysisStr( saveNum )
		if len( self.prestrain ) != 0:
			print("常驻内存的动作编号为: "+ str(self.prestrain) )
		
		# 读取folder所指定目录下, 以self.prefname开头的文件名,保存到 self.actionFPath
		self.actionFPaths = self.readFPath( folder, self.prefname)
		print("Files beginning with %s are read in the directory %s as follows:"%(self.prefname, folder) )
		for filePath in self.actionFPaths:
			print( "\t"+ filePath )
		
		# 读取动作数据 并将常注内存的动作数据存放到字典中
		self.allNumInfo, self.inMemDict = self.readAllAtion( self.actionFPaths, self.actionNumMark, self.prestrain)

	def analysisStr(self, numstr):
		"""
		解析区间字符串
		:param numStr: 要解析成列表的规则
		:return:解析出来的数据列表
		"""
		numlist = []
		numStr = numstr.split(',')
		for numtmp in numStr:
			scope = numtmp.split('-')
			if len(scope) > 2:
				print("Error for split, please check your input.\n")
				break
			if len(scope) == 1:
				numlist.append( int(scope[0]) )
			else:
				for addnum in range( int(scope[0]), int(scope[1])+1 ):
					numlist.append( addnum )
		return numlist

	def readFPath(self, folderPath, pre):
		"""
		读取folderPath目录下所有 以pre表示字符打头的动作文件所在的路径
		:param folderPath: 指定的目录
		:param pre: 字符串头
		:return: 路径字典
		"""
		paths = []
		dir_or_files = os.listdir( folderPath )
		for dir_file in dir_or_files:
			if not os.path.isdir(dir_file) and pre in dir_file:
				paths.append( folderPath+"/"+dir_file )
		return paths			
	
	# 查找下一个mark所在的行 从startPos行开始查找 返回mark所在的行
	def findNextMark(self, mark, datas, startPos, endPos):
		pos = startPos
		findPos = -1
		while pos<endPos:
			strtmp = datas[pos].strip()
			# 过滤掉空行与‘#’注释
			if strtmp == '' or strtmp[0] == '#' :
				pos += 1
				continue
			
			if mark in strtmp:
				findPos = pos
				break
			pos += 1
		return findPos

	def getData(self, datas, startPos, endPos, filepath):
		"""
		处理一块数据
		:param datas:
		:param startPos:
		:param endPos:
		:param filepath: 要处理的文件所在的路径
		:return:
		"""
		data = datas[startPos].strip()
		pos = startPos+1
		resFlag = True
		actionName = ""
		errorInfo = ''
		actionDatas = []
		actionNum = -1
		singleData = {"data":[], "runtime":0}
		if ":" in data:
			try:
				data = data.split(":")
				errorInfo = "Syntax error in file %s ,line %d"%(filepath, pos)
				actionNum = int( data[1].strip() )
				if len(data)>2:
					actionName = data[2].strip()
				while pos<endPos:
					strtmp = datas[pos]
					if strtmp.strip() == "" or "#" in strtmp[0]:
						pos += 1
						continue
					tmplist = strtmp.strip().split(" ")
					for tmp in tmplist:
						if tmp != "":
							if "ms" in tmp:
								errorInfo = "Incorrect data format in file %s ,line %d"%(filepath, pos+1)
								singleData["runtime"] = int(tmp.split("ms")[0])
								actionDatas.append(singleData)
								# 先清空singleData
								singleData = {"data":[], "runtime":0}
								break
							else:
								errorInfo = "Disputed data in file %s ,line %d"%(filepath, pos+1)
								singleData["data"].append(int(tmp))
					pos += 1
			except Exception as e:
				resFlag = False
		else:
			resFlag = False
			errorInfo = "No found ':' symbols in file %s ,line %d"%(filepath, pos+1)
			
		return actionNum, actionDatas, actionName, {"flag":resFlag, "errorInfo":errorInfo}
		
	def readAllAtion(self, paths, actionmark, save_mem_num):
		"""
		读取所有的动作组
		:param paths: 目录的路径列表
		:param actionmark:一个动作组开始的标志
		:param save_mem_num: 保存到内存中的动作组编号
		:return:
		"""
		allnuminfo = {}		# 搜索到的所有动作存放信息
		inmemdict = {}
		
		# 遍历所有文件
		for path in paths:
			actionFile = codecs.open( path, "r", "utf-8")
			datas = actionFile.readlines()
			datLen = len(datas)
			
			# 查找第1行后一个aNumMark标志所在的下标位置
			pos = self.findNextMark(actionmark, datas, 0, datLen)
			if pos == -1:
				continue
			while pos<datLen:
				numPos = pos
				# 查找第pos+2行后一个aNumMark标志所在的下标位置
				endPos = self.findNextMark(actionmark, datas, pos+1, datLen)
				if endPos == -1:
					endPos = datLen
				actionDatas = []
				# 正式解析动作数据 解析pos+1行到endPos行之间的数据
				actionNum, actionDatas, actionName, result = self.getData(datas, pos, endPos, path)
				pos = endPos
				# Save actionInfo(filepath, line) for this actionNum
				if result["flag"] == False:
					print( result["errorInfo"] )
					continue
				# 存在相同动作编号 提示并覆盖
				if actionNum in allnuminfo.keys():
					print( "Warning: (%s,line %d) was already overwrite (%s,line %d)"\
						%( path, numPos+1, allnuminfo[actionNum]["filePath"], allnuminfo[actionNum]["startPos"]+1 ) )
				
				if actionName != "":
					# 存在相同名字的动作就提示并覆盖
					if actionName in self.name_num.keys():
						print( "Warning: (%s,line %d) was already overwrite (%s,line %d)"\
							%( path, numPos+1, allnuminfo[self.name_num[actionName]]["filePath"], \
							allnuminfo[self.name_num[actionName]]["startPos"]+1 ) )
					self.name_num[actionName] = actionNum
				
				allnuminfo[actionNum] = {"filePath":path, "startPos":numPos, "endPos":endPos}
				# 判断该动作组是否要保存到内存中
				if actionNum in save_mem_num:
					inmemdict[actionNum] = actionDatas
		# 返回得到的结果数据
		return 	allnuminfo,	inmemdict

	def readActionArr(self, actionNum = 0, actionName = None):
		"""
		读取指定编号/名字的动作数组
		:param actionNum: 指定编号
		:param actionName: 指定名字
		:return:
		"""
		result = True
		errorInfo = ''
		actionDatas = []
		# 通过动作名查找动作对应的编号
		if actionName != None:
			if actionName in self.name_num.keys():
				actionNum = self.name_num[actionName]
			else:
				result = False
				errorInfo = "NoFound action name: %s"%actionName
				return actionDatas, {"flag":result, "errorInfo":errorInfo}
		# 查看是否加载到内存中
		if actionNum in self.inMemDict.keys():
			actionDatas = self.inMemDict[actionNum]
		# 查看是否在文件中
		elif actionNum in self.allNumInfo:
			filepath = self.allNumInfo[actionNum]["filePath"]
			startPos = self.allNumInfo[actionNum]["startPos"]
			endPos = self.allNumInfo[actionNum]["endPos"]
			actionFile = codecs.open( filepath, "r", "utf-8")
			datas = actionFile.readlines()
			actionNum, actionDatas, actionName, res = self.getData(datas, startPos, endPos, filepath)
			if res["flag"] == False:
				print( res["errorInfo"] )
				result = False
				errorInfo = "NoFound action number %d"%actionNum
		else:
			result = False
			errorInfo = "NoFound action number %d"%actionNum
		return actionDatas, {"flag":result, "errorInfo":errorInfo}
	
	def arrToStr_b(self, actionarr, runtime):
		"""
		将数据转为总线舵机对应协议的bytes
		:param actionarr: pwm数组
		:param runtime: 动作运行时间
		:return: 要发送的协议数据
		"""
		datas = b''
		timeL = (runtime&0xff)
		timeH = (runtime>>8)
		arrlen = len(actionarr)
		for pos in range(arrlen):
			val = actionarr[pos]
			valL = (val&0xff)
			valH = (int(val/256))
			if actionarr[pos] > -1:
				data = b'\x55\x55'
				data += (pos+1).to_bytes(1, byteorder='little')
				data += b'\x07\x01'
				data += valL.to_bytes(1, byteorder='little')
				data += valH.to_bytes(1, byteorder='little')
				data += timeL.to_bytes(1, byteorder='little')
				data += timeH.to_bytes(1, byteorder='little')
				checkSum = (pos+1)+7+1+valL+valH+timeL+timeH
				checkSum = (~checkSum)&0xff
				data += checkSum.to_bytes(1, byteorder='little')
				datas += data
		return datas
	
	# 类的析构
	def __del__(self):
		pass


# demo for LeServe
if __name__ == "__main__":
	
	LeA = LeServo()
	
	print("")
	arr, res = LeA.readActionArr(actionNum = 1)
	if res["flag"] == False:
		print(res["errorInfo"])
	else:
		print(arr)
		for arr in arrs:
			BusStr = LeA.arrToStr_b(arr["data"],arr["runtime"])
			print( BusStr )
