# encoding: utf-8

# 基于图灵机器人API 2.0的对话功能
# 需要实现在http://www.tuling123.com开通功能，并创建一个机器人
# 测试运行环境python3.7(windows10/linux)

import json
import random
import requests

class TuringRobot():
    # 连接TuringRobot的请求地址
    api_url = "http://openapi.tuling123.com/openapi/api/v2"
    # 请求的数据类型
    _INPUT_TYPE_TEXT = 0 # 文本信息
    _INPUT_TYPE_IMAGE = 1 # 图片信息
    _INPUT_TYPE_MEDIA = 2 # 音频信息

    def __init__(self, apikey):
        """
        TuringRobot初始化
        :param api_key: 图灵机器人的apikey
        """
        userid = str(random.randint(0,65535)) # 用户对话上下文控制
        self.__userinfo = {
                "apiKey": apikey,
                "userId": userid
        }
        self.__req_type = TuringRobot._INPUT_TYPE_TEXT
        self.__location = {
                        "city": "北京",
                        "province": "北京",
                        "street": "信息路"
                    }
        # __reqinfo为请求的json数据
        self.__reqinfo = {
            "reqType":self.__req_type,
            "perception": {
                "inputText": {
                    "text": "附近的酒店"
                },
                "selfInfo": {
                    "location": self.__location
                }
            },
            "userInfo": ""
        }

    @property
    def apikey(self):
        return self.__userinfo["apiKey"]
    @apikey.setter
    def apikey(self, apiKey):
        self.__userinfo["apiKey"] = apiKey

    @property
    def reqtype(self):
        return self.__req_type
    @reqtype.setter
    def reqtype(self, type = 0):
        self.__req_type = type

    @property
    def location(self):
        return self.__location
    @location.setter
    def location(self, location):
        """
        :param location: 地址 传入一个字典
        :return:
        """
        self.__location["city"] = location["city"]
        self.__location["province"] = location["province"]
        self.__location["street"] = location["street"]

    def getTalk(self, ask_text):
        """
        对话函数 主要实现对话功能的函数
        :param ask_text: 提问的问题(字符串)
        :return: 请求结果字典 dict
        """
        if ask_text == "" or not ask_text:
            return {"text": "您没问我问题呢", "code": ""}
        # 构建对应的请求数据
        self.__reqinfo["reqType"] = TuringRobot._INPUT_TYPE_TEXT
        self.__reqinfo["perception"]["selfInfo"]["location"] = self.__location
        self.__reqinfo["perception"]["inputText"] = {"text": ask_text}
        self.__reqinfo["userInfo"] = self.__userinfo
        print(self.__reqinfo)
        try:
            # 通过post请求发送数据
            ret = requests.post(url = TuringRobot.api_url, data = json.dumps(self.__reqinfo) , timeout=50)
        except Exception as e:
            # 出错时报错 构建一个假的返回数据
            return {"results": [{"values": {"text": "网络出现了点问题，请检查网络"}}]}

        # 对返回的数据进行UTF-8编码
        ret.encoding = "utf-8"
        # 将字符串转为json格式
        ret = json.loads(ret.text)
        print(ret)
        return ret

# 主函数
if __name__ == "__main__":

    # This is a example
    # 定义一个图灵机器人对话对象
    obj_tr = TuringRobot("填写你的图灵apikey")
    # 设置位置(可选)
    # obj_tr.location = {"city":"", "province":"", "street":""}
    # print(obj_tr.location)
    while True:
        ask_text = input('请输入提问的问题: ')
        # 注意以下如果返回"加密方式错误"请关闭"机器人设置"-"终端设置"中的"密钥"
        print( 'Turing的回答：%s' %obj_tr.getTalk(ask_text)["results"][0]["values"]["text"] )
