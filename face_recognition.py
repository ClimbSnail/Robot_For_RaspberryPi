# encoding: utf-8

# 本程序为封装了人脸识别的类	识别的功能基于opencv
# 具体调用方法请参考 if __name__ == "__main__": 的范例

import os
import json  # json对象
import time
import cv2 as cv  # pip install
import numpy as np
import threading
import urllib.request
from PIL import Image  # 记得安装 pip install Pillow
from platform import system


# import pytesseract as tess	# 记得安装 pip install pytesseract

class FaceRecognition():
    # 定义系统类型  linux 与 windows
    system = "linux"
    # HSV常用的色彩值 value列表的第一个值是低分量 第二个值为高分量
    HSV_value = {"black": [np.array([0, 0, 0]), np.array([180, 255, 46])],
                 "gray": [np.array([0, 0, 46]), np.array([180, 43, 220])],
                 "white": [np.array([0, 0, 221]), np.array([180, 30, 255])],
                 "red": [np.array([0, 43, 46]), np.array([10, 255, 255])],
                 "orange": [np.array([11, 43, 46]), np.array([25, 255, 255])],
                 "yellow": [np.array([26, 43, 46]), np.array([34, 255, 255])],
                 "green": [np.array([35, 43, 46]), np.array([77, 255, 255])],
                 "ching": [np.array([78, 43, 46]), np.array([99, 255, 255])],
                 "blue": [np.array([100, 43, 46]), np.array([124, 255, 255])],
                 "purple": [np.array([125, 43, 46]), np.array([155, 255, 255])]
                 }

    # 类的构造函数
    def __init__(self, fr_name="MyFace", image_msize=80, system="linux"):
        FaceRecognition.system = system  # 定义系统类型  linux 与 windows
        self.name = fr_name  # 当前人脸识别线程的名字
        self.image_save_num = 0  # 记录图片保存的数量
        self.image_msize = image_msize  # 设置训练数据的最大数目

        # 导入训练出来的模型(人脸特征)到级联分类器引擎 获取一个人脸检测器	cv.data.haarcascades
        self.face_detector = cv.CascadeClassifier("./data/"
                                                  + "haarcascade_frontalface_default.xml")
        # 导入训练出来的模型(人眼特征)到级联分类器引擎 获取一个人眼检测器	cv.data.haarcascades
        self.eye_detector = cv.CascadeClassifier("./data/"
                                                 + "haarcascade_eye_tree_eyeglasses.xml")
        self.face_model = 0  # 人脸模型 在initModel()里实际初始化
        self.label_json = {}  # 模型对应的标签描述文件
        self.imageSavePath = "./face_data/Image"  # 默认图片数据保存的总路径 注意：一定要加参数  %data
        self.modelPath = "./face_data/myface_data_xml"  # 默认模型保存的总路径

        self.face_model_flag = False

    def __del__(self):
        """
        类的析构函数
        :return:
        """
        cv.destroyAllWindows()  # 释放窗口资源

    @classmethod
    def string2int(self, strdat):
        """
        将英文字母字符串固定映射成整形数据 注：再次逆向转化回来需要使用int2string()函数(本函数目前不用了)
        :param strdat: 字符串
        :return:
        """
        ret = 0
        for strtmp in strdat:
            ret = ret * 100 + ord(strtmp) - 65
        return ret

    @classmethod
    def int2string(self, num):
        """
        将原本通过string2int()转化成的整形数据，再次转换成原始英文字母字符串（本函数目前不用了）
        :param num:
        :return:
        """
        ret = ""
        while num >= 0.5:  # 精度问题 不能写成 num>=0
            ret = chr(int(num % 100) + 65) + ret
            num /= 100
        return ret

    def getImageInfo(self, image):
        """
        打印图像数据的信息
        :param image: 图像数据
        :return:
        """
        print(type(image))
        print(image.shape)
        print(image.size)
        print(image.dtype)

    @classmethod
    def createDir(self, path):
        """
        检测目录是否存在 若不存在则创建目录
        :param path: 待检测的目录
        :return: None
        """
        location = "."
        floors = path.split("/")
        for floor in floors:
            location = location + "/" + floor
            if not os.path.exists(location):
                os.mkdir(location)  ## 创建目录操作函数

    def initModel(self, modelPath, modelName):
        """
        初始化模型对象
        :param modelPath: 模型的路径
        :param modelName: 模型名称
        :return:
        """
        # 判断是否存在该模型
        if not os.path.exists(modelPath + "/" + modelName):
            print("This model is not found !")
            return False
        # 使用LBPHFace算法识别，Confidence评分低于50是可靠
        self.face_model = cv.face.LBPHFaceRecognizer_create()
        # 读入模型
        self.face_model.read(modelPath + "/" + modelName)
        labelName = modelName.replace("xml", 'json')
        with open(modelPath + "/" + labelName, 'r', encoding="utf-8") as f_obj:
            self.label_json = json.load(f_obj)
        self.face_model_flag = True
        return True

    def faceDataExtraction(self, image, savePath, format):
        """
        采集图片中的人脸数据并保存
        :param image: 图片数据
        :param savePath: 保存的路径
        :param format: 保存的图片格式
        :return:
        """
        # 限制采集的图片数据
        if self.image_save_num >= self.image_msize:
            self.image_save_num = 0  # 初始化image_save_num计数变量
            cv.destroyWindow("Face Data extraction")  # 释放窗口资源
            cv.destroyWindow("Face Video")  # 释放窗口资源
            return True  # 返回是否采集完毕

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)  # 转为灰度图像 加快检测速度
        # 检测人脸 (120,120)表示允许检查到的最小人脸尺寸
        faces = self.face_detector.detectMultiScale(gray, 1.1, 10, 0, (120, 120))
        for x, y, w, h in faces:
            cv.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        if len(faces) == 1:
            x, y, w, h = faces[0]
            self.image_save_num += 1  # 计数
            # 扩大图片，可根据坐标调整 保证图片数据完整
            # x1 = int((x+w)*1.1)
            # y1 = int((y+h)*1.1)
            # x = int(x*0.9)
            # y = int(y*0.65)
            x1 = x + w
            y1 = y + h
            myFace = cv.resize(gray[y:y1, x:x1], (150, 150))  # 将兴趣域size为150 * 150
            cv.imshow("Face Data extraction", myFace)  # 显示绘制矩形框的图形
            # 检测目录是否存在 若不存在则创建目录
            FaceRecognition.createDir(savePath)
            # 图片名称已存在  不对其进行覆盖
            if os.path.exists(savePath + "/" + str(self.image_save_num) + format):
                print("The name of image was exist !")
            else:
                # 对于JPEG，其表示的是图像的质量，用0-100的整数表示，默认95;对于png ,第 三个参数表示的是压缩级别。默认为3.
                cv.imwrite(savePath + "/" + str(self.image_save_num) + format, myFace,
                           [int(cv.IMWRITE_JPEG_QUALITY), 95])
        # cv.imshow("Face Video", image)  # 显示绘制矩形框的图形
        return False  # 返回是否采集完毕

    def trainingModel(self, imagesPath, modelPath, modelName):
        """
        训练模型
        :param imagesPath: 训练数据路径
        :param modelPath: 保存模型路径
        :param modelName: 模型名称
        :return: 返回执行成功与否的标志位
        """
        # 判断是否存在图片数据
        if not os.path.exists(imagesPath):
            print("Image directory is not found !")
            return False

        # 储存图片和对应的标签
        images = []
        labels = []
        # 获取总图片目录下的所有子文件夹
        subfolders = os.listdir(imagesPath)

        # 遍历所有路径
        pos = 0  # 计数
        for subfolder in subfolders:
            pos += 1  # 累计计数
            # 获取路径下的所有文件名
            filenames = os.listdir(imagesPath + "/" + subfolder)
            # 提取图片数据与标签
            images += [cv.imread(imagesPath + "/" + subfolder + "/" + filename, cv.IMREAD_GRAYSCALE) for filename in
                       filenames]
            labels += [pos] * len(filenames)  #
            self.label_json[str(pos)] = subfolder
        # 没找到图片数据
        if len(images) == 0:
            return False
        # 创建识别模型，使用LBPHFace算法识别，Confidence评分低于50是可靠
        model = cv.face.LBPHFaceRecognizer_create()
        # 训练分类器 train函数参数：images, labels，两参数必须为np.array格式，而且labels的值必须为整型
        model.train(np.array(images), np.array(labels))
        # 检测目录是否存在 若不存在则创建目录
        FaceRecognition.createDir(modelPath)
        # 保存模型xml数据
        model.save(modelPath + "/" + modelName)
        # 保存label的映射描述json
        labelName = modelName.replace("xml", 'json')
        with open(modelPath + "/" + labelName, 'w', encoding="utf-8") as f_obj:
            json.dump(self.label_json, f_obj)

        # 返回成功
        return True

    def face_decete(self, image):
        """
        人脸检测
        :param image: RGB图片
        :return: 检测的结果(文本)
        """
        try:
            gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)  # 转为灰度图像 加快检测速度
            # 用人脸级联分类器引擎去检测gray中的人脸
            # 检测人脸 (80,80)表示允许检查到的最小人脸尺寸
            faces = self.face_detector.detectMultiScale(gray, 1.3, 5, 0, (40, 40))
            for x, y, w, h in faces:
                # 框选检测到的位置
                cv.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                # 放置消息文本框
                cv.putText(image, "Face", (x, y - 7), 1, 1.0, (0, 0, 255), 1, cv.LINE_AA)
                face_image = gray[y:y + h, x:x + w]
                # 用人眼级联分类器引擎去检测 face_image 中的人眼
                eyes = self.eye_detector.detectMultiScale(face_image, 1.5, 4)
                for x1, y1, w1, h1 in eyes:
                    # 框选识别面积
                    cv.rectangle(image, (x1 + x, y1 + y), (x1 + w1 + x, y1 + h1 + y), (0, 0, 255), 2)
                # face_image = gray[int(y*0.65):int((y+h)*1.1), int(x*0.9):int((x+w)*1.1)]

                if self.face_model_flag == True:
                    # 人脸识别
                    label, prob = self.face_model.predict(face_image)
                    ret_name = self.label_json[str(label)]
                    print(prob, end="\t")
                    print(ret_name)
                    # cv.imshow("face_image", face_image)  # 显示绘制矩形框的图形
                    if prob < 65:
                        # 放置消息文本框
                        cv.putText(image, ret_name, (int((2 * x + w) / 2), y - 18), 2, 1.0, (0, 0, 255), 1, cv.LINE_AA)
                        return "你好啊: " + ret_name
                    # 检测目录是否存在 若不存在则创建目录
                    FaceRecognition.createDir("./View")
                    # 图片名称已存在  不对其进行覆盖
                    if os.path.exists("./View" + "/" + str(time.time()) + ".jpg"):
                        print("The name of image was exist !")
                    else:
                        # 对于JPEG，其表示的是图像的质量，用0-100的整数表示，默认95;对于png ,第 三个参数表示的是压缩级别。默认为3.
                        cv.imwrite("./View" + "/" + str(time.time()) + ".jpg", image,
                                   [int(cv.IMWRITE_JPEG_QUALITY), 95])
            # image = cv.resize(image, (150, 150))  # 将兴趣域size为150 * 150
            # cv.imshow("face_decete", image)	#显示绘制矩形框的图形
            if len(faces) > 0:
                return "你好啊,朋友"
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def findColor(self, image, color="red"):
        """
        识别颜色 并将识别颜色对象外的其他颜色用黑色覆盖
        :param image: RGB图片
        :param color: 要识别的颜色
        :return: 处理后的图像
        """
        # 以下是计算绿色hsv色彩空间的值
        try:
            hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
        except Exception as err:
            hsv = image
            print(err)

        # 获取HSV对应色彩的值
        lower_hsv, upper_hsv = FaceRecognition.HSV_value[color]
        mask = cv.inRange(hsv, lowerb=lower_hsv, upperb=upper_hsv)  # 得到的掩膜值
        dst = cv.bitwise_and(image, image, mask=mask)  # 设置掩膜 位运算
        cv.imshow("dst", dst)  # 在窗口显示图像
        return dst

    def recognize_text(self, image):
        """
        验证码识别（有问题）
        :param image: RGB图片
        :return: 识别的结果(字符串)
        """
        gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)  # 转为灰度图像 加快检测速度
        ret, open_out = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)
        # 如果上面的效果不好 可以进行下列过滤
        # kernel = cv.getStructuringElement( cv.MORPH_RECT, (1,2) )
        # open_out = cv.morphologyEx( open_out, cv.MORPH_OPEN, kernel )
        # kernel = cv.getStructuringElement(cv.MORPH_RECT, (2, 1))
        # open_out = cv.morphologyEx(open_out, cv.MORPH_OPEN, kernel)
        cv.imshow("binary_image", open_out)
        cv.bitwise_not(open_out, open_out)
        textImage = Image.fromarray(open_out)
        # 图片转文字
        text = tess.image_to_string(textImage)
        # print( "识别结果：%s"%text )
        return text


