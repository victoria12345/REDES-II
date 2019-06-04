##############################################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
##############################################################################################

# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import threading as th
import os
import signal
import socket as sk
import time
import sys

sys.path.insert(0, './src')

import video_manager as video
import control_line as control
import servidor_desc as DS

class VideoClient(object):
	"""
	CLASE: VideoClient
	DESCRIPCION: Implementa la interfaz grafica de la aplicacion.
	"""
	CAM_IMG = "imgs/cam.gif"
	VIDEO_IMG = "imgs/video.gif"
	LOGO = "imgs/birdcall.gif"

	PUERTO_TCP = 8080
	PUERTO_UDP = 8001

	nuestra_IP = None
	dest_IP = None
	dest_port = None
	d_server = None
	window_size = None
	nick = None
	contrasenia = None
	user_list = []

	video_manager = None
	control_line = None

	en_llamada = False

	evento_hilo = None
	hilo_comand=None

	def __init__(self, window_size):
		self.app = gui("BirdCall", window_size)
		self.app.setResizable(canResize=True)
		self.app.setLocation("CENTER")
		self.app.setSticky("")
		self.app.setStretch('Both')
		self.app.setBg("MediumAquamarine")
		self.app.addImage("logo", self.LOGO)
		self.app.addLabelEntry("Username")
		self.app.addLabelSecretEntry("Password")
		self.app.addButtons(["Login","Salir"], self.buttonsCallback)
		self.app.setButtonBg("Login", "PeachPuff")
		self.app.setButtonBg("Salir", "PeachPuff")


		#Obtenemos nuestra IP local
		sock_aux = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		sock_aux.connect(("vega.ii.uam.es", 8000))
		self.nuestra_IP = sock_aux.getsockname()[0]
		sock_aux.close()

		self.d_server = DS.servidor_desc(8000)
		self.user_list = self.d_server.listar_usuarios()
		self.control_line = control.control_line(self, self.nuestra_IP, self.PUERTO_TCP, 8000, self.PUERTO_UDP)


	def login_enviar_REGISTER(self):
		"""
			FUNCION: login_enviar_REGISTER(self)
			DESCRIPCION: Registra a un usuario en la aplicacion
						 si ese usuario ya estaba registrado simplemente comprueba
						 que haya introducido la contrasenna correctamente
		"""
		self.nick = self.app.getEntry("Username")
		self.contrasenia = self.app.getEntry("Password")
		if self.nick == "" or self.contrasenia == "":
			self.app.errorBox("Error datos",  "Error al registrar, introduzca datos validos")
			return "ERROR"

		#Llamamos a la funcion registrar usuario (/iniciar sesion)
		respuesta = self.d_server.registrar_usuario(self.nick, self.contrasenia, self.nuestra_IP, self.PUERTO_TCP)
		if respuesta == "ERROR":
			self.app.errorBox("Error registrar", "Error, el registro no se ha podido realizar")
			return "ERROR"

		if respuesta == "ERROR_CONTRA":
			self.app.errorBox("Error registrar", "Error, la contraseña introducida es incorrecta")
			return "ERROR"

		self.mostrar_pantalla_principal()

		#Iniciamos hilo que se encargue de escuchar peticiones
		self.evento_hilo = th.Event()
		self.hilo_comand = th.Thread(target = self.control_line.escucha_peticiones, args = (self.evento_hilo,))
		self.hilo_comand.setDaemon(True)
		self.hilo_comand.start()

		return "OK"

	def buscar_usuario(self):
		"""
			FUNCION: buscar_usuario(self)
			DESCRIPCION: Busca a un usuario en funcion de su nombre
		"""
		usuario = self.app.getEntry("Busqueda")
		self.app.clearListBox("Lista de usuarios")
		for item in self.user_list:
			if usuario.lower() in item.lower():
				self.app.addListItem("Lista de usuarios", item)
				self.app.setListItemBg("Lista de usuarios", item, "Gold")

	def llamar(self):
		"""
			FUNCION: llamar(self)
			DESCRIPCION: Llama a un usuario que se haya seleccionado
		"""
		usuarios = self.app.getListBox("Lista de usuarios")
		if usuarios:
			u = usuarios[0]
			if u != None:
				u_info = self.d_server.obtener_info_usuario(u)
				self.dest_port = u_info['port']
				self.dest_IP = u_info['ip_address']

				if self.en_llamada == True:
					self.app.errorBox("Error2", "No puedes llamar a un usuario mientras estas en llamada. Debes colgar antes.")
					return

				if self.dest_IP == None:
					self.app.errorBox("ErrorIP", "No ha sido posible obtener la IP de {}".format(u))
					return

				#Llamamos a la funcion que envia el comando de llamar
				self.control_line.enviar_CALLING(self.dest_IP, self.dest_port, self.nick)


			else:
				self.app.errorBox("Error_usr", "Tienes que seleccionar a un usuario en la lista para llamar")

		else:
			self.app.errorBox("Error_usr", "Tienes que seleccionar a un usuario en la lsita para llamar")

	def colgar(self):
		"""
			FUNCION: colar(self)
			DESCRIPCION: Si se estaba llamando/en una llamada, lo finaliza
		"""
		self.control_line.enviar_CALL_END(self.control_line.ip_llamada, self.control_line.puerto_llamada, self.nick)
		self.en_llamada = False


	def pausar(self):
		"""
			FUNCION: pausar(self)
			DESCRIPCION: pausa una llamada
		"""
		if self.en_llamada == True:
			self.control_line.enviar_CALL_HOLD(self.dest_IP, self.dest_port, self.nick)

	def play(self):
		"""
			FUNCION: play(self)
			DESCRIPCION: le da al play de una llamada. 
		"""
		if self.en_llamada == True:
			self.control_line.enviar_CALL_RESUME(self.dest_IP, self.dest_port, self.nick)

	def salir(self):
		"""
			FUNCION: salir(self)
			DESCRIPCION: Sale de la aplicacion
						 Como decision de disenno el usuario no puede salir si esta en
						 una llamada
		"""
		# Comprobamos que no estuviese en uhna Llamada
		if self.en_llamada == True:
			self.app.errorBox("Error", "No puedes salir mientras estas en llamada")
			return
		self.app.stop()

	def mostrar_pantalla_principal(self):
		"""
			FUNCION: mostrar_pantalla_principal(self)
			DESCRIPCION: Muestra la pantalla principal de la aplicacion
		"""
		self.app.removeAllWidgets()
		self.app.setSticky("")
		self.app.setStretch('Both')
		self.app.setGuiPadding(10,10)

		# Preparacion del interfaz
		self.app.addImage("birdcall", self.LOGO, 0, 0)
		self.app.addLabel("usuario", "Usuario: {}".format(self.nick), 1, 0)
		self.app.addListBox("Lista de usuarios", self.user_list, 2, 0)
		self.app.addLabelEntry("Busqueda", 3, 0)

		self.video = self.app.addImage("Video", self.VIDEO_IMG, 0, 1, rowspan = 3)
		self.our_camera = self.app.addImage("Webcam", self.CAM_IMG, 0, 2, rowspan = 10)
		self.app.setPadding([5,5]) # padding outside the widget
		self.app.setInPadding([40,20]) # padding inside the widget

		# Anyadir los botones
		self.app.addButtons(["Buscar"], self.buttonsCallback, 4, 0)
		self.app.addButtons(["Enviar video", "Llamar", "Colgar", "Play", "Pause"], self.buttonsCallback, 3, 1)
		self.app.addButtons(["Salir"], self.buttonsCallback, 4, 2)
		self.app.setButtonBg("Buscar", "PeachPuff")
		self.app.setButtonBg("Enviar video", "PeachPuff")
		self.app.setButtonBg("Llamar", "PeachPuff")
		self.app.setButtonBg("Colgar", "PeachPuff")
		self.app.setButtonBg("Play", "PeachPuff")
		self.app.setButtonBg("Pause", "PeachPuff")
		self.app.setButtonBg("Salir", "PeachPuff")

		#Anyadimos la caja de opciones para los fps
		self.app.addOptionBox("FPS", ["15", "20", "30", "40"], 3, 2)
		self.app.setOptionBoxBg("FPS", "PeachPuff")


		# Barra de estado
		# Debe actualizarse con informacion util sobre la llamada (duracion, FPS, etc...)
		# Copypaste, may be useful cuando tengamos que controlar esas cosillas
		self.app.addStatusbar(fields=3)
		self.app.setStatusbar("FPS =", 0)
		self.app.setStatusbar("Ninguna llamada en proceso", 1)
		self.app.setStatusbar("...", 2)
		self.app.setStatusbarBg("PeachPuff", 0)
		self.app.setStatusbarBg("PeachPuff", 1)
		self.app.setStatusbarBg("PeachPuff", 2)

	def start(self):
		"""
			FUNCION: start(self)
			DESCRIPCION: Funcion que "lanza la aplicacion"
		"""
		self.app.go()

	def enviar_video(self):
		"""
			FUNCION: enviar_video(self)
			DESCRIPCION: Funcion que envia un video cuando el usuario lo seleccione
		"""
		
		if self.en_llamada == True:
			self.app.errorBox("Error2", "No puedes enviar video a un usuario mientras estas en llamada. Debes colgar antes.")
			return
		
		usuarios = self.app.getListBox("Lista de usuarios")
		if usuarios:
			u = usuarios[0]
			if u != None:

				u_info = self.d_server.obtener_info_usuario(u)
				self.dest_port = u_info['port']
				self.dest_IP = u_info['ip_address']

				#Mostramos los videos posibles
				path = os.getcwd()
				ruta_fichero = self.app.openBox(title="Elegir video a enviar", dirName= path,fileTypes=[('videos','*.mpeg'),('videos','*.mp4')], asFile=None, parent=None)

				if path == "" or path == ():
					return

				if self.en_llamada == True:
					self.app.errorBox("Error2", "No puedes enviar video a un usuario mientras estas en llamada. Debes colgar antes.")
					return

				if self.dest_IP == None:
					self.app.errorBox("ErrorIP", "No ha sido posible obtener la IP de {}".format(u))
					return

				self.control_line.enviar_video_CALLING(self.dest_IP,self.dest_port,ruta_fichero,self.nick)


			else:
				self.app.errorBox("Error_usr", "Tienes que seleccionar a un usuario en la lista para llamar")

		else:
			self.app.errorBox("Error_usr", "Tienes que seleccionar a un usuario en la lsita para llamar")


	def setImageResolution(self, resolution):
		"""
			FUNCION: setImageResolution(self,resolution)
			DESCRIPCION: Establece la resolucion de la imagen capturada
		"""
		# Se establece la resolucion de captura de la webcam
		# Puede anyadirse algun valor superior si la camara lo permite
		# pero no modificar estos
		if resolution == "LOW":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
		elif resolution == "MEDIUM":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
		elif resolution == "HIGH":
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


	def buttonsCallback(self, button):
		"""
			FUNCION: buttonsCallBack(self,button)
			DESCRIPCION: Gestiona los callbacks de los botones
		"""

		if button == "Salir":
			self.salir()

		elif button == "Login":
			self.login_enviar_REGISTER()

		elif button == "Buscar":
			self.buscar_usuario()

		elif button == "Enviar video":
			self.enviar_video()

		elif button == "Colgar":
			self.colgar()

		elif button == "Play":
			self.play()

		elif button == "Pause":
			self.pausar()

		elif button == "Llamar":
			self.llamar()

if __name__ == '__main__':

	vc = VideoClient("1280x720")
	vc.start()
