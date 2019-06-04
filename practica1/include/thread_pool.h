/**
* Autores: Victoria Pelayo e Ignacio Rabunnal
*
*/
#ifndef _THREAD_POOL_
#define _THREAD_POOL_

#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>
#include <locale.h>
#include <signal.h>
#include <pthread.h>
#include "socket.h"

/**
* Estructura del pool de hilos
*/
typedef struct _thread_pool thread_pool;

/**
* Funcion que realiza la tarea de los hilos
* Se encarga de recibir las peticiones y procesarlas
*
*/
void* thread_task(void* args);

/**
* Funcion que crea el pool de hilos
*
* num_hilos: numero de hilos del pool
* socket_escucha: socket del pool
* tam_buff: tmaannio maximo del buffer
* puntero a la funcion tarea de los hilos
*
* Devuelve estructura de tipo thread_pool
*/
thread_pool* thread_pool_create(int num_hilos, int socket_escucha, int tam_buff, int(*handle_pointer)(int, char*));

/**
* Se encarga de destruir un pool de hilos
* liberando la memoria y finalizando la ejecucion de los hilos
*/
void thread_pool_destroy(thread_pool* pool);

#endif