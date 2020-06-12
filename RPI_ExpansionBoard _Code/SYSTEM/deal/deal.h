#ifndef __DEAL_H
#define __DEAL_H
#include "sys.h"


extern void rcvDataCvtToPwmVal(u8 *dat, char *rcvFinish);	//将指令数据帧转换成PWM值并执行
//串口3的接受与转发的控制程序
extern void checkDeal_UT(u8 Usart1Data[], char *usart1Finish, u8 Usart3Data[], char *Usart3Finish, u16 Uart3len );
extern char checkAndDealActionDebug(u8 dat[], char *rcvFinish );	//处理动作数组
extern char checkADCReq(u8 dat[], char *rcvFinish);	//ADC数据请求处理
extern u16 adcValue;


#endif

