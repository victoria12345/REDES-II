#######################################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
#######################################################################################

import cv2
import socket as sk
import time
import threading as th
from PIL import Image, ImageTk
import servidor_desc as DS
import video_manager as video

class control_line:
	"""
	CLASE: control_line
	DESCRIPCION: Implementa la linea de control para la transmision de video
	(play, pausa...) mediante una comunicacion TCP
	"""
	#MACRO DE LA COLA DEL SOCKET
	cola = 10

	#MACRO PARA SABER SI EL VIDEO SE ESTA ENVIANDO
	env_video = 0

	#ATRIBUTOS NECESAIRIOS PARA LAS LLAMADAS
	puerto_llamada = None
	ip_llamada = None

	sock_envio = None
	sock_recepcion = None
	d_server = None
	nuestra_IP = None
	nuestroUDPport = None
	listen_port = None
	pausa = None
	finalizacion = None
	gui = None
	video_manager = None

	#ruta del video que enviamos
	ruta = None

	def __init__(self, gui, ip, listen_port, ds_port, srcUDPport):
		#MyUDPport?

		self.gui = gui
		self.nuestra_IP = ip
		self.listen_port = listen_port
		self.d_server = DS.servidor_desc(ds_port)
		self.nuestroUDPport = srcUDPport

		self.sock_recepcion = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		self.sock_recepcion.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
		self.sock_recepcion.bind(('', int(self.listen_port)))
		self.sock_recepcion.listen(self.cola)

	###############################################
	###############################################
	###############################################
	####### FUNCIONES PARA ENVIAR COMANDOS  #######
	###############################################
	###############################################
	###############################################

	def enviar_comando(self, comando, dest_IP, dest_port):
		"""
			FUNCION: enviar_comando(self,comando,dest_IP,dest_port)
			DESCRIPCION: Envia un comando a otro usuario

			comando: Comando que se desea enviar
			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
		"""

		#Imprimimos el comando enviado, esto es temporal
		#Si se desea se puede comentar la linea de abajo
		#print(comando)

		try:
			self.sock_envio = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
			self.sock_envio.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
			self.sock_envio.settimeout(10)
			self.sock_envio.connect((dest_IP, int(dest_port)))
			self.sock_envio.settimeout(None)

		except(OSError, ConnectionRefusedError):
			return "ERROR"

		self.sock_envio.send(comando.encode('utf-8'))
		self.sock_envio.close()
		return "OK"

	def enviar_CALLING(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_CALLING(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		comando = "CALLING {} {}".format(nick, self.nuestroUDPport)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		self.gui.app.setStatusbar("Llamando...", 2)
		if ret == "ERROR":
			return "ERROR"

	def enviar_video_CALLING(self,dest_IP, dest_port, ruta_video,nick):
		"""
			FUNCION: enviar_video_CALLING(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando llamada de enviar video

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
			ruta_video: ruta del video que se quiere enviar
		"""
		if ruta_video == ():
			return "ERROR"

		comando = "CALLING {} {}".format(nick, self.nuestroUDPport)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		self.gui.app.setStatusbar("Llamando...", 2)
		if ret == "ERROR":
			return "ERROR"

		self.env_video = 1
		self.ruta = ruta_video


	def enviar_CALL_HOLD(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_HOLD(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando pausar la llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		if self.gui.en_llamada == True:
			comando = "CALL_HOLD {}".format(nick)
			self.gui.app.setStatusbar("Llamada en pausa", 2)
			ret = self.enviar_comando(comando, dest_IP, dest_port)
			if ret == "ERROR":
				return "ERROR"
			self.pausa.set()

	def enviar_CALL_RESUME(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_RESUME(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando de reanudar la llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		comando = "CALL_RESUME {}".format(nick)
		self.gui.app.setStatusbar("En llamada", 2)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		if ret == "ERROR":
			return "ERROR"
		self.pausa.clear()

	def enviar_CALL_END(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_END(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando de finalizar la llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		if self.gui.en_llamada == True:

			#Reanudamos la llamada para colgar
			if self.pausa.isSet() == True:
				comando = "CALL_RESUME {}".format(nick)
				self.gui.app.setStatusbar("En llamada", 2)
				ret = self.enviar_comando(comando, dest_IP, dest_port)
				if ret == "ERROR":
					return "ERROR"
				self.pausa.clear()

			comando = "CALL_END {}".format(nick)
			ret = self.enviar_comando(comando, dest_IP, dest_port)
			self.gui.app.setStatusbar(" ", 2)
			if ret == "ERROR":
				return "ERROR"
			self.finalizacion.set()
			self.en_llamada = False

	def enviar_CALL_ACCEPTED(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_CALL_ACCEPTED(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando de aceptar la llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		comando = "CALL_ACCEPTED {} {}".format(nick, self.nuestroUDPport)
		self.gui.app.setStatusbar("En llamada", 2)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		if ret == "ERROR":
			return "ERROR"

	def enviar_CALL_DENIED(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_CALL_DENIED(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando de rechazar la llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		comando = "CALL_DENIED {}".format(nick)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		if ret =="ERROR":
			return "ERROR"

	def enviar_CALL_BUSY(self, dest_IP, dest_port, nick):
		"""
			FUNCION: enviar_CALL_BUSY(self,dest_IP,dest_port,nick)
			DESCRIPCION: Envia comando cuando el usuario esta ya ocupado
						 con otra llamada

			dest_IP: IP destino, a la que va dirigida el comando
			dest_port: puerto destino, donde va dirigido el comando
			nick: nick del usuario que envia el comando
		"""
		comando = "CALL_BUSY {}".format(nick)
		ret = self.enviar_comando(comando, dest_IP, dest_port)
		if ret == "ERROR":
			return "ERROR"


	#############S#####################################################
	##################################################################
	##################################################################
	####### FUNCIONES PARA GESTIONAR LA RECEPCION DE COMANDOS  #######
	##################################################################
	##################################################################
	##################################################################


	def gestionar_CALLING(self, nick, rcv_port):
		"""
			FUNCION: gestionar_CALLING(self,nick, rcv_port)
			DESCRIPCION: Gestiona cuando se recibe la peticion de iniciar
						 una llamada

			nick: nick del usuario que nos quiere llamar
			rcv_port: Puerto donde se recibe la llamada
		"""

		#Obtenemos la informacion necesaria del otro usuario
		u_info = self.d_server.obtener_info_usuario(nick)
		ip = u_info['ip_address']
		port = u_info['port']
		u_nick = u_info['nick']
		self.puerto_llamada = port #puerto destino de la llamada
		self.ip_llamada = ip #ip destino en la llamada

		if self.gui.en_llamada == False:
			ret = self.gui.app.yesNoBox("Llamada", "Llamada entrante de {}\n¿Aceptar?".format(nick), parent = None)

			if ret == True:
				#Aceptamos la llamada
				self.gui.dest_IP = ip
				self.gui.dest_port = port
				self.gui.app.setStatusbar("Llamada en proceso", 2)
				self.enviar_CALL_ACCEPTED(ip, port, self.gui.nick)
				self.gui.en_llamada = True

				self.video_manager = video.video_manager(self.gui, self.nuestroUDPport)
				self.video_manager.configurar_destinatario(ip, rcv_port)
				#Creamos los eventos de pausa y finalizacion
				self.pausa = th.Event()
				self.finalizacion = th.Event()
				#Creamos los hilos que gestionan la transmision y recepcion de video y el tiempo de llamada
				self.thread_envia_video = th.Thread(target = self.video_manager.transmitir_video, args = (self.pausa, self.finalizacion))
				self.thread_recepcion_video = th.Thread(target = self.video_manager.llenar_buf_recepcion, args = (self.pausa, self.finalizacion))
				self.thread_muestra_video = th.Thread(target = self.video_manager.recibir_video, args = (self.pausa, self.finalizacion))
				self.thread_tiempo = th.Thread(target = self.gestion_tiempo_llamada, args = (self.pausa, self.finalizacion))
				#Demonizamos los hilos y los iniciamos
				self.thread_recepcion_video.setDaemon(True)
				self.thread_muestra_video.setDaemon(True)
				self.thread_envia_video.setDaemon(True)
				self.thread_tiempo.setDaemon(True)
				self.thread_recepcion_video.start()
				self.thread_muestra_video.start()
				self.thread_envia_video.start()
				self.thread_tiempo.start()

			elif ret == False:
				self.enviar_CALL_DENIED(ip, port, u_nick)

		else:
			self.enviar_CALL_BUSY(ip, port, u_nick)

	def gestionar_CALL_HOLD(self,nick):
		"""
			FUNCION: gestionar_CALL_HOLD(self)
			DESCRIPCION: Gestiona cuando se recibe la peticion de pausar
						 una llamada

			nick: nick del usuario que la ha pausado

		"""
		if self.gui.en_llamada == True and self.pausa.isSet() == False:
			self.gui.app.setStatusbar("Llamada en pausa", 2)
			self.pausa.set()
			self.gui.app.infoBox("PAUSA", "{} ha pausado la llamada".format(nick))

	def gestionar_CALL_RESUME(self,nick):
		"""
			FUNCION: gestionar_CALL_RESUME(self)
			DESCRIPCION: Gestiona cuando se recibe la peticion de reanudar
						 una llamada

			nick: nick del usuario que la ha reanudado
		"""
		if self.gui.en_llamada == True and self.pausa.isSet() == True:
			self.gui.app.setStatusbar("Llamada en proceso", 2)
			self.pausa.clear()
			self.gui.app.infoBox("PLAY", "{} ha reanudado la llamada".format(nick))


	def gestionar_CALL_END(self,nick):
		"""
			FUNCION: gestionar_CALL_END(self)
			DESCRIPCION: Gestiona cuando se recibe la peticion de finalizar
						 una llamada

			nick: nick del usuario que la termina

		"""
		if self.gui.en_llamada == True:
			self.gui.app.setStatusbar("", 2)
			self.finalizacion.set()
			self.gui.en_llamada = False
			self.gui.app.infoBox("FIN", "{} ha finalizado la llamada".format(nick))

	def gestionar_CALL_ACCEPTED(self, nick, port_UDP):
		"""
		FUNCION: gestionar_CALL_ACCEPTED(self,nick, port_UDP)
		DESCR: gestiona la accion de aceptar una Llamada

		ARGS_IN:
			nick: usuario que aceptar
			port_UDP: puerto UDP para recibir video
		"""
		u_info = self.d_server.obtener_info_usuario(nick)
		ip = u_info['ip_address']
		port = u_info['port']
		u_nick = u_info['nick']
		self.puerto_llamada = port #puerto destino de la llamada
		self.ip_llamada = ip #ip destino en la llamada

		if self.gui.en_llamada == False:
			self.gui.app.setStatusbar("Llamada en proceso", 2)
			self.gui.en_llamada = True

			self.video_manager = video.video_manager(self.gui, self.nuestroUDPport)
			self.video_manager.configurar_destinatario(ip, port_UDP)

			#Comprobamos si el video ya se esta enviando
			if self.env_video == 0:
				self.video_manager.set_ruta_video(None, 0)
			#Solo toma valores 0 o 1
			elif self.env_video == 1:
				self.video_manager.set_ruta_video(self.ruta, 1)
				self.env_video = 0
			#Creamos los eventos de pausa y finalizacion
			self.pausa = th.Event()
			self.finalizacion = th.Event()
			#Creamos los hilos que gestionan la transmision y recepcion de video y el tiempo de llamada
			self.thread_muestra_video = th.Thread(target = self.video_manager.recibir_video, args = (self.pausa, self.finalizacion))
			self.thread_recepcion_video = th.Thread(target = self.video_manager.llenar_buf_recepcion, args = (self.pausa, self.finalizacion))
			self.thread_envia_video = th.Thread(target = self.video_manager.transmitir_video, args = (self.pausa, self.finalizacion))
			self.thread_tiempo = th.Thread(target = self.gestion_tiempo_llamada, args = (self.pausa, self.finalizacion))
			#Demonizamos los hilos y los iniciamos
			self.thread_recepcion_video.setDaemon(True)
			self.thread_muestra_video.setDaemon(True)
			self.thread_envia_video.setDaemon(True)
			self.thread_tiempo.setDaemon(True)
			self.thread_recepcion_video.start()
			self.thread_muestra_video.start()
			self.thread_envia_video.start()
			self.thread_tiempo.start()


	def gestionar_CALL_DENIED(self, nick):
		"""
			FUNCION: gestionar_CALL_DENIED(self)
			DESCRIPCION: Gestiona cuando deniegan la llamada

			nick: nick del usuario que rechaza la llamada
		"""
		self.gui.app.infoBox("Llamada rechazada", "{} ha rechazado tu llamada".format(nick), parent = None)
		self.gui.app.setStatusbar("", 2)

	def gestionar_CALL_BUSY(self, nick):
		"""
			FUNCION: gestionar_CALL_DENIED(self)
			DESCRIPCION: Gestiona cuando se recibe que el otro usuario
						 esta ocupado en otra llamada

			nick: nick del usuario que esta ocupado
		"""
		self.en_llamada = False
		self.gui.app.infoBox("Llamada ocupada", "{} esta ocupado en otra llamada, intentalo mas tarde".format(nick), parent = None)
		self.gui.app.setStatusbar("", 2)

	def gestionar_peticion(self, msg):
		"""
			FUNCION: gestionar_peticion(self,msg)
			DESCRIPCION: Gestiona una peticion

			msg: peticion que se recibe
		"""
		info = msg.split(" ")

		#print (msg)

		comando = info[0]
		nick = info[1]

		if comando == "CALLING":
			#unica peticion que lleva un tercer argumento
			port_UDP = info[2]
			self.gestionar_CALLING(nick, port_UDP)
			return

		elif comando == "CALL_HOLD":
			self.gestionar_CALL_HOLD(nick)
			return

		elif comando == "CALL_RESUME":
			self.gestionar_CALL_RESUME(nick)
			return

		elif comando == "CALL_END":
			self.gestionar_CALL_END(nick)
			return

		elif comando == "CALL_ACCEPTED":
			port_UDP = info[2]
			self.gestionar_CALL_ACCEPTED(nick, port_UDP)
			return

		elif comando == "CALL_DENIED":
			self.gestionar_CALL_DENIED(nick)
			return

		elif comando == "CALL_BUSY":
			self.gestionar_CALL_BUSY(nick)
			return

	def gestion_tiempo_llamada(self, pausa, finalizacion):
		"""
			FUNCION: gestionar_CALL_DENIED(self)
			DESCRIPCION: Gestiona el tiempo de duracion de la llamada

			pausa: evento de pausa de la llamada
			finalizacion: evento de finalizacion de la llamada
		"""
		segundos = 00
		minutos = 00
		horas = 00

		while not finalizacion.isSet():
			while pausa.isSet():
				if finalizacion.isSet():
					break
			#vamos aumentando 1 segundo cuando no estamos en pausa
			time.sleep(1)
			segundos += 1
			if segundos == 60:
				segundos = 0
				minutos += 1
				if minutos == 60:
					minutos = 0
					horas += 1

			#actualizamos la duracion
			mensaje = "En llamada durante: {:02}:{:02}:{:02}".format(horas, minutos, segundos)
			self.gui.app.setStatusbar(mensaje, 1)

		#Cuando acaba la llamada quitamos el tiempo que duro 
		mensaje = "Ninguna llamada en proceso"
		self.gui.app.setStatusbar(mensaje, 1)

	def escucha_peticiones(self, evento):
		"""
			FUNCION: escuchar_peticiones(self,evento)
			DESCRIPCION: Escucha las peticiones que van llegando

			evento: evento que hemos recibido
		"""
		while not evento.isSet():
			#Aceptamos y leemos la peticion
			conn, address = self.sock_recepcion.accept()
			peticion = conn.recv(1024)

			#Imprimimos la peticion y la gestionamos
			if peticion:
				#print(peticion.decode('utf-8'))
				self.gestionar_peticion(peticion.decode('utf-8'))
