#######################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
# Redes de Comunicaciones II
#
#######################################################################
import securebox_encrypt as encrypt
import os
import requests
import json
import securebox_user as usuarios

########################################################
#
# FUNCION: subir_fichero_aux(fichero, token)
#
# DESCRIPCION: Funcion que realiza *unicamente* el proceso de subir un archivo
#
# ARGS_IN:
# fichero: fichero que se quiere subir
# toke: token de autenticacion
#
# ARGS_OUT: None unicamente en caso de error
#
########################################################
def subir_fichero_aux(fichero, token):

	try:
		#si el fichero existe leemos el mensaje
		with open(fichero, "rb") as f:

			url = 'http://vega.ii.uam.es:8080/api/files/upload'
			authorization = {'Authorization':"Bearer " + token}

			#Unica funcion del api que no tieneargumentos JSON
			try:
				files = {'ufile': f}
				r = requests.post(url, headers=authorization,files=files)
			except requests.ConnectionError:
				print ("-> ERROR. No se ha podido establecer conexion")

	except EnvironmentError :
		print ("ERROR. No se puede abrir ese fichero")
		return None

	#Comprobamos que la peticion POST haya salido bien

	if r.status_code == 200:
		#Devolvemos el id del fichero
		return r.json()['file_id']
	else:
		print ("-> ERROR.No se ha podido subir el fichero")
		error(r.json()['error_code'], r.json()['description'])
		return None

#############################################################
#
# FUNCION: subir_fichero(fichero, dest_id, token)
#
# DESCRIPCION: Funcion que cifra el fichero y lo sube
#
# ARGS_IN:
# fichero: fichero que se quiere subir
# dest_id: id del destinatacio
# token: token de autenticacion
#
# ARGS_OUT: id del fichero
#
#############################################################
def subir_fichero(fichero, dest_id,token):

	#Obtenemos el nombre real
	f_nombre = os.path.basename(fichero)
	print ( 'Solicitado envio de fichero a SecureBox')

	try:
		with open(fichero, "rb") as f:
			mensaje = f.read()
			f.close()

	except EnvironmentError:
		print ( "ERROR: No ha sido posible abrir el fichero")
		return None

	mensaje_en = encrypt.firmar_cifrar_mensaje(mensaje, dest_id,token)

	if mensaje_en == None:
		print ( "->ERROR. Abortamos subida de fichero")
		return None

	with open(f_nombre, "wb") as f:
		f.write(mensaje_en)
		f.close()

	#Llamamos a la funcion subir fichero
	try:
		file_id = subir_fichero_aux(fichero, token)

	except requests.ConnectionError:
		with open(f_nombre, "wb") as f:
			f.write(mensaje)
			f.close()
		print ( "ERROR AL SUBIR EL FICHERO.No hay conexion\n")
		return None
	with open(f_nombre, "wb") as f:
		f.write(mensaje)
		f.close()
	#Comprobamos que file_id sea valido
	if file_id == None:
		return None

	print ( "-> Subiendo fichero a servidor...OK")
	print ( "Subida realizada correctamente, ID del fichero: "+file_id+"\n")
	#os.remove(f_nombre)

	return file_id


###############################################################
#
# FUNCION: descargar_fichero(file_id, id_emisor, token)
#
# DESCRIPCION: Descarga un fichero
# ARGS_IN:
# file_id: id del fichero que se quiere descargar
# id_emisor: id del emisor del fichero
# token: token de autenticacion
#
# ARGS_OUT: None solo si hay algun error
###############################################################

