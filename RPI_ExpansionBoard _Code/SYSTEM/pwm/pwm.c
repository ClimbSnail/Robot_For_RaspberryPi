#include "pwm.h"
#include "usart1.h"
#include "delay.h"


//上电后就是这个状态(初始值就是一个站立状态)
short nowPwm[3] = {1500,1500,1500};//当前Pwm
short targetPwm[3] = {1500,1500,1500};//目标Pwm
//每次定时中断时要增加的舵机量
short addPwm[3]= {0,0,0};


/************************************************************************
函数名称：	upData(void)
功能描述： 立即将nowPwm数据更新输出
入口参数： none
返 回 值： none
其他说明： 该函数将nowPwm数据直接输出到定义好的IO端口
**************************************************************************/
void upData(void )
{
    pwm1 = nowPwm[0];
    pwm2 = nowPwm[1];
    pwm3 = nowPwm[2];
}


/************************************************************************
函数名称：	countAddPwm(short temp_pwm[3], short frequency)
功能描述： 计算每次pwm更新需要多大的增量(用于减速控制)
入口参数： temp_pwm frequency:减缓倍率
返 回 值： none
其他说明： 该函数传入pwm以及减速倍率(单位减缓时间预设值为50ms),定时器6开启时
					将自动缓慢生效
**************************************************************************/
void countAddPwm(short temp_pwm[3], short frequency)
{
    u8 i;
    for( i = 0 ; i<3 ; i++ )
    {
        if( temp_pwm[i]>0 )
        {
            targetPwm[i] = temp_pwm[i];
            addPwm[i] = (targetPwm[i]-nowPwm[i])/frequency;
        }
    }
}

/************************************************************************
函数名称：	doAction(const short *actionArr,short length)
功能描述： 执行动作数组
入口参数： 指针型的actionArr length
返 回 值： none
其他说明： 该函数将传入的动作数组指针actionArr，以及actionArr的长度length(一定
						要是4的倍数 每组第4位为执行的时间间隔)有兴趣的可根据需要自行修改。
						本项目中此函数已经没有实际意义了暂时没用上
**************************************************************************/
void doAction(const short *actionArr,short length)
{
    short i = 0;
    char j = 0;
    short temp_pwm[3];//临时变量
    for( i = 0 ; i<length ; i+=4 )	//不带动作中途中断功能
//    for( i = 0 ; i<length && USART_RX_BUF[0] ; i+=4 )	//需要接收到停止命令的时候，当前动作才可以被打断
    {
        for( j = 0 ; j<3 ; j++ )
        {
            temp_pwm[j] = actionArr[i+j];
        }
        countAddPwm(temp_pwm, actionArr[i+3]/eachFrequencyTime);//50ms为定时器更新pwm的周期
        delay_ms(actionArr[i+3]);//时间延缓 舵机减速控制的一部分

        //添加以下代码 可以在做动作的同时进行语音对话
        /*
        if( usart3ReceiveSuccess2 )//如果语音缓冲区表明接收到完成指令帧
        {
        if( USART_RX_BUF2[0] == 'Y' )//语音命令帧头标志
        if( USART_RX_BUF2[1] == 'S' )
            YSOrder( USART_RX_BUF2[2] );//语音设置命令
        else if( USART_RX_BUF2[1] == 'T' ) //语音转发
            XFS_FrameInfo( &USART_RX_BUF2[2] );
        usart3ReceiveSuccess2 = 0;//标志位清零
        }
        */
    }
}
