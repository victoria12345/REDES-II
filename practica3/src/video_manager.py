##############################################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
##############################################################################################
import time
import queue
import socket as sk
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageTk

class video_manager:
	"""
	CLASE: video_manager
	DESCRIPCION: Clase que gestiona la transmision de video
					utilizando una conexion UDP
	"""

	cap = None
	gui = None

	sock_envio = None
	IP_dest = 0
	port_dest = 0

	frame_no = 0
	fps = 20

	resolucion_w = 640
	resolucion_h = 480

	compresion_rate = 60

	ruta_video = None

	sock_recepcion = None
	buf_recepcion = None

	def __init__(self, gui, puerto):
		self.gui = gui

		self.sock_envio = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		self.sock_envio.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)

		self.sock_recepcion = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		self.sock_recepcion.settimeout(0.5)
		self.sock_recepcion.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
		self.sock_recepcion.bind(("0.0.0.0", int(puerto)))

		#Elegimos los FPS seleccionados
		FPS = int(self.gui.app.getOptionBox("FPS"))
		self.set_fps(FPS)

		#este buffer guarda 3 segundos de video
		self.buf_recepcion = queue.PriorityQueue(self.fps*3)

	################################
	#####FUNCIONES DE ENVIO#####
	################################

	def configurar_destinatario(self, dest_ip, dest_port):
		"""Establece la ip y puerto a la que se enviaran los paquetes con los frames.

		Keyword arguments:
		dest_ip -- La IP del destinatario del video.
		dest_port -- El puerto de recepcion del destinatario del video.
		"""
		self.IP_dest = dest_ip
		self.port_dest = dest_port

	def set_fps(self, fps):
		"""Establece los frames por segundo de la transmision.

		Keyword arguments:
		fps -- Frames por segundo deseados.
		"""
		if int(fps) <= 0:
			return "ERROR"
		else:
			self.fps = int(fps)
			return "OK"

	def set_ruta_video(self, ruta, flag):
		"""Establece la ruta al video local a ser enviado.

		Keyword arguments:
		ruta -- Ruta al video.
		flag -- 0 si no se quiere enviar video
		"""

		if flag == 0:
			self.ruta_video = None
			return

		video = Path(ruta)
		if video.is_file():
			self.ruta_video = ruta
			return "OK"
		else:
			return "ERROR"

	def capturar_frame(self):
		"""Captura y comprime una imagen para ser enviada.

		Output:
		encoded_frame -- La imagen lista para enviar.
		"""
		ret, frame = self.cap.read()
		if (frame is None) or (ret == False):
			self.gui.colgar()
			return None

		if self.ruta_video is None:
			selected_fps = self.gui.app.getOptionBox("FPS").split(" ")[0]
			if self.fps != int(selected_fps):
				self.set_fps(selected_fps)

		#Calculamos el periodo con los fps introducidos
		periodo = float(1/self.fps)
		time.sleep(periodo)

		#Establecemos resoluciones de envio y recepcion de video
		our_frame = cv2.resize(frame, (200, 300))
		frame = cv2.resize(frame, (self.resolucion_w, self.resolucion_h))

		gui_frame = cv2.cvtColor(our_frame,cv2.COLOR_BGR2RGB)
		gui_image = ImageTk.PhotoImage(Image.fromarray(gui_frame))
		self.gui.app.setImageData("Webcam", gui_image, fmt = 'PhotoImage')

		#Comprimimos la imagen para enviarla por el socket
		ok, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.compresion_rate])
		if ok == False:
			return None

		encoded_frame = encoded_frame.tobytes()
		return encoded_frame

	def enviar_frame(self, frame):
		"""Añade una cabecera al frame con la informacion pertinente y lo envia.

		Keyword arguments:
		frame -- Frame a ser enviado.
		"""
		if frame is None:
			return "ERROR"

		#Hacemos las cabeceras de los frames que vamos a enviar
		cabecera = "{}#{}#{}x{}#{}#".format(self.frame_no, time.time(), self.resolucion_w, self.resolucion_h, self.fps)
		cabecera = cabecera.encode('utf-8')
		cabecera = bytearray(cabecera)

		#Actualizamos el numero y enviamos
		self.frame_no += 1
		self.sock_envio.sendto(cabecera+frame, (self.IP_dest, int(self.port_dest)))
		return "OK"

	def transmitir_video(self, pausa, finalizacion):
		"""Establece una transmision continuada de video capturando y enviando
			frames hasta que un evento de finalizacion o pausa actua.

		Keyword arguments:
		pausa -- Evento de hilo que controla las pausas.
		finalizacion -- Evento de hilo que controla la finalizacion de la transmision.
		"""

		#Si hay que enviar video local, abrimos el fichero y ajustamos los FPS
		#Si no activamos la webcam
		if self.ruta_video is not None:
			self.cap = cv2.VideoCapture(self.ruta_video)
			self.set_fps(self.cap.get(cv2.CAP_PROP_FPS))
		else:
			#abrir webcam
			self.cap = cv2.VideoCapture(0)

		while not finalizacion.isSet():
			while pausa.isSet():
				if finalizacion.isSet():
					break

			#Capturamos frame de la webcam/video y enviamos
			frame = self.capturar_frame()
			self.enviar_frame(frame)

		#Cuando acabamos "restauramos" la interfaz
		webcam_img = ImageTk.PhotoImage(Image.open(self.gui.CAM_IMG, "r"))
		self.gui.app.setImageData("Webcam", webcam_img, fmt = 'PhotoImage')
		return

	def acabar_transmision(self):
		"""Finaliza la transmision de video actualizando los parametros
			necesarios.
		"""
		self.sock_envio.close()
		self.sock_recepcion.close()
		self.cap.release()
		self.gui.app.setStatusbar("FPS = ", 0)

	################################
	#####FUNCIONES DE RECEPCION#####
	################################

	def recibir_frame(self):
		"""Recibe un frame y lo almacena en el buffer.
		"""
		try:
			byt, address = self.sock_recepcion.recvfrom(65000)
		except:
			return "ERROR, timeout"

		if address[0] != self.IP_dest:
			return "ERROR, la IP no coincide con la destino"

		mensaje = byt.split(b"#")
		if not self.buf_recepcion.full():
			#mensaje[0] es el numero de frame (frame_no)
			self.buf_recepcion.put((int(mensaje[0]), byt))

		return "OK"

	def llenar_buf_recepcion(self, pausa, finalizacion):
		"""Va llenando el buffer hasta que un evento de pausa o finalizacion se establece.

		Keyword arguments:
		pausa -- Evento de hilo que controla las pausas.
		finalizacion -- Evento de hilo que controla la finalizacion de la transmision.
		"""

		#Mientras no hayamos acabado ni estemos en pausa recibimos frames
		while not finalizacion.isSet():
			while not pausa.isSet():
				self.recibir_frame()
				if finalizacion.isSet():
					break

		return

	def mostrar_frame(self):
		"""Adapta el formato y muestra por pantalla un frame sacado del buffer de recepcion.
		"""

		#Si el buffer esta vacio esperamos 2 segundos a que se llene
		if self.buf_recepcion.empty():
			time.sleep(1)
			return

		new_frame = self.buf_recepcion.get()[1]
		#Cabecera = frame_no#timestamp#resolucion#fps#datos
		cabecera = new_frame.split(b"#", 4)
		resolucion = cabecera[2].split(b"x")
		resolucion_w = int(resolucion[0])
		resolucion_h = int(resolucion[1])
		header_fps = int(cabecera[3])


		#Descomprimimos y adaptamos el formato para mostrarlos correctamente
		datos = cv2.imdecode(np.frombuffer(cabecera[4], np.uint8), 1)
		frame = cv2.resize(datos, (resolucion_w, resolucion_h))
		gui_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		gui_image = ImageTk.PhotoImage(Image.fromarray(gui_frame))
		self.gui.app.setImageData("Video", gui_image, fmt = 'PhotoImage')

		#Aqui estaamos calculando el tiempo para que los frames se muestren segun
		# los FPS indicados
		if self.buf_recepcion.qsize() < self.fps:
			fps_time = float(1/(0.5*header_fps))
			time.sleep(fps_time)
			self.gui.app.setStatusbar("FPS = " + str(0.5*header_fps), 0)

		else:
			fps_time = float(1/header_fps)
			self.gui.app.setStatusbar("FPS = " + str(header_fps), 0)		

	def recibir_video(self, pausa, finalizacion):
		"""Adapta el formato y muestra por pantalla un frame sacado del buffer de recepcion.

		Keyword arguments:
		pausa -- Evento de hilo que controla las pausas.
		finalizacion -- Evento de hilo que controla la finalizacion de la transmision.
		"""
		#Vamos mostrando frames mientras no finalice la llamada
		while not finalizacion.isSet():
			while not pausa.isSet():
				self.mostrar_frame()
				if finalizacion.isSet():
					break
			#en caso de que el video se pause hay que vaciar el buffer
			while not self.buf_recepcion.empty():
				try:
					self.buf_recepcion.get(False)
				except Empty:
					continue

		#Cuando la llamada acaba volvemos a las imagenes iniciales
		video_img = ImageTk.PhotoImage(Image.open(self.gui.VIDEO_IMG, "r"))
		self.gui.app.setImageData("Video", video_img, fmt = 'PhotoImage')
		self.acabar_transmision()
		return
