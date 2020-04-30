# encoding: utf-8

import json
import requests

class TuringRobot:
    # 连接TuringRobot的请求地址
    api_url = "http://www.tuling123.com/openapi/api"

    def __init__(self):
        # ask为请求的json数据
        self.ask = {
            "key": "adfb722fdaf44e9fa820ed7c7d36a0c2",
            "info": ""
        }
    # 对话函数 主要实现对话功能的函数
    def talk(self, ask_text):
        if ask_text == "" or not ask_text:
            return {"text": "您没问我问题呢", "code": ""}
        # 构建对应的请求数据
        self.ask["info"] = ask_text
        try:
            # 通过post请求发送数据
            re = requests.post(url = TuringRobot.api_url, data = self.ask , timeout=50)
        except Exception as e:
            # 出错时报错 构建一个假的返回数据
            return {"text":"网络出现了点问题，请检查网络", "code":""}
        # 对返回的数据进行UTF-8编码
        re.encoding = "utf-8"
        # 将字符串转为json格式
        ret = json.loads(re.text)
        return ret

# 主函数
if __name__ == "__main__":

    # This is a example
    # 定义一个图灵机器人对话对象
    TR = TuringRobot()
    while True:
        ask_text = input('请输入对话内容: ')
        print( 'Turing的回答：%s' %TR.talk(ask_text)["text"] )