#include "sys.h"
#include "deal.h"
#include <stdlib.h>
#include "delay.h"
#include "usart1.h"
#include "usart3.h"
#include "adc.h"
#include "pwm.h"
#include "actionArrFile.h"

void rcvDataCvtToPwmVal(u8 *dat, char *rcvFinish);	//将指令数据帧转换成PWM值并执行
//串口3的接受与转发的控制程序
void checkDeal_UT(u8 Usart1Data[], char *usart1Finish, u8 Usart3Data[], char *Usart3Finish, u16 Uart3len );
char checkAndDealActionDebug(u8 dat[], char *rcvFinish );	//处理动作数组
char checkADCReq(u8 dat[], char *rcvFinish);	//ADC数据请求处理
u16 adcValue = 0;


/************************************************************************
函数名称：rcvDataCvtToPwmVal()
功能描述： 数组调试模式 接收到的信息帧转换为Pwm信号并缓慢生效 可一次同时调试执行
					约400个动作
入口参数： dat: 表示要解析的数据帧		rcvFinish: 串口中断标志位
返 回 值： none
其他说明：
**************************************************************************/
void rcvDataCvtToPwmVal(u8 *dat, char *rcvFinish)
{
    short len = 1;//标识处理数据时的buffer指针
    short pwm[3];//存放当前动作组的pwm值
    short actionNum = 0;//存放动作组的个数值
    short executionTime;//存放当前动作组要执行的时间
    char flag;
    char i;

    //解析出帧头的数据(动作组的个数)
    while( dat[len] == ' ' ) len++;
    while( dat[len]<58 && dat[len]>47 )
    {
        actionNum = actionNum*10+dat[len++]-48;
    }

    *rcvFinish = 0;//标志位清零

    //解析actionNum次数据
    while( actionNum-- && !(*rcvFinish) )//标志位重新被置一的话说明有新的指令 需停止当前动作
    {
        executionTime = 0;
        flag = 0;
        for( i = 0 ; i<3 ; i++)
            pwm[i] = 0;

        //解析L动作数组的值
        while( flag<3 )
        {
            while( dat[len++] != ' ' );
            while( dat[len]<58 && dat[len]>47 )
            {
                pwm[flag] = pwm[flag]*10+dat[len++]-48;
            }
            if(  dat[len-1]<58 && dat[len-1]>47  )
                flag++;
        }
        //解析此组动作组要执行的时间
        while( dat[len] == ' ' )	len++;
        while( dat[len]<58 && dat[len]>47 )
        {
            executionTime = executionTime*10+dat[len++]-48;
        }

        countAddPwm(pwm, executionTime/eachFrequencyTime);//传入pwm以及减速倍率5,定时器6开启时将自动缓慢生效
        delay_ms(executionTime);//等待动作结束
    }
}

/************************************************************************
函数名称：	Uart3Cvt( void )
功能描述：	串口3收发控制程序
入口参数：	dat命令数据帧		rcvFinish:数据帧完整标志位
返 回 值：	none
其他说明：	开头‘YS’为语音设置指令 开头‘YT’为语音转发指令
**************************************************************************/
void checkDeal_UT(u8 Usart1Data[], char *usart1Finish, u8 Usart3Data[], char *Usart3Finish, u16 Uart3len)
{
    u8 *dat;
    u16 pos;
	
    if( *usart1Finish )//Usart1接收到完成指令标志位
    {
        if( Usart1Data[0] == 'U' && Usart1Data[2] == 'T' )//语音命令帧头标志
        {
            if( Usart1Data[1] == '2' )
            {
                for( dat=&Usart1Data[3]; *dat!='\r' || (*(dat+1)!='\n'); dat++)
                    USART2_PutChar( *dat );
                *usart1Finish = 0;//标志位清零
            }
            else if( Usart1Data[1] == '3' )
            {
                for( dat=&Usart1Data[3]; *dat!='\r' || (*(dat+1)!='\n'); dat++)
                    USART3_PutChar( *dat );
                *usart1Finish = 0;//标志位清零
                USART3_PutStr( "\r\n" );
            }
        }
    }
    //	转发控制	串口3的数据通过串口1转发出去
    if( *Usart3Finish )//Usart1接收到完成指令标志位
    {
        for( pos = 0; pos<Uart3len; pos++ )
            USART1_PutChar( Usart3Data[pos] );
        *Usart3Finish = 0;//标志位清零
    }
}

/************************************************************************
函数名称：	checkAndDealActionDebug( void )
功能描述： 检查并处理动作及调试指令
入口参数： dat命令数据帧		rcvFinish:数据帧完整标志位
返 回 值： 是否为Debug模式
其他说明： 开头‘D’为Debug模式 其余为动作指令
**************************************************************************/
char checkAndDealActionDebug(u8 dat[], char *rcvFinish )
{
    if( *rcvFinish )//是否已接收完整帧
    {
        if( dat[0] == 'D' )//数组调试模式帧头标志
        {
            rcvDataCvtToPwmVal(dat, rcvFinish);//数组调试模式 可一次同时调试执行400个动作
            *rcvFinish = 0;//标志位清零
            return 1;
        }
        return 0;
    }
    else
        return 0;
}

/************************************************************************
函数名称：	checkADCReq(const u8 dat[])
功能描述：	检测ADC请求
入口参数：	dat命令数据帧		rcvFinish:数据帧完整标志位
返 回 值：	char 表示是否有ADC请求
其他说明：	ADC请求指令的数据帧为"ADC?"
**************************************************************************/
char checkADCReq( u8 dat[], char *rcvFinish)
{
    if( *rcvFinish )//是否已接收完整帧
    {
        //数组调试模式帧头标志
        if( dat[0] == 'A' && dat[1] == 'D' && dat[2] == 'C' && dat[3] == '?' )
        {
            adcValue = Get_Adc(ADC_Channel_1);
            USART1_PutStr ( "ADC=" );
            USART1_PutChar( adcValue>>8 );
            USART1_PutChar( adcValue%256 );
            *rcvFinish = 0;//标志位清零
            return 1;
        }
        return 0;
    }
    else
        return 0;
}