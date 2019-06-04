/**
* Autores: Victoria Pelayo e Ignacio Rabunnal
*
*/
#include <stdio.h> 
#include <sys/types.h> 
#include <unistd.h> 
#include <sys/wait.h> 
#include "myhttp_parser.h"

typedef struct _Metodos{
  int num_metodos ;
  char permitidos [3][15];
  char todos[50];
}Metodos;

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
int parsear_peticion(int sock, char* peticion, char* servidor, char* root, long int max_size, long int timeout){
  int i, pet_res;
  char *method, *path, *argumentos, *aux, *path_def, *pos_inter;
  char* cuerpo_peticion;
  char metodo[20], ruta_fichero[100];
  struct phr_header headers[50];
  int minor_version;
  size_t headers_len, method_len, path_len;
  Metodos metodos;


  headers_len = sizeof(headers) / sizeof(headers[0]);
  if(strcmp(peticion, "GET / HTTP/1.1\r\n") == 0 || strcmp(peticion, "GET / HTTP/1.1") == 0){
    strcpy(peticion, "GET /index.html HTTP/1.1\r\n");
  }

  pet_res = phr_parse_request(peticion, (size_t)strlen(peticion), (const char**)&method, &method_len, (const char**)&path, &path_len, &minor_version, headers, &headers_len, (size_t) 0);
  if(pet_res == -1 || strlen(peticion) == sizeof(peticion)){
    if(respuesta_error(servidor, sock, root, 404, minor_version, max_size) == -1){
      syslog(LOG_ERR, "Error en HTTP Response ERROR");
      return -1;
    }
    return -1;
  }

  cuerpo_peticion = peticion + pet_res;

  sprintf(metodo, "%.*s", (int)method_len, method);

  /*Hay que ver si se pasan argumentos detras de ?*/
  path_def = (char*)malloc((100)*sizeof(char));
  argumentos = (char*)malloc((100)*sizeof(char));
  aux = (char*)malloc((100)*sizeof(char));

  /*aux va a contener la direccion entera*/
  sprintf(aux, "%.*s", (int)path_len, path);

  /*Buscamos si hay un ?, pos_inter apunta al primer '?'*/
  pos_inter = strchr(aux, '?');

  /*Cuando no lo encuentra devuelve NULL*/
  if(pos_inter == NULL){
    strcpy(path_def, aux);
    strcpy(argumentos, "");
    free(aux);
  } else{
    /*Si hay ?, guardamos la ruta al script sin los argumentos en path_def
    y los argumentos en "argumentos"*/
    int tmp;
    tmp = (int) (pos_inter - aux) * sizeof(char);
    sprintf(path_def, "%.*s", tmp, aux);
    tmp = (int) ((aux + path_len) - pos_inter) * sizeof(char);
    sprintf(argumentos, "%.*s", tmp, pos_inter + 1);
    free(aux);
  }

  if(strcmp(path_def, "/") == 0){
    strcpy(path_def, "/index.html");
  }

  /*Guardamos la ruta completa del fichero*/
  sprintf(ruta_fichero, "%s%s", root, path_def);

  strcpy(metodos.todos, "GET,OPTIONS,POST");
  strcpy(metodos.permitidos[0], "GET");
  strcpy(metodos.permitidos[1], "OPTIONS");
  strcpy(metodos.permitidos[2], "POST");
  metodos.num_metodos = 3;

  /*Miramos que metodo es*/
  if(strcmp(metodo, "GET") == 0){
    for(i = 0; i < metodos.num_metodos; i++){
      if(strcmp(metodos.permitidos[i], "GET") == 0){
        if(respuesta_get(servidor, sock, ruta_fichero, path_def, argumentos, max_size, minor_version, timeout) == -1){
          syslog(LOG_ERR, "Error al obtener respuesta a peticion GET");
          free(path_def);
          free(argumentos);
          return -1;
        }
      }
    }
  }
  else if(strcmp(metodo, "POST") == 0){
    for(i = 0; i < metodos.num_metodos; i++){
      if(strcmp(metodos.permitidos[i], "POST") == 0){
        if(respuesta_post(servidor, sock, ruta_fichero, path_def, cuerpo_peticion, argumentos, max_size, minor_version, timeout) == -1){
          syslog(LOG_ERR, "Error al obtener respuesta a peticion POST");
          free(path_def);
          free(argumentos);
          return -1;
        }
      }
    }
  }
  else if(strcmp(metodo, "OPTIONS") == 0){
    for(i = 0; i < metodos.num_metodos; i++){
      if(strcmp(metodos.permitidos[i], "OPTIONS") == 0){
        if(respuesta_options(servidor, sock, max_size, minor_version, &metodos) == -1){
          syslog(LOG_ERR, "Error al obtener respuesta a peticion OPTIONS");
          free(path_def);
          free(argumentos);
          return -1;
        }
      }
    }
  }
  else{
  	/*Metodo desconocido*/
    free(path_def);
  	free(argumentos);
  }
  return 0;
}

