#include "sys.h"
#include "usart1.h"
//////////////////////////////////////////////////////////////////////////////////
//如果使用ucos,则包括下面的头文件即可.
#if SYSTEM_SUPPORT_OS
#include "includes.h"					//ucos 使用	  
#endif

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
//////////////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////
//加入以下代码,支持printf函数,而不需要选择use MicroLIB
#if 1
#pragma import(__use_no_semihosting)
//标准库需要的支持函数
struct __FILE
{
    int handle;
};

FILE __stdout;
//定义_sys_exit()以避免使用半主机模式
_sys_exit(int x)
{
    x = x;
}
//重定义fputc函数
int fputc(int ch, FILE *f)
{
    while((USART1->SR&0X40)==0);//循环发送,直到发送完毕
    USART1->DR = (u8) ch;
    return ch;
}
#endif

/*使用microLib的方法*/
/*
int fputc(int ch, FILE *f)
{
USART_SendData(USART1, (uint8_t) ch);

while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET) {}

   return ch;
}
int GetKey (void)  {

   while (!(USART1->SR & USART_FLAG_RXNE));

   return ((int)(USART1->DR & 0x1FF));
}
*/

#if EN_USART1_RX   //如果使能了接收
//串口1中断服务程序
//注意,读取USARTx->SR能避免莫名其妙的错误
//接收状态
//bit15，	接收完成标志
//bit14，	接收到0x0d
//bit13~0，	接收到的有效字节数目
u8 USART1_RX_BUF1[USART1_REC_LEN1];     //接收缓冲,最大USART_REC_LEN个字节.
u16 USART1_RX_STA1=0;       //接收状态标记
char USART1_RcvFinish1;//接收一帧完成标志位

u8 USART1_RX_BUF2[USART1_REC_LEN2];     //接收缓冲,最大USART_REC_LEN个字节.
u16 USART1_RX_STA2=0;       //接收状态标记
char USART1_RcvFinish2;//接收一帧完成标志位

void USART1_Init(u32 bound)
{
    //GPIO端口设置
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1|RCC_APB2Periph_GPIOA, ENABLE);	//使能USART1，GPIOA时钟

    //USART1_TX   GPIOA.9
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9; //PA.9
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;	//复用推挽输出
    GPIO_Init(GPIOA, &GPIO_InitStructure);//初始化GPIOA.9

    //USART1_RX	  GPIOA.10初始化
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;//PA10
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;//浮空输入
    GPIO_Init(GPIOA, &GPIO_InitStructure);//初始化GPIOA.10

    //Usart1 NVIC 配置
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=3 ;//抢占优先级3
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 3;		//子优先级3
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
    NVIC_Init(&NVIC_InitStructure);	//根据指定的参数初始化VIC寄存器

    //USART 初始化设置

    USART_InitStructure.USART_BaudRate = bound;//串口波特率
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;//字长为8位数据格式
    USART_InitStructure.USART_StopBits = USART_StopBits_1;//一个停止位
    USART_InitStructure.USART_Parity = USART_Parity_No;//无奇偶校验位
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;//无硬件数据流控制
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;	//收发模式

    USART_Init(USART1, &USART_InitStructure); //初始化串口1
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);//开启串口接受中断
    USART_Cmd(USART1, ENABLE);                    //使能串口1

}

u8 firstdata = 0;//第一回接收到的值
void USART1_IRQHandler(void)                	//串口1中断服务程序
{
    u8 Res;
#if SYSTEM_SUPPORT_OS 		//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntEnter();
#endif
    if(USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)  //接收中断(接收到的数据必须是0x0d 0x0a结尾)
    {
        Res = USART_ReceiveData(USART1);	//读取接收到的数据
        if( USART1_RX_STA1==0 && Res == 'D' && USART1_RX_STA2==0)
        {
            firstdata = Res;
            USART1_RX_BUF1[0] = Res;
        }
        else if( USART1_RX_STA2==0 && USART1_RX_STA1==0)
        {
            firstdata = Res;
            USART1_RX_BUF2[0] = Res;
        }
				
        if( firstdata == 'D' )
        {
							if(Res == '\n')
							{
									if( USART1_RX_STA1>1 && USART1_RX_BUF1[USART1_RX_STA1-1] == '\r' )
									{
											USART1_RX_BUF1[ USART1_RX_STA1 ] = Res;
											USART1_RX_STA1 = 0;//重新开始接收
											USART1_RcvFinish1 = 1;//接收一帧完成标志位
									}
									else
									{
											USART1_RX_BUF1[USART1_RX_STA1++] = Res ;
									}
							}
							else
									USART1_RX_BUF1[ USART1_RX_STA1++ ] = Res ;
							if(USART1_RX_STA1 > (USART1_REC_LEN1-1))
									USART1_RX_STA1 = 0;//接收数据错误,重新开始接收
        }
        else
        {
							if(Res == '\n')
							{
									if( USART1_RX_STA2>1 && USART1_RX_BUF2[USART1_RX_STA2-1] == '\r' )
									{
											USART1_RX_BUF2[ USART1_RX_STA2 ] = Res ;
											USART1_RX_STA2 = 0;//重新开始接收
											USART1_RcvFinish2 = 1;//接收一帧完成标志位
									}
									else
									{
											USART1_RX_BUF2[USART1_RX_STA2++]=Res ;
									}
							}
							else
									USART1_RX_BUF2[ USART1_RX_STA2++ ] = Res ;
							if(USART1_RX_STA2 > (USART1_REC_LEN2-1))
									USART1_RX_STA2 = 0;//接收数据错误,重新开始接收
        }
    }
#if SYSTEM_SUPPORT_OS 	//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntExit();
#endif
}
#endif

