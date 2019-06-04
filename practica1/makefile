###############################################################################
# Makefile con auto-deteccion de dependencias: nunca querras usar otro
# (de tipo .h; las de linkado hay que enumerarlas)
# Ver http://www.cs.washington.edu/orgs/acm/tutorials/dev-in-unix/makefiles.html
################################################################################

# banderas de compilacion (PUEDE SER UTIL CAMBIARLAS)
CC = gcc
#ifdef ENTREGA
CFLAGS = -Wall -g -I .
LDLIBS = -lm
#else
CFLAGS = -Wall -g -I .
#-DENTREGA
LDLIBS = -lm -pthread
#endif

# fuentes a considerar (si no se cambia, todos los '.c' del directorio actual)
SRC = ./src/
INC = ./include/

OBS = server.o demonio.o myhttp_parser.o picohttpparser.o socket.o thread_pool.o

all: server
	rm -f *.o

server: $(OBS)
	gcc $(CFLAGS) -o server $^ -pthread -lm

thread_pool.o: $(SRC)thread_pool.c $(INC)thread_pool.h
	@echo -n compilando thread_pool.c...
	@gcc $(CFLAGS) -I./include -c $(SRC)thread_pool.c
	@echo [OK]

demonio.o: $(SRC)demonio.c $(INC)demonio.h
	@echo -n compilando demonio.c...
	@gcc $(CFLAGS) -I./include -c $(SRC)demonio.c
	@echo [OK]

myhttp_parser.o: $(SRC)myhttp_parser.c $(INC)myhttp_parser.h
	@echo -n compilando myhttp_parser.c...
	@gcc $(CFLAGS) -I./include -c $(SRC)myhttp_parser.c
	@echo [OK]

picohttpparser.o: $(SRC)picohttpparser.c $(INC)picohttpparser.h
	@echo -n compilando picohttpparser.c...
	@gcc $(CFLAGS) -I./include -c $(SRC)picohttpparser.c
	@echo [OK]

socket.o: $(SRC)socket.c $(INC)socket.h
	@echo -n compilando socket.c...
	@gcc $(CFLAGS) -I./include -c $(SRC)socket.c
	@echo [OK]

server.o: server.c $(INC)socket.h $(INC)thread_pool.h $(INC)demonio.h $(INC)myhttp_parser.h
	@echo -n compilando server.c...
	@gcc $(CFLAGS) -I./include -c server.c
	@echo [OK]

clean:
	rm -f *.o server

