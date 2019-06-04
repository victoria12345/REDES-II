#ifndef __DEMONIO_H__
#define __DEMONIO_H__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <syslog.h>


/**
* Funcion que demoniza un proceso
*/
int demonizar();

#endif
