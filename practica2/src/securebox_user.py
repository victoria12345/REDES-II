#######################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
# Redes de Comunicaciones II
#
#######################################################################

import os
import requests
import json
from Crypto.PublicKey import RSA

########################################################
#
# FUNCION: crear_identidad(nombre, email, token, alias)
#
# DESCRIPCION: Almacena un usuario
#
# ARGS_IN:
# Nombre: nombre del usuario
# email: email del usuario
# token: token de autenticacion
# alias: alias del usuario
#
# ARGS_OUT: None si hay algun error
#
########################################################

def crear_identidad(nombre,email,token,alias = None):

	#Generamos claves
	clave = RSA.generate(2048)

	#PEM -> contains the X.509 certificate encoded in text (base64 and encrypted)
	privada = clave.exportKey('PEM')
	publica = clave.publickey().exportKey('PEM')

	print ( "Generando par de claves RSA de 2048 bits...OK")

	url = "http://vega.ii.uam.es:8080/api/users/register"
	cadena = "Bearer " + token
	headers = {'Authorization':cadena}
	args = {'nombre': nombre, 'email':email,'alias':alias,'publicKey':publica}

	try:
		r = requests.post(url,headers = headers,json = args)

	except requests.ConnectionError:
		print ( "ERROR. No hay conexion")
		return None

	if r.status_code == 200:

		print (r.text)

		#Si todo ha salido bien guardamos la clave
		#Comprobamos antes si ya existia el directorio
		if os.path.exists("./clave/") == False:
			os.mkdir("./clave/")

		with open("./clave/clave_privada.pem", "wb") as clave_f:
			clave_f.write(privada)

		#nombre-nombre, ts-timestamp

		r2 =  buscar_aux(email,token)

		#Buscamos el ultimo usuario registrado
		id = None
		max = -10000
		tmp = r2.json()
		for item in tmp:
			aux = item['ts']
			if float(aux) > max:
				max = float(aux)
				id = item['nombre']

		print ( 'Identidad con ID# '+id+' creada correctamente')

		#Guardamos todos los datos en un fichero

		with open("registro.dat", "w") as f:
			f.write("Datos del ultimo usuario:\nNombre: {}\nEmail: {}\nAlias: {}\nID: {}".format(r.json()['nombre'], email, alias, id))


	#problema en la peticion
	else:
		print ( r.status_code)
		print ( "ERROR. El usuario no se ha podido registrar")

	return

#########################################################
#
# FUNCION: buscar(usuario, token)
#
# DESCRIPCION: Funcion que busca un usuario en el sistema
#
# ARGS_IN:
# usuario: id del usuario que se busca
# token: token de autenticacion
#
# ARGS_OUT: None si hay algun error
#
#########################################################
def buscar(usuario, token):
	r = buscar_aux(data_search = usuario, token=token)

	if(r == None):
		return r

	if r.status_code == 200:
		tmp = r.json()
		print ( "Buscando usuario {} en el servidor...OK" .format(usuario))
		print ( "{} usuarios encontrados: ".format(len(tmp)))
		i = 0

		#Imprimimos informacion de los usuarios
		for item in tmp:
			print ("[{}] {}, {}, ID: {}".format(i+1, tmp[i]['nombre'], tmp[i]['email'], tmp[i]['userID']))
			i +=1

	else:
		print ( "->ERROR. No se ha podido buscar el usuario")
		error(r.json()['error_code'], r.json()['description'])

	return i

#########################################################
#
# FUNCION: buscar_aux)(data_search, token)
#
# DESCRIPCION: Funcion auxiliar de buscar. Realiza unicamente la busqueda
# al servidor de ese usuario
#
# ARGS_IN:
# data_search: atributo para buscar el usuario en el servidor
# token: token de autenticacion
#
# ARGS_OUT: resultado de la peticion al servidor
#
#########################################################
def buscar_aux(data_search, token):

	url = 'http://vega.ii.uam.es:8080/api/users/search'
	authorization = {'Authorization':"Bearer " + token}
	args = {'data_search': data_search}

	try:
		r = requests.post(url, headers = authorization, json = args)

	except requests.ConnectionError:
		print ( "NO HAY CONEXION")
		return None

	if r.status_code == 200:
		return r

	else:
		error(r.json()['error_code'], r.json()['description'])
		return None

#########################################################
#
# FUNCION: buscar_clave_puclica(id, token)
#
# DESCRIPCION: Busca la clave publica de un usuario
#
# ARGS_IN:
# id: id del usuario cuya clave buscamos
# token: token de autenticacion
#
# ARGS_OUT: clave publica del usuario
#
#########################################################
def buscar_clave_publica(id, token):
	url = 'http://vega.ii.uam.es:8080/api/users/getPublicKey'
	authorization = {'Authorization':"Bearer " + token}
	args = {'userID': id}

	try:
		r = requests.post(url, headers = authorization, json = args)

	except requests.ConnectionError:
		print ( "ERROR.NO HAY CONEXION")
		return None

	if r.status_code == 200:

		return r.json()['publicKey']

	else:
		print ( "->ERROR. No se ha podido buscar la clave publica")
		error(r.json()['error_code'], r.json()['description'])

	return

#########################################################
#
# FUNCION: borrar(userID, token)
#
# DESCRIPCION: Funcion que borra un usuario
#
# ARGS_IN:
# userID: id del usuario que se quiere borrar
# token: token de autenticacion
#
# ARGS_OUT: None si hay algun error
#
#########################################################
def borrar (userID, token):

	url = 'http://vega.ii.uam.es:8080/api/users/delete'
	authorization = {'Authorization':"Bearer " + token}
	args = {'userID': userID}

	try:
		r = requests.post(url,json = args,headers = authorization)

	except requests.ConnectionError:
		print ( "Solicitado borrado de la identidad {}....ERROR".format(userID))
		print ( "NO HAY CONEXION")
		return None

	if r.status_code == 200:
		print ( "Solicitando borrado de la identidad {}...OK".format(userID))
		print ( "El usuario con ID {} se ha borrado correctamente" .format(userID))

	else:
		print ( "->ERROR. No se ha podido borrar al usuario")
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

	if codigo == "USER_ID2" or codigo == "USER_ID1" or codigo == "ARGS1":
		print ( "ERROR: "+ desc+ "\n\n")

	elif  codigo == "TOK1" or codigo == "TOK2" or codigo == "TOK3":
		print ( "ERROR: "+ desc+ "\n\n")
	else:
		print ( "ERROR. Codigo de error desconocido")
