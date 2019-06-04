/**
* Autores: Victoria Pelayo e Ignacio Rabunnal
*
*/
#ifndef __MYHTTP_PARSER_H__
#define __MYHTTP_PARSER_H__

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
#include <signal.h>
#include <fcntl.h>
#include <time.h>

#include "picohttpparser.h"
#include "socket.h"

#define NO_SCRIPT 1
#define SCRIPT 2
#define PYTHON_S 6
#define PHP_S 7
#define TAM_COMANDO 255
#define MAX_STRING 300

typedef struct _Metodos Metodos;

/**
* Devuelve la fecha
*/
char* get_date();

/**
* Funcion que parsea una peticion
* sock: socket que usaremos
* peticion : peticion a parsear
* servidor : nombre del servidor
* root: directorio raiz del servidor
* max_size : tamanio  maximo del buffer
* timeout: timeout del servidor
*
* Devuelve 0 si todo ha ido correctamente
*/
int parsear_peticion(int sock, char* peticion, char* servidor, char* root, long int max_size, long int timeout);

/**
* Funcion que obtiene la fecha de ultima modificacion de un fichero
* file_info : Estructura que contiene la informacion del fichero
*
* Devuelve la fecha si todo ha ido correctamente y NULL en otro caso
*/
char* get_ultima_mod(struct stat* file_info);

/**
* Funcion que obtiene la extension de un fichero
* nombre_f : Nombre del fichero
*
* Devuelve la extension si todo ha ido correctamente y una string vacia en otro caso
*/
char* get_extension(char* nombre_f);

/**
* Se encarga de procesar cuando ha habido un error en una peticion
* server_name: nombre del servidor
* sock: socket que usa
* clean_path: directorio raiz
* num_error: numero del error
* version: version
* tam_buff: tamanio maximo del buffer
*
* Devulevo 0 si todo ha ido bien, -1 en caso de error
*/
int respuesta_error(char* server_name, int sock, char* cleanpath, int num_error, int version, int tam_buff);

/**
* Se encarga de procesar las peticiones GET
* servidor: nombre del servidor
* sock: socket que usa
* ruta_fichero: ruta del fichero
* path_def: path definitivo
* argumentos: argumentos del script
* max_size: maximo tamanio del buffer
* minor_version: version
* timeout: timeout del servidor
*
* Devulevo 0 si todo ha ido bien, -1 en caso de error
*/
int respuesta_get(char* servidor, int sock, char* ruta_fichero, char* path_def, char* argumentos, int max_size, int minor_version, long int timeout);

/**
* Se encarga de procesar las peticiones POST
* server_name: nombre del servidor
* sock: socket que usa
* ruta_fichero: ruta del fichero
* cuerpo_peticion: el cuerpo de la peticion
* path_def: path definitivo
* argumentos: argumentos del script
* max_size: maximo tamanio del buffer
* minor_version: version
* timeout: timeout del servidor
*
* Devulevo 0 si todo ha ido bien, -1 en caso de error
*/
int respuesta_post(char* server_name, int sock, char* ruta_fichero, char* path_def, char* cuerpo_peticion, char* argumentos, int max_size, int minor_version, int timeout);

/**
* Se encarga de procesar una peticion OPTIONS
* server_name: nombre del servidor
* sock: socket que usa
* max_size: tam maximo del buffer
* minor_version: version
* metodos: puntero a una estructura metodos
*
* Devulevo 0 si todo ha ido bien, -1 en caso de error
*/
int respuesta_options(char* server_name, int sock, int max_size, int minor_version, Metodos* metodos);
#endif
