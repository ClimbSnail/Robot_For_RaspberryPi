#include "actionArrFile.h"

const short actionArr[12] __attribute__((at(0x08010000))) = {
			500,500,1500,1800,
			2500,2500,1500,1800,
			1500,1500,1500,1800};

const short pressArr[8] __attribute__((at(0x08010018))) = {
			1500,1500,1500,200,
			1000,1000,1500,200};