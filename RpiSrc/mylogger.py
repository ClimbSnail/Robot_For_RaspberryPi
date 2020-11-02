

ColorMap = {
	"black":[30, 40],
	"red":[31, 41],
	"green":[32, 42],
	"yellow":[33, 43],
	"blue":[34, 44],
	"darkmagenta":[35, 45],
	"cyan":[36, 46],
	"white":[37, 47],
	"normal":[38, 48]
}# 大于37将显示默认字体

displayMode = [0, 1, 4, 5, 7, 8]


def myPrint(msg, *args, **kwargs):
	try:
		if args != ():
			foreGround = ColorMap[args[0]][0] if args[0] in ColorMap else ColorMap["normal"][0]
			backGround = ColorMap[args[1]][1] if args[1] in ColorMap else ColorMap["normal"][1]
			dpMode = str(args[2]) if len(args) == 3 and args[2] in displayMode else "0"
			colorSet = "\033[%s;%s;%sm" % (foreGround, backGround, dpMode)
		else:
			colorSet = ""
		#logger.debug(msg, **kwargs)
		print(colorSet, end="")
		print(msg, end="")
		print("\033[0m")  # 恢复默认
	except Exception as err:
		print(err)
		print(err.__traceback__.tb_frame.f_globals["__file__"],
			  "\tLines：", err.__traceback__.tb_lineno)  # 发生异常所在的文件


if __name__ == "__main__":
	myPrint("This is demo!", "green", "", 1)