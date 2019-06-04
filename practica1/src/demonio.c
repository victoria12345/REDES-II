/***************************************************************************
 demonio.c
 Autor: Victoria Pelayo e Ignacio Rabunnal
 2019
***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "demonio.h"

/**
* Funcion que demoniza un proceso
*/
int demonizar(){
  pid_t pid;

  pid = fork();
  if(pid < 0){
    return -1;
  }

  if(pid > 0){
    exit(EXIT_SUCCESS);
  }

  umask(0);
  setlogmask(LOG_UPTO(LOG_INFO));
  openlog("Diablo yung beef remix", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL3);
  syslog(LOG_ERR, "Iniciando nuevo servidor");

  if(setsid() < 0){
    syslog(LOG_ERR, "Error creando un nuevo SID para el proceso hijo \n");
    return -1;
  }

  if((chdir("/")) < 0 ){
    syslog(LOG_ERR, "Error cambiando el directiorio de trabajo \n");
    return -1;
  }

  syslog(LOG_INFO, "Cerrando los descriptores de fichero estandar\n");
  close(STDIN_FILENO);
  close(STDOUT_FILENO);
  close(STDERR_FILENO);

  return 0;
}
