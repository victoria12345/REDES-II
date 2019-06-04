/**
* Autores: Victoria Pelayo e Ignacio Rabunnal
*
*/
#ifndef __SOCKET_H__
#define __SOCKET_H__

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
#include <unistd.h>

#define MAX_CHAR 100

/**
* Acepta una conexion
* sockfd: identificador del socket de la conexion

* devuelve -1 si ha habido un error y si no el descriptor
*/
int aceptar_conexion(int sockfd);

int cerrar_conexion(int sockfd);

/**
*Lee los datos recibidos por un cliente y los guarda en buff
*
* sock_cliente: socket del cliente
* buff: cadena donde recibe los datos
* buf_size: tamanio del buff
*
* Devuelve -1 es caso de error, si no la longitud del mensaje
*/
int recibir(int sock_cliente, char* buff, long int buf_size);

/**
* Envia los datos del buffer al socket cliente
* sock_cleinte: socket del cliente
* buff: datos que se transmiten
* len: longitud de los datos
*
* Devuelve-1 en caso de error
*/
int enviar(int sock_cliente, char* buff, int len);

/**
* Envia los datos del buffer al socket cliente
* sock_cleinte: socket del cliente
* buff: datos que se transmiten
* len: longitud de los datos
*
* Devuelve-1 en caso de error
* 0 exito, -1 si error
*/
int cerrar_conexion(int sockfd);

/**
* Abre un socket
*
* Devuelve el identifcador en caso de exito
* <0 en caso de error
*/
int abrir_socket();

/**
* liga un puerto a un socket
*
* sockfd: socket que se quiere ligar
* self: estructura sockaddr_in para ligar el puerto 
*
* Devuelve el resultado de bind, <0 en caso de error
*/
int ligar_puerto_socket(int sockfd, struct sockaddr_in self);

/**
* Escucha hasta que la cola se llena
* sockfd: socket que escuha
* max_queue: tamanio maximo de la cola
*
* Devuelve <0 en caso de error
*/
int escuchar(int sockfd, int max_queue);

/**
* Funcion que crea un socket lo liga a un puerto y se queda escuchando
*
* maxqueue: tamanio maximo de la cola
* self: estructura sockaddr_in
*
* devuelve el sockfd en caso de exito y -1 en caso de error
*/
int socket_conf(int maxqueue, struct sockaddr_in self);

#endif
