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
#include <unistd.h>
#include "socket.h"

/**
* Acepta una conexion
* sockfd: identificador del socket de la conexion

* devuelve -1 si ha habido un error y si no el descriptor
*/
int aceptar_conexion(int sockfd){
  int desc;
  struct sockaddr client_addr;
  socklen_t len = sizeof(client_addr);

  desc = accept(sockfd, &client_addr, &len);
  if(desc < 0){
    syslog(LOG_ERR, "Error al aceptar la conexion");
    return -1;
  }



  return desc;
}

/**
*Lee los datos recibidos por un cliente y los guarda en buff
*
* sock_cliente: socket del cliente
* buff: cadena donde recibe los datos
* buf_size: tamanio del buff
*
* Devuelve -1 es caso de error, si no la longitud del mensaje
*/
int recibir(int sock_cliente, char* buff, long int buf_size){
  if(buff == NULL){
    return -1;
  }

  return recv(sock_cliente, buff, buf_size, 0);
}

/**
* Envia los datos del buffer al socket cliente
* sock_cleinte: socket del cliente
* buff: datos que se transmiten
* len: longitud de los datos
*
* Devuelve-1 en caso de error
*/
int enviar(int sock_cliente, char* buff, int len){
  if(buff == NULL){
    return -1;
  }

  return send(sock_cliente, buff, len, 0);
}

/**
* Cierra una conexion
*
* sockfd: socket de la conexion que se va a cerrar
*
* devuelve resultado de close
* 0 exito, -1 si error
*/
int cerrar_conexion(int sockfd){
  return close(sockfd);
}

/**
* Abre un socket
*
* Devuelve el identifcador en caso de exito
* <0 en caso de error
*/
int abrir_socket(){
  return socket(AF_INET, SOCK_STREAM, 0);
}


/**
* liga un puerto a un socket
*
* sockfd: socket que se quiere ligar
* self: estructura sockaddr_in para ligar el puerto 
*
* Devuelve el resultado de bind, <0 en caso de error
*/
int ligar_puerto_socket(int sockfd, struct sockaddr_in self){
  if(sockfd < 0){
    return -1;
  }
  return bind(sockfd, (struct sockaddr*) &self, sizeof(self));
}

/**
* Escucha hasta que la cola se llena
* sockfd: socket que escuha
* max_queue: tamanio maximo de la cola
*
* Devuelve !=0 en caso de error
*/
int escuchar(int sockfd, int max_queue){
  if(sockfd < 0 || max_queue < 0){
    return -1;
  }
  return listen(sockfd, max_queue);
}

/**
* Funcion que crea un socket lo liga a un puerto y se queda escuchando
*
* maxqueue: tamanio maximo de la cola
* self: estructura sockaddr_in
*
* devuelve el sockfd en caso de exito y -1 en caso de error
*/
int socket_conf(int maxqueue, struct sockaddr_in self){
  int sockfd;

  sockfd = abrir_socket();
  if(sockfd < 0){
      syslog(LOG_ERR, "Error en la creacion del socket");
      return -1;
  }

  if(ligar_puerto_socket(sockfd, self) ==-1){
    /*printf("error en bind\n");*/
    syslog(LOG_ERR, "Error al ligar puerto");
    return -1;
  }

  if(escuchar(sockfd,maxqueue) != 0){
    syslog(LOG_ERR, "Error al esuchar");
    return -1;
  }


  return sockfd;
}