/**
* Devuelve la fecha
*/
char* get_date(){
  time_t actual = time(0);
  struct tm tm = *gmtime(&actual);
  char *buff = (char*)malloc(sizeof(char) * 35);

  if(buff == NULL){
    return NULL;
  }

  strftime(buff, 35, "%a, %d %b %Y %H:%M:%S %Z", &tm);
  return buff;
}


/**
* Funcion que obtiene la fecha de ultima modificacion de un fichero
* file_info : Estructura que contiene la informacion del fichero
*
* Devuelve la fecha si todo ha ido correctamente y NULL en otro caso
*/
char* get_ultima_mod(struct stat* file_info){
  char* aux;

  aux = (char*)malloc(sizeof(char)*35);
  if(aux == NULL){
    return NULL;
  }

  /*Copiamos en aux la fecha expresada en el formato adecuado*/
  strftime(aux, 35, "%a, %d %b %Y %H:%M:%S %Z", gmtime(&(file_info->st_ctime)));
  return aux;
}

/**
* Funcion que obtiene la extension de un fichero
* nombre_f : Nombre del fichero
*
* Devuelve la extension si todo ha ido correctamente y una string vacia en otro caso
*/
char* get_extension(char* nombre_f){
  char* ext;
  /*Guardamos en ext la parte del nombre despues del punto (la extension)*/
  strtok(nombre_f, ".");
  ext = strtok(NULL, ".");

  if(ext == NULL){
    return "";
  }

  if(strcmp(ext, "txt") == 0){
    return "text/plain";
  }
  else if(strcmp(ext, "html") == 0 || strcmp(ext, "htm") == 0){
    return "text/html";
  }
  else if(strcmp(ext, "gif") == 0){
    return "image/gif";
  }
  else if(strcmp(ext, "jpeg") == 0 || strcmp(ext, "jpg") == 0){
    return "image/jpeg";
  }
  else if(strcmp(ext, "mpeg") == 0 || strcmp(ext, "mpg") == 0){
    return "video/mpeg";
  }
  else if(strcmp(ext, "doc") == 0 || strcmp(ext, "docx") == 0){
    return "application/msword";
  }
  else if(strcmp(ext, "pdf") == 0){
    return "application/pdf";
  }
  else if(strcmp(ext, "py") == 0){
    return "py";
  }else if(strcmp(ext, "php") == 0){
    return "php";
  }else if(strcmp(ext, "sh") == 0){
    return "sh";
  }
  else{
    return "";
  }
}

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

