# encoding: utf-8
from mylogger import *	# 导入日志库
import codecs
import time
import json
import os

class ConfigManager(object):

    def __init__(self, cfgfile):
        fp = codecs.open(cfgfile, "r", "utf8")
        cfg = json.load(fp)
        self._baiduspeak = cfg["baiduspeak"] if "baiduspeak" in cfg.keys() else None
        self._turing = cfg["turing"] if "turing" in cfg.keys() else None
        self._action = cfg["action"] if "action" in cfg.keys() else None
        self._opencv = cfg["opencv"] if "opencv" in cfg.keys() else None
        self._gpio = cfg["gpio"] if "gpio" in cfg.keys() else None
        self._socket = cfg["gpio"] if "gpio" in cfg.keys() else None

    def __del__(self):
        pass

    def getBaiduSpeakAppid(self):
        return self._baiduspeak["APP_ID"] if self._baiduspeak and "APP_ID" in self._baiduspeak.keys() else None
    def getBaiduSpeakAppkey(self):
        return self._baiduspeak["API_KEY"] if self._baiduspeak and "API_KEY" in self._baiduspeak.keys() else None
    def getBaiduSpeakSecretkey(self):
        return self._baiduspeak["SECRET_KEY"] if self._baiduspeak and "SECRET_KEY" in self._baiduspeak.keys() else None
    def getBaiduSpeakcachepath(self):
        return self._baiduspeak["cachepath"] if self._baiduspeak and "cachepath" in self._baiduspeak.keys() else None

    def getTuringApikey(self):
        return self._turing["apikey"] if self._turing and "apikey" in self._turing.keys() else None

    def getActionFolder(self):
        return self._action["actionfolder"] if self._action and "actionfolder" in self._action.keys() else None
    def getActionSavenum(self):
        return self._action["saveNum"] if self._action and "saveNum" in self._action.keys() else None

    def getOpencvDataFolderpath(self):
        return self._opencv["datafolderpath"] if self._opencv and "datafolderpath" in self._opencv.keys() else None
    def getOpencvModelSavePath(self):
        return self._opencv["modelPath"] if self._opencv and "modelPath" in self._opencv.keys() else None
    def getOpencvModelName(self):
        return self._opencv["modelName"] if self._opencv and "modelName" in self._opencv.keys() else None
    def getOpencvImageSavePath(self):
        return self._opencv["imageSavePath"] if self._opencv and "imageSavePath" in self._opencv.keys() else None


    def getGPIOUartname(self):
        return self._gpio["uartname"] if self._gpio and "uartname" in self._gpio.keys() else None
    def getGPIOUartbaudrate(self):
        return int(self._gpio["baudrate"]) if self._gpio and "baudrate" in self._gpio.keys() else None

    def getSocketIp(self):
        return self._socket["ip"] if self._socket and "ip" in self._socket.keys() else None
    def getSocketPort(self):
        return self._socket["port"] if self._socket and "port" in self._socket.keys() else None

if __name__ == "__main__":
    config = ConfigManager("default.cfg")
    print( config.getBaiduSpeakAppid() )
