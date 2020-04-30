#coding:utf-8
import pyaudio
import wave
from baidu_speech_api import BaiduVoiceApi
import json
import signal
import sys
import RPi.GPIO as GPIO
import os
import thread
from aip.speech import AipSpeech

from urllib2 import Request, urlopen, URLError, HTTPError
import time
from pixels import Pixels, pixels
from alexa_led_pattern import AlexaLedPattern
from google_home_led_pattern import GoogleHomeLedPattern

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 1
RESPEAKER_WIDTH = 2
CHUNK = 1024
RECORD_SECONDS = 2
#WAVE_OUTPUT_FILENAME = "output.wav"

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.output(12, GPIO.LOW)
GPIO.output(13, GPIO.LOW)

p = pyaudio.PyAudio()
stream = p.open(
            rate=RESPEAKER_RATE,
            format=p.get_format_from_width(RESPEAKER_WIDTH),
            channels=RESPEAKER_CHANNELS,
            input=True,
            start=False,)

APP_ID = '11674925'
API_KEY = 'XATnBiP0mO9SYUSAPyrryPHP'
SECRET_KEY = '3Xk0pPNgsRkkRfRLOL2K5PGpFZ2jEMvr'
boolWaterlight = 0

aipSpeech = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

baidu = BaiduVoiceApi(appkey=API_KEY,secretkey=SECRET_KEY)

def generator_list(list):
    for l in list:
        yield l

def record():
    stream.start_stream()
    print("* recording")
    frames = []
    for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("* done recording")
    stream.stop_stream()
    print("start to send to baidu")
    # audio_data should be raw_data
    text = baidu.server_api(generator_list(frames))
    if text:
        try:
            text = json.loads(text)
            for t in text['result']:
                print(t)
                return(t)
        except KeyError: 
            return("get nothing")
    else:
        print("get nothing")
        return("get nothing")

def sigint_handler(signum, frame):
    stream.stop_stream()
    stream.close()
    p.terminate()
    print 'catched interrupt signal!'
    sys.exit(0)

def thread_water():
    while True:
        if boolWaterlight == 1:
            data = [255,0,0,0,0,0,0,0,0]
            pixels.show(data)
            time.sleep(0.4)
            data = [0,0,0,0,255,0,0,0,0]
            pixels.show(data)
            time.sleep(0.4)
            data = [0,0,0,0,0,0,0,0,255]
            pixels.show(data)
            time.sleep(0.4)
            data = [0,0,0,0,0,0,0,0,0]
            pixels.show(data)
            time.sleep(0.4)
        else:
            time.sleep(1)
    

# 注册ctrl-c中断
signal.signal(signal.SIGINT, sigint_handler)
pixels.pattern = GoogleHomeLedPattern(show=pixels.show)

thread.start_new_thread(thread_water, ())

while True:
    try:
        outputtext = record()
        if (u'开灯') in outputtext:
            boolWaterlight = 0
            os.system("sudo mpg123 turn_on_light.mp3")
            data =[255,255,255] * 3
            pixels.show(data)

        if (u'亮红灯') in outputtext:
            boolWaterlight = 0
            os.system("sudo mpg123 red.mp3")
            data =[255,0,0] * 3
            pixels.show(data)
                    
        if (u'亮绿灯') in outputtext:     
            boolWaterlight = 0       
            os.system("sudo mpg123 green.mp3")
            data =[0,255,0] * 3
            pixels.show(data)

        if (u'流水灯') in outputtext:
            os.system("sudo mpg123 waterlight.mp3")
            boolWaterlight = 1
            
        if (u'关灯') in outputtext:
            boolWaterlight = 0
            os.system("sudo mpg123 turnoff.mp3")
            pixels.off()
                
            
    except KeyError: 
        stream.close()
        p.terminate()
