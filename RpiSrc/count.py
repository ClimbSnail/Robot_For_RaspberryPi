
PinList = [32, 36, 38, 40, 35, 33]
PinListOdd = PinList[0::2]
PinListEven = PinList[1::2]
print( PinListOdd )
print( PinListEven )

while True:
	try:
		data = input("请输入数据1: ")
		data2 = input("请输入数据2: ")
		datas = data.split(",")
		datas2 = data2.split(",")
		lis = []
		lis2 = []
		datas.reverse()
		datas2.reverse()
		if len(lis)==len(lis2):
			
			for dat in datas:
				lis.append(dat.strip())
			for dat2 in datas2:
				lis2.append(dat2.strip())
				
			for pos in range(len(lis)):
				print(int((int(lis[pos])-1500)*0.375+500),end = " ")
				print(int((int(lis2[pos])-1500)*0.375+500),end = " ")
			print("\n")
	except Exception as e:
		pass
