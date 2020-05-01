### 基于树莓派的双足多感知机器人

项目来自我的本科毕业设计

最早之前做过一版，由单片机离线控制的。可以先预览。

B站视频[链接](https://b23.tv/BV1qs411L7Pn) https://b23.tv/BV1qs411L7Pn

整个项目为一个软硬件结合的项目，提供整个电路工程文件以及相关功能的所有源代码。

开发语言C、C++、Python、C#。

##### 代码结构
整个代码的设计遵从高内聚低耦合，每个子模块都可以单独使用，内部都有对应的demo。

* RobotMainLinux.py _（整个机器人的主控制模块，controller）_
* BaiduSpeak.py _（百度语音识别与合成）_
* face_recognition.py _（基于opencv的人脸检测与识别）_
* GPIO.py _（树莓派拓展板的IO驱动API）_
* ReadAction.py _（动作组文件的读取）_
* snowboydecoder.py _（语音唤醒支撑文件）_
* snowboydetect.py _（语音唤醒支撑文件）_
* TuringRobot.py _（图灵机器人对话）_
* 其余的为参考图片

##### 补充

所有功能都已实现，相关内容等整立完了，统一更新。

相关的windows客户端随后也将更新。