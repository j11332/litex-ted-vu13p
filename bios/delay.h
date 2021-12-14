#ifndef _DELAY_H
#define _DELAY_H

#define DELAY_MS(n) cdelay((n)*(CONFIG_CLOCK_FREQUENCY/4000))

static inline void cdelay(int i)
{
	while(i > 0) {
		__asm__ volatile(CONFIG_CPU_NOP);
		i--;
	}
}

#endif /* _DELAY_H */