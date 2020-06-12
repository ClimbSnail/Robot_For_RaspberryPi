#ifndef __USART1_H
#define __USART1_H
#include "stdio.h"	
#include "sys.h" 
#include "stm32f10x.h"

//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//ALIENTEK STM32开发板
//串口1初始化		   
//正点原子@ALIENTEK
//技术论坛:www.openedv.com
//修改日期:2012/8/18
//版本：V1.5
//版权所有，盗版必究。
//Copyright(C) 广州市星翼电子科技有限公司 2009-2019
//All rights reserved
//********************************************************************************
//V1.3修改说明 
//支持适应不同频率下的串口波特率设置.
//加入了对printf的支持
//增加了串口接收命令功能.
//修正了printf第一个字符丢失的bug
//V1.4修改说明
//1,修改串口初始化IO的bug
//2,修改了USART_RX_STA,使得串口最大接收字节数为2的14次方
//3,增加了USART_REC_LEN,用于定义串口最大允许接收的字节数(不大于2的14次方)
//4,修改了EN_USART1_RX的使能方式
//V1.5修改说明
//1,增加了对UCOSII的支持
#define USART1_REC_LEN1  			4096  	//定义最大接收字节数 8192
#define USART1_REC_LEN2  			4096  	//定义最大接收字节数 8192
#define EN_USART1_RX 			1		//使能（1）/禁止（0）串口1接收

extern u8 firstdata;//第一回接收到的值

// 第一组数据信息
extern u8  USART1_RX_BUF1[USART1_REC_LEN1]; //接收缓冲,最大USART_REC_LEN个字节.末字节为换行符 
extern u16 USART1_RX_STA1;         		//接收状态标记
extern char USART1_RcvFinish1;//接收一帧完成标志位

// 第二组数据信息
extern u8  USART1_RX_BUF2[USART1_REC_LEN2]; //接收缓冲,最大USART_REC_LEN个字节.末字节为换行符 
extern u16 USART1_RX_STA2;         		//接收状态标记
extern char USART1_RcvFinish2;//接收一帧完成标志位

//如果想串口中断接收，请不要注释以下宏定义
extern void USART1_Init(u32 bound);			//串口1初始化
extern void USART1_PutChar(uint8_t Data);//发送一个字节
extern void USART1_PutStr (uint8_t *str);//发送字符串

extern void USART2_Init(u32 bound);
extern void USART2_PutChar(uint8_t Data);//发送一个字节
extern void USART2_PutStr (uint8_t *str);//发送字符串

#endif