//发送一个字节
void USART1_PutChar(uint8_t Data)
{
    USART_SendData(USART1, Data);
    while(USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);
}

//发送字符串
void USART1_PutStr (uint8_t *str)
{
    while ( *str )
    {
        USART1_PutChar(*str);
        str++;
    }
}

void USART2_Init(u32 bound)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);	//使能USART1，GPIOA时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2,ENABLE);
    //USART1_TX   GPIOA.2
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2; //PA.2
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_OD;	//复用推挽输出
    GPIO_Init(GPIOA, &GPIO_InitStructure);//初始化GPIOA.2

    //Usart1 NVIC 配置
    NVIC_InitStructure.NVIC_IRQChannel = USART2_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=3 ;//抢占优先级3
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 3;		//子优先级3
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
    NVIC_Init(&NVIC_InitStructure);	//根据指定的参数初始化VIC寄存器

    //USART 初始化设置
    USART_InitStructure.USART_BaudRate = bound;//串口波特率
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;//字长为8位数据格式
    USART_InitStructure.USART_StopBits = USART_StopBits_1;//一个停止位
    USART_InitStructure.USART_Parity = USART_Parity_No;//无奇偶校验位
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;//无硬件数据流控制
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;//收发模式
    USART_Init(USART2, &USART_InitStructure); //初始化串口2
    USART2->CR2 &=(0<<14);
    USART2->CR2 &=(0<<11);
    USART2->CR3 &=(0<<1);
    USART2->CR3 &=(0<<5);
    USART2->CR3 |=(1<<3);
//    USART_HalfDuplexCmd(USART2,ENABLE);     //半双工使能

    USART_Cmd(USART2, ENABLE);      //打开串口2


}

//发送一个字节
void USART2_PutChar(uint8_t Data)
{
//    while(USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET);
////    USART2->CR1 &= ~(0<<2);
//    USART_SendData(USART2, Data);
//    while(USART_GetFlagStatus(USART2, USART_FLAG_TC) == RESET);

    USART_SendData(USART2, Data);
    while(USART_GetFlagStatus(USART2, USART_FLAG_TC) == RESET);
}

//发送字符串
void USART2_PutStr (uint8_t *str)
{
    while ( *str )
    {
        USART2_PutChar(*str);
        str++;
    }
}
void USART2_IRQHandler(void)//串口2中断服务程序
{
    u8 Res;
#if SYSTEM_SUPPORT_OS 		//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntEnter();
#endif
    if(USART_GetITStatus(USART2, USART_IT_RXNE) != RESET)//接收中断(接收到的数据必须是0x0d 0x0a结尾)
    {
        Res = USART_ReceiveData(USART2);	//读取接收到的数据
        USART2_PutChar(Res);
    }
#if SYSTEM_SUPPORT_OS 	//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntExit();
#endif
}
//void USART2_IRQHandler(void)                	//串口2中断服务程序
//{
//    u8 Res;
//#if SYSTEM_SUPPORT_OS 		//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
//    OSIntEnter();
//#endif
//    USART_ClearITPendingBit(USART2, USART_IT_RXNE);
//    USART_ClearFlag(USART2, USART_FLAG_RXNE);
//    if(USART_GetITStatus(USART2, USART_IT_RXNE) != RESET)  //接收中断(接收到的数据必须是0x0d 0x0a结尾)
//    {
//        Res = USART_ReceiveData(USART2);	//读取接收到的数据
//				USART2_PutChar(Res);
//    }
//#if SYSTEM_SUPPORT_OS 	//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
//    OSIntExit();
//#endif
//}
