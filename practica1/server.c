/***************************************************************************
 servidor.c
 Autor: Victoria Pelayo e Ignacio Rabunnal
 2019
***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <syslog.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <resolv.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <unistd.h>
#include "socket.h"
#include "thread_pool.h"
#include "demonio.h"
#include "myhttp_parser.h"

/*VARIABLES GLOBALES*/
int sock, max_clients, listen_port, buf_size, timeout;
thread_pool* tpool;
char server_root[MAX_CHAR];
char server_signature[MAX_CHAR];

/*
* MAnejador de la senial ctr+C
*/
void SIGINT_handler(){
	close(sock);
	thread_pool_destroy(tpool);
	syslog(LOG_ERR, "SIGINT: Cierre de servidor");
	exit(1);
}

/**
* Manejador de peticiones
*
* socket: socket para la peticion
* buff: cadena recibida
*
* Return: la peticion parseada
*/

int petition_handler(int socket, char* buff){
	return parsear_peticion(socket, buff, server_signature, server_root,  buf_size,  timeout);
}

/**
* Configura el servidor leyendo los argumentos de un fichero
*
* conf_file: ruta del fichero, o nombre si esta en el mismo directorio
* server_root: puntero a ruta del servidor
* max_clients: puntero al numero maximo de clientes
* listen_poort: puntero al numero de puerto
* server_signature: nombre del servidor
* buf_size: puntero al tamanio del buffer
* timeout: puntero al timeout
*
*/
void server_configure(char* conf_file, char* server_root, int* max_clients, int*listen_port, char* server_signature, int* buf_size, int* timeout){
	FILE* conf = fopen(conf_file, "r");
	char actual[100];
	char* delim = "=";
	char* tok;

	/*Hasta que no haya comentarios en el archivo de configuracion*/
	do{
		fgets(actual, sizeof(actual), conf);

	}while(strcmp(actual, "#") == 0);
	
	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	tok = strtok(NULL, delim);
	/*Eliminamos el caracter \n que tiene la cadena tok al parsearla desde el fichero*/
	strcpy(server_root, strtok(tok, "\n"));
	
	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	*max_clients = atoi(strtok(NULL, delim));

	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	*listen_port = atoi(strtok(NULL, delim));

	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	tok = strtok(NULL, delim);;
	strcpy(server_signature, strtok(tok, "\n"));

	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	*buf_size = atoi(strtok(NULL, delim));

	fgets(actual, sizeof(actual), conf);
	strtok(actual, delim);
	*timeout = atoi(strtok(NULL, delim));
	
	fclose(conf);
}

/**
* main del servidor
*/
int main(int argc, char const *argv[]){
	sigset_t set;
	struct sockaddr_in self;

	/*Parseamos el archivo de configuracion del servidor*/
	server_configure("server.conf", server_root, &max_clients, &listen_port, server_signature, &buf_size, &timeout);
	

	/***************************************************************************
	*********************DEMONIZAMOS EL PROCESO*********************************
	***************************************************************************/

		/*if(demonizar() < 0){
			syslog(LOG_ERR, "Error al demonizar el proceso");
			return -1;
		}*/

	/**************************************************************************
	*********************INICIAMOS LA CONEXION*********************************
	***************************************************************************/

	// inicializamos a 0 todas las variabless
	bzero((char*)&self, sizeof(self));

	self.sin_family = AF_INET;
	self.sin_port = htons(listen_port);
	self.sin_addr.s_addr = INADDR_ANY;

	sock = socket_conf(max_clients, self);

	if(sock < 0){
		close(sock);
		syslog(LOG_ERR, "Error al configurar el socket");
		return -1;
	}


	/****************************************************************************
	********************CREAMOS EL POOL DE HILOS ********************************
	***************************************************************************/

	tpool = thread_pool_create(max_clients, sock, buf_size, petition_handler);
	if(tpool == NULL){
		close(sock);
		syslog(LOG_ERR, "Error al crear la pool de hilos");
		return -1;
	}

	//Desbloqueamos SIGINT en el hilo principal
	sigemptyset(&set);
	sigaddset(&set, SIGINT);
	if(pthread_sigmask(SIG_UNBLOCK, &set, NULL) != 0){
		close(sock);
		thread_pool_destroy(tpool);
		syslog(LOG_ERR, "Error al desbloquear SIGINT del hilo principal");
		return -1;
	}

	// Asociamos la señal al manejador
	if(signal(SIGINT, SIGINT_handler) == SIG_ERR){
		close(sock);
		thread_pool_destroy(tpool);
		syslog(LOG_ERR, "Error al asociar la señal al manejador");
		return -1;
	}

	while(1);

	return 0;
}
