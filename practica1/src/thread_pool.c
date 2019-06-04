/**
* Autores: Victoria Pelayo e Ignacio Rabunnal
*
*/
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
#include "thread_pool.h"

/**
* Estructura del pool de hilos
*/
typedef struct _thread_pool{
	pthread_t* lista_hilos; /*!< lista de los hilos*/
	pthread_mutex_t mutex; /*!< semaforo de hilos*/
	int num_hilos;  /*!< numero de hilos */
	int socket_escucha;  /*!< socket que usa */
	int (*handle_pointer)(int, char*);  /*!< puntero a la funcion */
	long int tam_buff;  /*!< tamanio del buffer */
	int stop_flag;  /*!< bandera que se activa cuando el servidor debe parar*/
}thread_pool;

/**
* Funcion que realiza la tarea de los hilos
* Se encarga de recibir las peticiones y procesarlas
*
*/
void* thread_task(void* args){
	/*Primero casteamos los argumentos ya que por exigencias de la libreria tienen que ser void*/
	int sock, socket_escucha, tam_buff;
	int (*handler)(int, char*);
	thread_pool* pool = (thread_pool*)args;

	if(pthread_mutex_lock(&pool->mutex) != 0){
		syslog(LOG_ERR, "Error al entrar en el mutex");
		pthread_exit(NULL);
	}

	handler = pool->handle_pointer;
	socket_escucha = pool->socket_escucha;
	tam_buff = pool->tam_buff;

	char buff_entrada[tam_buff];
	memset(buff_entrada, 0, tam_buff);

	if(pthread_mutex_unlock(&pool->mutex) != 0){
		syslog(LOG_ERR, "Error al salir del mutex");
		pthread_exit(NULL);
	}

	while(1){
		if(pthread_mutex_lock(&pool->mutex) != 0){
			syslog(LOG_ERR, "Error al entrar en el mutex");
			pthread_exit(NULL);
		}

		if(pool->stop_flag == 1){
			if(pthread_mutex_unlock(&pool->mutex) != 0){
				syslog(LOG_ERR, "Error al salir del mutex");
				pthread_exit(NULL);
			}
		}

		if(pthread_mutex_unlock(&pool->mutex) != 0){
			syslog(LOG_ERR, "Error al salir del mutex");
			pthread_exit(NULL);
		}

		sock = aceptar_conexion(socket_escucha);
		if(sock == -1){
			syslog(LOG_ERR, "Error al aceptar la conexion");
			pthread_exit(NULL);
		}

		if(recibir(sock, buff_entrada, tam_buff) == -1){
			syslog(LOG_ERR, "Error al recibir datos");
			pthread_exit(NULL);
		}

		/*Si al procesar la peticion ocurre un fallo, no cancelamos el hilo
		ya que debe de seguir siendo capaz de aceptar otras peticiones*/
		if(handler(sock, buff_entrada) == -1){
			syslog(LOG_ERR, "Error al procesar la peticion");
		}

		close(sock);
		bzero(buff_entrada, tam_buff);
	}

	pthread_exit(NULL);
}

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
thread_pool* thread_pool_create(int num_hilos, int socket_escucha, int tam_buff, int(*handle_pointer)(int, char*)){
	int i;
	sigset_t sigset;
	thread_pool* pool;

	/*Reservamos memoria e inicializamos atributos de la pool*/
	pool = (thread_pool*)malloc(sizeof(thread_pool));
	if(pool == NULL){
		syslog(LOG_ERR, "Error reservando memoria para la pool");
		return NULL;
	}

	/*Inicializamos el mutex*/
	if(pthread_mutex_init(&pool->mutex, NULL) != 0){
		syslog(LOG_ERR, "Error al inicializar el mutex de la pool");
		free(pool);
		return NULL;
	}

	pool->num_hilos = num_hilos;
	pool->socket_escucha = socket_escucha;
	pool->tam_buff = tam_buff;
	pool->handle_pointer = handle_pointer;
	pool->stop_flag = 0;
	
	pool->lista_hilos = (pthread_t*)malloc(sizeof(pthread_t)*num_hilos);
	if(pool->lista_hilos == NULL){
		syslog(LOG_ERR, "Error reservando memoria para la lista de hilos de la pool");
		free(pool);
		return NULL;
	}

	/*Creamos una mascara para bloquear la señan SIGINT de todos los hilos
	(se desbloqueara la misma en el hilo principal del servidor)*/
	sigemptyset(&sigset);
	sigaddset(&sigset, SIGINT);
	if(pthread_sigmask(SIG_BLOCK, &sigset, NULL) != 0){
		syslog(LOG_ERR, "Error al aplicar la mascara de bloqueo de señales");
		free(pool->lista_hilos);
		free(pool);
		return NULL;
	}

	/*Creamos todos los hilos solicitados*/
	for(i = 0; i < num_hilos; i++){
		if(pthread_create(&pool->lista_hilos[i], NULL, thread_task, (void*)pool) != 0){
			syslog(LOG_ERR, "Error creando algun hilo");
			free(pool->lista_hilos);
			free(pool);
			return NULL;
		}
	}

	return pool;
}

/**
* Se encarga de destruir un pool de hilos
* liberando la memoria y finalizando la ejecucion de los hilos
*/
void thread_pool_destroy(thread_pool* pool){
	int i;

	if(pthread_mutex_lock(&pool->mutex) != 0){
		syslog(LOG_ERR, "Error al liberar la pool");
		pthread_exit(NULL);
	}

	pool->stop_flag = 1;

	if(pthread_mutex_unlock(&pool->mutex) != 0){
		syslog(LOG_ERR, "Error al liberar la pool");
		pthread_exit(NULL);
	}

	for(i = 0; i < pool->num_hilos; i++){
		pthread_cancel(pool->lista_hilos[i]);
	}


	pthread_mutex_destroy(&pool->mutex);
	free(pool->lista_hilos);
	free(pool);
	return;
}
