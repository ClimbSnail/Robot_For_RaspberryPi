#include "usart3.h"
#include "usart1.h"

u8 USART3_RX_BUF[USART3_REC_LEN] = {0};//接收缓冲,最大USART_REC_LEN个字节.末字节为换行符
u16 USART3_RX_STA = 0;         		//接收状态标记
char USART3_RcvFinish = 0;		//接收一帧完成标志位
u16 USART3_Len = 0;	//接收到的数据长度

void USART3_Init(u32 bound)
{
    //GPIO端口设置
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);	//GPIOB
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);	//使能UART3

    //UART3_TX
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;	//复用推挽输出
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    //UART3_RX
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;//浮空输入
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    //Uart3 NVIC 配置
    NVIC_InitStructure.NVIC_IRQChannel = USART3_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=3 ;//抢占优先级3
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;		//子优先级3
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//IRQ通道使能
    NVIC_Init(&NVIC_InitStructure);	//根据指定的参数初始化VIC寄存器

    //USART 初始化设置
    USART_InitStructure.USART_BaudRate = bound;//串口波特率
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;//字长为8位数据格式
    USART_InitStructure.USART_StopBits = USART_StopBits_1;//一个停止位
    USART_InitStructure.USART_Parity = USART_Parity_No;//无奇偶校验位
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;//无硬件数据流控制
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;	//收发模式

    USART_Init(USART3, &USART_InitStructure); //初始化串口3
    USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);//开启串口接受中断
    USART_Cmd(USART3, ENABLE);                    //使能串口3

}

void USART3_IRQHandler(void)//串口2中断服务程序
{
    u8 Res;
#if SYSTEM_SUPPORT_OS 		//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntEnter();
#endif
    if(USART_GetITStatus(USART3, USART_IT_RXNE) != RESET)//接收中断(接收到的数据必须是0x0d 0x0a结尾)
    {
        Res = USART_ReceiveData(USART3);	//读取接收到的数据

				if(Res == '\n')
				{
						if( USART3_RX_STA>1 && USART3_RX_BUF[USART3_RX_STA-1] == '\r' )
						{
								USART3_RX_BUF[ USART3_RX_STA++ ] = Res;
								USART3_Len = USART3_RX_STA;
								USART3_RX_STA = 0;//重新开始接收
								USART3_RcvFinish = 1;//接收一帧完成标志位
						}
						else
						{
								USART3_RX_BUF[USART3_RX_STA++] = Res ;
						}
				}
				else
				{
						USART3_RX_BUF[ USART3_RX_STA++ ] = Res ;
				}
				if(USART3_RX_STA > (USART3_REC_LEN-1))
						USART3_RX_STA = 0;//接收数据错误,重新开始接收
				
        /*
        if((USART3_RX_STA&0x8000)==0)//接收未完成
        {
        if(USART3_RX_STA&0x4000)//接收到了0x0d
        {
        if(Res!=0x0a)
        				{
            USART3_RX_STA=0;//接收错误,重新开始
        						USART3_Len = 0;
        				}
        else
        {
            USART3_RX_STA|=0x8000;	//接收完成了
            USART3_RcvFinish = 1;//接收一帧完成标志位
        						USART3_Len ++;
        }
        }
        else //还没收到0X0D
        {
        if(Res==0x0d)
        {
            USART3_RX_BUF[USART3_RX_STA] = Res;
            USART3_RX_STA|=0x4000;
        }
        else
        {
            USART3_RX_BUF[USART3_RX_STA&0X3FFF]=Res ;
            USART3_RX_STA++;
        						USART3_Len ++;
            if(USART3_RX_STA>(USART3_REC_LEN-1))
                USART3_RX_STA=0;//接收数据错误,重新开始接收
        }
        }
        }
        */
    }
#if SYSTEM_SUPPORT_OS 	//如果SYSTEM_SUPPORT_OS为真，则需要支持OS.
    OSIntExit();
#endif
}

//发送一个字节
void USART3_PutChar(uint8_t Data)
{
    USART_SendData(USART3, Data);
    while(USART_GetFlagStatus(USART3, USART_FLAG_TC) == RESET);
}

//发送字符串
void USART3_PutStr(uint8_t *str)
{
    while (0 != *str)
    {
        USART3_PutChar(*str);
        str++;
    }
}

