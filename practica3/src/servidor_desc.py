###########################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
###########################################################################

import socket as sk
import time

class servidor_desc:
	"""
	CLASE: servidor_desc
	DESCRIPCION: Implementa las funciones necesarias para la creacion
	y cierre de conexiones con el servidor de descubrimientos y para la
	realizacion de consultas al mismo.
	"""

	puerto = None   #Puerto del servidor de descrubrimiento.
	tam_buffer = 1024   #Tamaño del buffer de recepcion del socket.
	url = "vega.ii.uam.es" #url del servidor de desubrimiento

	#Constructor
	def __init__(self, puerto):
		self.puerto = puerto

	def crear_socketDS(self):
		"""Crea un socket para el servidor en el puerto de la clase.

		"""
		if self.puerto == None:
			return None

		#Creamos el socket TCP para la comunicacion con el DS
		try:
			socketDS = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
			socketDS.settimeout(5)
			socketDS.connect((self.url, int(self.puerto)))
		except(OSError, ConnectionRefusedError):
			print("Error al crear el socketDS")
			return None

		return socketDS

	def cerrar_socketDS(self, socketDS):
		"""Cierra el socket del servidor despues de enviarle el comando QUIT
			indicando que se va.

		Keyword arguments:
		socketDS -- El socket que queremos cerrar
		"""
		comando = "QUIT"

		try:
			socketDS.send(bytes(comando, 'utf-8'))
			respuesta = socketDS.recv(self.tam_buffer)
			socketDS.close()
		except:
			return None

		return respuesta

	def registrar_usuario(self, nick, contrasenia, IPAddr, puerto):
		"""Registra un usuario en el servidor de descubrimiento enviando
			el comando adecuado.

		Keyword arguments:
		nick -- El nick del usuario que queremos registrar.
		contrasenia -- La contraseña del usuario que queremos registrar.
		IPAddr -- Ip a registrar en el servidor
		puerto -- Puerto de recepcion a registrar en el servidor
		"""
		socketDS = self.crear_socketDS()

		if socketDS == None:
			return "ERROR"

		#Creamos el comando para el servidor, lo enviamos y comprobamos la respuesta
		try:
			comando = "REGISTER {} {} {} {} V0".format(nick, IPAddr, puerto, contrasenia)
			socketDS.send(bytes(comando, 'utf-8'))
			respuesta = socketDS.recv(self.tam_buffer).decode('utf-8')
		except:
			return "ERROR"

		self.cerrar_socketDS(socketDS)

		#print(respuesta)

		if respuesta == "NOK WRONG_PASS":
			return "ERROR_CONTRA"

		return "OK"

	def obtener_info_usuario(self, nick):
		"""Envia al servidor una consulta para obtener informacion de un usuario
			y en caso de que exista, delvuelve un diccionario con la respuesta.

		Keyword arguments:
		nick -- El nick del usuario cuya informacion queremos obtener.

		Output:
		diccionario -- Esctructura con la info del usuario solicitado.
		"""

		socketDS = self.crear_socketDS()
		if socketDS == None:
			return None

		#Creamos el comando para el servidor, lo enviamos y comprobamos la respuesta
		try:
			comando = "QUERY {}".format(nick)
			socketDS.send(bytes(comando, 'utf-8'))
			respuesta = socketDS.recv(self.tam_buffer).decode('utf-8')
		except:
			return None

		self.cerrar_socketDS(socketDS)

		if respuesta == "NOK USER_UNKNOWN":
			return "ERROR"

		#Agrupamos los datos en un diccionario y los devolvemos
		info = respuesta.split(" ")
		diccionario = {}
		diccionario['nick'] = info[2]
		diccionario['ip_address'] = info[3]
		diccionario['port'] = info[4]
		diccionario['protocols'] = info[5]

		return diccionario

	def listar_usuarios(self):
		"""Envia al servidor una consulta para listar a todos los usuarios
			disponibles en el sistema.

		Output:
		lista_usuarios -- Lista que contiene el nick de los usuarios del sistema.
		"""

		socketDS = self.crear_socketDS()
		if socketDS == None:
			return None

		#Creamos el comando para el servidor, lo enviamos y comprobamos la respuesta
		try:
			comando = "LIST_USERS"
			socketDS.send(bytes(comando, 'utf-8'))
			respuesta = socketDS.recv(self.tam_buffer).decode('utf-8')
		except:
			return None


		if respuesta == "NOK USER_UNKNOWN":
			self.cerrar_socketDS(socketDS)
			return "ERROR"

		respuesta_total = respuesta
		n_users = int(respuesta.split(" ")[2])
		n_leidos = respuesta.count('#')
		while n_leidos < n_users:
			respuesta = socketDS.recv(self.tam_buffer).decode('utf-8')
			n_leidos += respuesta.count('#')
			respuesta_total += respuesta

		lista_usuarios = []
		usuarios = respuesta_total.split("#")

		#Hay que tener en cuenta que el primer usuario no esta separado del OK USER_LIST del mensaje de respuesta
		campos = usuarios[0].split(" ")
		lista_usuarios.append(campos[3])

		for u in usuarios[1:]:
			campos = u.split(" ")
			lista_usuarios.append(campos[0])

		self.cerrar_socketDS(socketDS)
		return lista_usuarios