def descargar_fichero(file_id, id_emisor, token):

	print ( "Descargando fichero de SecureBox...OK")

	url = 'http://vega.ii.uam.es:8080/api/files/download'
	authorization = {'Authorization':"Bearer " + token}
	args = {'file_id':file_id}

	try:
		r = requests.post(url, headers=authorization,json=args)

	except requests.ConnectionError:
		print ( "ERROR. No hay conexion")
		return None

	if r.status_code == 200:

		#Buscamos en la cabecera el nombre del archivo

		headers = r.headers
		f_nombre = "{}".format(headers['Content-Disposition'].split('"')[1])
		m_enc = r.content

		#Comprobamos que los directorios existan
		directorio = "./ficheros"
		if os.path.exists(directorio) == False:
			os.mkdir(directorio)

		directorio = "./ficheros/descargas"
		if os.path.exists(directorio) == False:
			os.mkdir(directorio)

		ruta_fichero = "{}/{}".format(directorio, f_nombre)

		#Desencriptados
		#try:

		mensaje = encrypt.desencriptar_general(m_enc, id_emisor, token)

		# except(TypeError, ValueError):
		# 	print ( "-> Error al desencriptar el mensaje")
		# 	print ( "ERROR. No se ha podido descargar el fichero")
		# 	return None

		if mensaje == None:
			print('NO ha sido posible la descarga')
			return None

		#Guardamos en el fichero
		with(open(ruta_fichero,"wb")) as f:
			f.write(mensaje)
			f.close()
			print ( "Fichero descargado y verificado correctamente.")
		return
	else:
		print ( "-> ERROR. No se ha podido descargar el fichero")
		error(r.json()['error_code'], r.json()['description'])

		return None


################################################################
#
# FUNCION: listar_fichero(token)
#
# DESCRIPCION:Lista todos los ficheros de un usuario
#
# ARGS_IN:
# 	token: token de autenticacion
#
# ARGS_OUT: None si hay algun error
#
################################################################

def listar_ficheros(token):

	print ( "Listando ficheros ...")

	url = 'http://vega.ii.uam.es:8080/api/files/list'
	authorization = {'Authorization':"Bearer " + token}

	try:
		r = requests.post(url, headers = authorization)

	except requests.ConnectionError:
		print ( "ERROR")
		print ("Ha habido un problema en la conexion")

		return None

	if r.status_code == 200:
		tmp = r.json()
		fichs = tmp['files_list']
		cont = 0

		print ( "OK")
		print ( "Se han encontrado {} ficheros".format(tmp['num_files']))
		print ( "Listado de ficheros del usuario con token: \n" + token)


		for item in fichs:
			print ( "->[{}] ID: {}, Nombre: {}".format(cont+1, item['fileID'], item['fileName']))
			cont +=1

		print ( "Listado mostrado correctamente")
		return

###############################################################
#
# FUNCION: borrar_fichero(file_id, fichero)
#
# DESCRIPCION: Borra un fichero
#
# ARGS_IN:
# file_id id del fichero que se desea borrar
# token: token de autenticacion
#
# ARGS_OUT: None si hay algun error
#
###############################################################

def borrar_fichero(file_id, token):

	print ("Borrando fichero con ID:{} ...".format(file_id))

	url = 'http://vega.ii.uam.es:8080/api/files/delete'
	authorization = {'Authorization':"Bearer " + token}
	args = {'file_id':file_id}

	try:
		r = requests.post(url, headers=authorization,json=args)

	except requests.ConnectionError:
		print ( "ERROR. No hay conexion")
		return None

	if r.status_code == 200:
		print ( "OK")
		print ( "Se ha borrado correctamente el fichero con ID: "+file_id)
		return

	else:
		print ( "->ERROR.No ha sido posible borrar correctamente el fichero")
		error(r.json()['error_code'], r.json()['description'])
		return


#########################################################
#
# FUNCION. error(codigo, desc)
# DESCRIPCION: Imprime codigo de error y su descripcion
#
# ARGS_IN:
# codigo: codigo del error
# desc: descripcion del error
#
#########################################################

def error(codigo, desc):

	if codigo == "FILE1" or codigo == "FILE2" or codigo == "FILE3":
		print ( "ERROR: "+ desc+ "\n\n")


	elif codigo == "TOK1" or codigo == "TOK2" or codigo == "TOK3" or codigo == "ARGS1":
		print ( "ERROR: "+ desc+ "\n\n")
	else:
		print ( "ERROR. Codigo de error desconocido")
