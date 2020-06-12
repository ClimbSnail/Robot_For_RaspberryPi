#ifndef __PWM_H
#define __PWM_H
#include "sys.h"

#define  pwm1 TIM4->CCR1
#define  pwm2 TIM4->CCR2
#define  pwm3 TIM4->CCR3

#define eachFrequencyTime 50		//舵机减缓单位时间(预设50ms 可更改)

extern void upData(void);//立即将nowPwm数据更新输出
extern void countAddPwm(short temp_pwm[3], short frequency);//计算每次pwm更新需要多大的增量(用于减速控制)
extern void changePwm(const short pwmValue[]);
extern void doAction(const short *actionArr,short length);

extern short targetPwm[3];//储存目标PWM
extern short nowPwm[3];//现在的Pwm
extern short addPwm[3];//每次自增的Pwm量

#endif