stream = None
Running = False
bytes = b''
orgFrame = None
minFrame = None


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


def get_image():
    global Running
    global orgFrame, minFrame
    global bytes
    while True:
        if Running:
            try:
                bytes += stream.read(2048)  # 接收数据
                a = bytes.find(b'\xff\xd8')  # 找到帧头
                b = bytes.find(b'\xff\xd9')  # 找到帧尾
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]  # 取出图片数据
                    bytes = bytes[b + 2:]  # 去除已经取出的数据
                    orgFrame = cv.imdecode(np.fromstring(jpg, dtype=np.uint8), cv.IMREAD_COLOR)  # 对图片进行解码
                    minFrame = cv.resize(orgFrame, (720, 480), interpolation=cv.INTER_LINEAR)  # 将图片缩放到 320*240
            except Exception as e:
                print(e)
                continue
        else:
            time.sleep(0.01)


# 主函数
if __name__ == "__main__":

    # This is a example
    """
	cap = cv.VideoCapture(0)
	while( cap.isOpened() ):#USB摄像头工作时,读取一帧图像
		#t1 = time.time()
		ret, frame = cap.read() #显示图像窗口在树莓派的屏幕上
		#t2 = time.time()
		#print( "read: "+str(t2-t1) )
		cv.imshow('Capture',frame) 
		#t3 = time.time()
		#print( "imshow: "+str(t3-t2) )
		#按下q键退出
		key = cv.waitKey(1) #print( '%08X' % (key&0xFFFFFFFF) )
		if key & 0x00FF == ord('q'):
			break # 释放资源和关闭窗口
		time.sleep(0.03)
	cap.release()
	cv.destroyAllWindows()

	"""

    # 定义系统类型  linux 与 windows
    system = system().lower()

    # 定义图像来源 Camera 与 MJPEG_Stream, windows上建议参数Camera
    Image_Source = "MJPEG_Stream"

    if system == "windows":
        os.system("title FaceRecognition")

    if Image_Source == "Camera":
        capture = cv.VideoCapture(0)  # 获取摄像头对象
        capture.set(3, 720)  # 设置分辨率
        capture.set(4, 480)
    else:
        #	Image_Source选用MJPEG_Stream方式
        cv_continue()
        # MJPEG_Stream图像更新线程
        th1 = threading.Thread(target=get_image)
        th1.setDaemon(True)  # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
        th1.start()

    # 当前输入的模型名称(等效于标签)
    ModelName = "heqi"
    # 获取一个人脸识别的对象
    F = FaceRecognition(fr_name="MyFace")
    # 尝试加载模型对象
    modelLoad = F.initModel(modelPath=F.modelPath,
                            modelName="%s_FaceData.xml" % ModelName)

    # 如果模型没加载成功 说明模型文件有问题
    if modelLoad == False:
        # 尝试重新通过训练数据得到模型
        modelReady = F.trainingModel(F.imageSavePath, F.modelPath,
                                     "%s_FaceData.xml" % ModelName)
        #	训练模型失败
        if modelReady == False:
            #	遍历每个子文件夹
            filenames = os.listdir("./mypicture")
            for filename in filenames:
                frame = cv.imread("./mypicture/%s" % filename)

                # while isFinish == False:
                # 	ret, frame = capture.read()	#读取摄像头图像数据
                # 	if ret == False:
                # 		break
                isFinish = F.faceDataExtraction(frame, F.imageSavePath + "/heqi", ".jpg")
                c = cv.waitKey(20)  # 等待操作
                if c == 27:  # 如果按看下esc按键
                    break
            # 重新尝试训练模型
            F.trainingModel(F.imageSavePath, F.modelPath,
                            "%s_FaceData.xml" % ModelName)

        # 重新初始化相关的检测器和模型检测器
        F.initModel(modelPath=F.modelPath,
                    modelName="%s_FaceData.xml" % ModelName)

    # while( capture.isOpened() ):	#如果Image_Source选用Camera方式请开启注释	如果选用MJPEG_Stream方式请注释
    while True:  # 如果Image_Source选用MJPEG_Stream方式请开启注释	如果选用Camera方式请注释
        frame = None
        # 下面代码二选一
        # -------------------------------------------------------------#
        if Image_Source == "Camera":
            ret, frame = capture.read()  # 读取摄像头图像数据
            if ret == False:
                continue

        if Image_Source == "MJPEG_Stream":  # 通过MJPEG_Stream获取
            frame = minFrame
        # -------------------------------------------------------------#

        # frame = cv.imread("./face_data/test.jpg")	#读取指定路径的图片
        frame = cv.flip(frame, 1)  # 左右图像对换
        # cv.imshow('Capture',frame)

        # F.findColor(frame, color="red")	#以掩模的方式找到目标

        # 获取人脸检查与识别的结果
        info = F.face_decete(frame)
        # 人脸检查与识别的结果不为空
        if info != None:
            print(info)
        key = cv.waitKey(50)  # 等待操作
        if key & 0x00FF == ord('q'):  # 按下ESC
            break  # 释放资源和关闭窗口
        time.sleep(0.1)

    capture.release()  # 释放摄像头资源
    cv.destroyAllWindows()  # 释放窗口资源