int respuesta_get(char* servidor, int sock, char* ruta_fichero, char* path_def, char* argumentos, int max_size, int minor_version, long int timeout){
  int fd, len;
  char orden[10];
  int script_flag = NO_SCRIPT;
  char buffer_salida[max_size];
  char buffer_aux[max_size];
  struct stat file_info;
  struct timeval time_out;
  char* fecha;
  char* ultima_mod;
  char* extension;
  char comando[TAM_COMANDO];
  FILE* pipe;
  int pipe_d, tout_flag;
  fd_set set;


  /*Nos aseguramos de que el buffer de salida este limpio*/
  memset(buffer_salida, 0, max_size);

  fd = open(ruta_fichero, O_RDONLY);
  if(fd < 0){
    
    return -1;
  }

  /*Obtenemos informacion acerca del archivo recien abierto*/
  if(fstat(fd, &file_info) < 0){
    syslog(LOG_ERR, "Error al obtener informacion del fichero respuesta_get");
    return -1;
  }


  time_out.tv_sec = (time_t)timeout;
  time_out.tv_usec = 0;

  len = file_info.st_size;
  fecha = get_date();
  ultima_mod = get_ultima_mod(&file_info);
  extension = get_extension(ruta_fichero);

  /*Comprobamos que la extension este soportada*/
  if(strcmp(extension, "py") == 0){
    script_flag = SCRIPT;
    strcpy(orden, "python3");
    extension = "text/html";

  }else if(strcmp(extension, "php") == 0){
    script_flag = SCRIPT;
    strcpy(orden,"php");
    extension = "text/html";

  }else if(strcmp(extension, "sh") == 0){
    script_flag = SCRIPT;
    strcpy(orden,"bash");
    extension = "text/html";

  }else if(strcmp(extension, "") == 0){
    if(respuesta_error(servidor, sock, path_def, 404, minor_version, max_size) < 0){
      syslog(LOG_ERR, "Error en la respuesta de error");
    
      free(fecha);
      free(ultima_mod);
      return -1;
    }
  
    free(fecha);
    free(ultima_mod);
    return -1;
  }

  /*Aqui iran mas shits de scripts junto con el bloque*/

  if(script_flag == NO_SCRIPT){
    /*Imprimimos las cabeceras en el buffer de salida y enviamos*/
    sprintf(buffer_salida, "HTTP/1.%d 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %lu\r\nConnection: keep-alive\r\nContent-Type: %s\r\n\r\n", minor_version, fecha, servidor, ultima_mod, len*sizeof(char), extension);
    if(enviar(sock, buffer_salida, strlen(buffer_salida)*sizeof(char)) < 0){
      syslog(LOG_ERR, "Error al enviar las cabeceras\n");
    
      free(fecha);
      free(ultima_mod);
      return -1;
    }

    /*Limpiamos el buffer de salida para utilizarlo al leer el fichero*/
    len = max_size;
    memset(buffer_salida, 0, max_size);

    /*Vamos enviando el fichero al socket a trozos. Ahora usamos len para comprobar si todavia queda algo por leer en el fichero*/
    while(len == max_size){
      len = read(fd, buffer_salida, max_size);

      /*Obviamos el caso len = 0 ya que no tiene sentido enviar nada ni es un error de lectura*/
      if(len < 0){
        syslog(LOG_ERR, "Error al leer el fichero\n");
      
        free(fecha);
        free(ultima_mod);
        return -1;
      }
      else if(len > 0){
        if(enviar(sock, buffer_salida, len) < 0){
          syslog(LOG_ERR, "Error enviar datos del fichero\n");
        
          free(fecha);
          free(ultima_mod);
          return -1;
        }
      }

      /*Limpiamos el buffer para llenarlo con nuevos datos leidos*/
      memset(buffer_salida, 0, max_size);
    }
  }else if(script_flag == SCRIPT){

  	  sprintf(comando, "echo %s | %s %s \"%s\"",argumentos,orden,path_def+1, argumentos);
      pipe = popen(comando, "r");
      if(pipe == NULL){
        syslog(LOG_ERR, "Error al crear la tubería");
      
        free(fecha);
        free(ultima_mod);
        return -1;
      }

      pipe_d = fileno(pipe);
      FD_ZERO(&set);
      FD_SET(pipe_d, &set);
      tout_flag = select(pipe_d + 1, &set, NULL, NULL, &time_out);
      if(tout_flag < 0){
        syslog(LOG_ERR, "Error al aplicar select");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;

      }else if(tout_flag == 0){
        syslog(LOG_ERR, "Timeout excedido");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;

      }else{

        /*La ejecucion ha terminado antes de time_out*/
        /*leemos contenido tuberia y guardamos en buffer_salida*/
        len = fread((void*)buffer_salida, 1, max_size, pipe);
        if(len < 0){
          syslog(LOG_ERR, "Error al leer la salida");
        
          free(fecha);
          free(ultima_mod);
          pclose(pipe);
          return -1;
        }


        sprintf(buffer_aux, "HTTP/1.%d 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %lu\r\nConnection: keep-alive\r\nContent-Type: %s\r\n\r\n", minor_version, fecha, servidor, ultima_mod, len*sizeof(char), extension);
        if(enviar(sock, buffer_aux, strlen(buffer_aux)) < 0){
          syslog(LOG_ERR, "Error al enviar la cabecera de la respuesta del script");
        
          free(fecha);
          free(ultima_mod);
          pclose(pipe);
          return -1;
        }

        strcat(buffer_salida, "\r\n\r\n");
        len +=5;

        if(enviar(sock, buffer_salida, len) < 0){
          syslog(LOG_ERR, "Error al enviar la respuesta del script");
        
          free(fecha);
          free(ultima_mod);
          pclose(pipe);
          return -1;
        }
      }

      if(pclose(pipe) < 0){
        syslog(LOG_ERR, "Error al cerrar la tuberia");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
      }
    }



  free(fecha);
  free(ultima_mod);

  return 0;
}

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
int respuesta_post(char* server_name, int sock, char* ruta_fichero, char* path_def, char* cuerpo_peticion, char* argumentos, int max_size, int minor_version, int timeout){
  int fd, len;
  int script_flag = NO_SCRIPT;
  char buffer_salida[max_size];
  char buffer_aux[max_size];
  struct stat file_info;
  struct timeval time_out;
  char* fecha;
  char* ultima_mod;
  char* extension;
  char orden[10];
  char comando[TAM_COMANDO];
  FILE* pipe;
  int pipe_d, tout_flag;
  fd_set set;

  /*Nos aseguramos de que el buffer de salida este limpio*/
  memset(buffer_salida, 0, max_size);

  fd = open(ruta_fichero, O_RDONLY);
  if(fd < 0){
    syslog(LOG_ERR, "Error al abrir el archivo para la respuesta post");
    if(respuesta_error(server_name, sock, path_def, 404, minor_version, max_size)){
      syslog(LOG_ERR, "Error en la respuesta de error");
      return -1;
    }
    return -1;
  }

  /*Obtenemos informacion acerca del archivo recien abierto*/
  if(fstat(fd, &file_info) < 0){
    syslog(LOG_ERR, "Error al obtener informacion del fichero respuesta_get");
  
    return -1;
  }

  time_out.tv_sec = (time_t)timeout;
  time_out.tv_usec = 0;

  fecha = get_date();
  ultima_mod = get_ultima_mod(&file_info);
  extension = get_extension(ruta_fichero);

  /*Comprobamos la extension del fichero, si es un script actualizamos el flag y si
  la extension no esta soportada devolvemos error*/
  if(strcmp(extension, "py") == 0){
    script_flag = SCRIPT;
    strcpy(orden,"python3");
    extension = "text/html";

  }else if(strcmp(extension, "php") == 0){
    script_flag = SCRIPT;
    strcpy(orden,"php");
    extension = "text/html";

  }else if(strcmp(extension, "sh") == 0){
    script_flag = SCRIPT;
    strcpy(orden,"bash");
    extension = "text/html";

  }else if(strcmp(extension, "") == 0){
  
    free(fecha);
    free(ultima_mod);
    return -1;
  }

  if(script_flag == NO_SCRIPT){
    if(respuesta_error(server_name, sock, path_def, 404, minor_version, max_size) < 0){
    
      free(fecha);
      free(ultima_mod);
      return -1;
    }

  }else if(script_flag == SCRIPT){
    sprintf(comando, "echo %s | %s %s \"%s\"",cuerpo_peticion,orden,path_def+1,cuerpo_peticion);

    pipe = popen(comando, "r");
    if(pipe == NULL){
      syslog(LOG_ERR, "Error abriendo el pipe");
    
      free(fecha);
      free(ultima_mod);
      return -1;
    }

    /*Configuramos ciertos parametros para poder llamar correctamente a select,
    la funcion que gestiona el timeout*/
    pipe_d = fileno(pipe);
    FD_ZERO(&set);
    FD_SET(pipe_d, &set);
    tout_flag = select(pipe_d + 1, &set, NULL, NULL, &time_out);
    if(tout_flag < 0){
      syslog(LOG_ERR, "Error en select respuesta post");
    
      free(fecha);
      free(ultima_mod);
      pclose(pipe);
      return -1;

    }else if(tout_flag == 0){
      syslog(LOG_ERR, "Tiempo de ejecucion sobrepasado.\n");
      if(respuesta_error(server_name, sock, path_def, 800, minor_version, max_size) < 0){
        syslog(LOG_ERR, "Error en la respuesta de error.\n");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
      }
    
      free(fecha);
      free(ultima_mod);
      pclose(pipe);
      return -1;

    }else{
      /*Si no se ha sobrepasdo el timeout*/
      len = fread(buffer_salida, 1, max_size, pipe);
      if(len < 0){
        syslog(LOG_ERR, "Error al leer la salida del pipe.\n");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
      }

      /*Escribimos las cabeceras en el buffer auxiliar y enviamos las cabeceras y el resultado del script*/
      sprintf(buffer_aux, "HTTP/1.%d 200 OK\r\nDate: %s\r\nServer: %s\r\nLast-Modified: %s\r\nContent-Length: %lu\r\nConnection: keep-alive\r\nContent-Type: %s\r\n\r\n", minor_version, fecha, server_name, ultima_mod, len*sizeof(char), extension);
      if(enviar(sock, buffer_aux, strlen(buffer_aux)) < 0){
        syslog(LOG_ERR, "Error al enviar cabeceras de la respuesta post.\n");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
      }

      if(enviar(sock, buffer_salida, len) < 0){
        syslog(LOG_ERR, "Error al enviar resultado de la respuesta post.\n");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
      }
    }

    /*Cerramos el pipe una vez finalizado el envio*/
    if(pclose(pipe) < 0){
        syslog(LOG_ERR, "Error al cerrar el pipe respuesta post.\n");
      
        free(fecha);
        free(ultima_mod);
        pclose(pipe);
        return -1;
    }

  }


  free(fecha);
  free(ultima_mod);
  return 0;
}

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
int respuesta_error(char* server_name, int sock,char* cleanpath, int num_error, int version, int tam_buff){
  char html_code[1000];
  char buf_salida[tam_buff];
  char* date = get_date();

  switch(num_error){

    case 400:
      sprintf(html_code, "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n<html><head>\n<title>400 Bad Request</title>\n</head><body>\n<h1>Bad Request</h1>\n<p>The server could not understand the request due to invalid syntax.</p>\n</body></html>");
      sprintf(buf_salida, "HTTP/1.%d 400 Bad Request\r\nDate: %s\r\nServer: %s\r\nAllow: GET,POST,OPTIONS\r\nContent-Length: %lu\r\nConnection: close\r\nContent-Type: text/html\r\n\r\n%s\r\n", version, date, server_name, sizeof(char)*strlen(html_code), html_code);

      break;

    // Archivo no encontrado
    case 404:
      sprintf(html_code, "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n<html lang = \"en\"><head>\n<title>404 not found</title>\n</head><body>\n<h1>404 RESOURCE NOT FOUND</h1>\n<p> The server could not found the resource you requested.</p>\n</body></html>");
      sprintf(buf_salida, "HTTP/1.%d 404 Not Found\r\nDate: %s\r\nServer: %s\r\nAllow: GET,POST,OPTIONS\r\nContent-Length: %lu\r\nConnection: close\r\nContent-Type: text/html\r\n\r\n%s\r\n", version, date, server_name, sizeof(char)*strlen(html_code), html_code);

      break;

    default:
      syslog(LOG_ERR, "Error desconocido");
      free(date);
      return -1;
  }

  if(enviar(sock, buf_salida, strlen(buf_salida)) < 0){
    free(date);
    syslog(LOG_ERR, "Error al enviar respuesta de error");
    return -1;
  }

  free(date);
  return 0;
}


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
int respuesta_options(char* server_name, int sock, int max_size, int minor_version, Metodos* metodos){
  char buf_salida[max_size];
  char* fecha = get_date();

  sprintf(buf_salida, "HTTP/1.%d 200 OK\r\nDate: %s\r\nServer: %s\r\nAllow: %s\r\nContent-Length: 0\r\nConnection: close\r\nContent-Type: text/plain\r\n\r\n", minor_version, fecha, server_name, metodos->todos);
  if(enviar(sock, buf_salida, strlen(buf_salida)*sizeof(char)) < 0){
    syslog(LOG_ERR, "Error al enviar respuesta options");
    free(fecha);
    return -1;
  }

  free(fecha);
  return 0;
}


