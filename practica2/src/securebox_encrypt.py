#######################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
# Redes de Comunicaciones II
#
#######################################################################

import json
import os
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad, pad
from base64 import b64decode, b64encode
from Crypto.Signature import *
from Crypto.Hash import SHA256
import securebox_user as usuarios

#################################################
# FUNCION: encriptar_AES(texto,clave)
#
# DESCRIPCION: Encriptamos con AES un mensaje
#
# ARGS_IN:
# texto: texto que se va a encriptar
# clave: clave que se va a usar
#
# ARGS_OUT: iv(vector inicializacion)+ct_bytes(textoencriptado)
#
##################################################
def encriptar_AES(texto, clave):

    IV = get_random_bytes(16)
    cipher = AES.new(clave, AES.MODE_CBC, IV)

    ct_bytes = cipher.encrypt(pad(texto, 16)) #bloques de 16B
    return IV+ct_bytes

################################################
#
# FUNCION_ desencriptar_AES(texto_enc, clave, iv)
#
# DESCRIPCION: desencripta con AES un texto
#
# ARGS_IN:
# texto_enc: texto que queremos desencriptar
# clave: clave que usaremos para desencriptar
# iv: vector de inicializacion
#
# ARGS_OUT: texto desencriptado
################################################
def desencriptar_AES(texto_enc, clave,iv):

    cipher = AES.new(clave, AES.MODE_CBC, iv)

    return unpad(cipher.decrypt(texto_enc), 16)

#################################################
#
# FUNCION: firmar_mensaje(mensaje)
#
# DESCRIPCION: Firma un mensaje
# ARGS_IN:
# mensaje: mensaje que queremos firmar
#
# ARGS_OUT: mensaje firmado
#
#################################################
def firmar_mensaje(mensaje):
    key = RSA.importKey(open("./clave/clave_privada.pem", "r").read())
    h = SHA256.new(mensaje)
    PKCS1_OAEP.new(key)

    firma = pkcs1_15.new(key).sign(h) #aqui tenemos la firma
    return firma + mensaje

#####################################################
#
# FUNCION: firmar_fichero(fichero)
#
# DESCRIPCION: Firma un fichero
#
# ARGS_IN:
# fichero: fichero que queremos firmar
#
# ARGS_OUT:None solo en caso de error
#
#####################################################

def firmar_fichero(fichero):

	file = os.path.basename(fichero) #obtener nombre real, por si trabajamos en varios directorios

	try:
		#si el fichero existe leemos el mensaje
		with open(fichero, "rb") as f:
			aux = f.read()
			f.close()

	except EnvironmentError :
		#en caso de que el fichero no se pueda abrir
		return None

	#firmamos el mensaje
	mensaje = firmar_mensaje(aux)


	#en ficheros/firmados estan los ficheros firmados
	#comprobamos que existan los directorios, si no, los creamos:
	directorio = "./ficheros"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	directorio = "./ficheros/firmados"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	fichero_firmado = "{}/{}".format("./ficheros/firmados", file)

	with open(fichero_firmado, "wb") as f:
		f.write(mensaje)
		f.close()

	print ( "-> Firmando fichero...OK")

	return

#####################################################
#
# FUNCION: cifrar_clave(clave, id_receptor, token)
#
# DESCRIPCION: Funcion que cifra la clave AES con RSA
# ARGS_IN:
# clave: clave que queremos encriptar, con AES
# id_receptor: id del receptor, lo necesitamos para
# 				obtener la clave publica
# token: token de autenticacion
#
# ARGS_OUT: clave cifrada
#
#####################################################
def cifrar_clave(clave, id_receptor, token):

	clave_aux = usuarios.buscar_clave_publica(id_receptor, token)

	if clave_aux == None or not clave_aux:
		print ( "ERROR: No se ha encontrado la clave")
		return None

	clave_pub = RSA.import_key(clave_aux)
	print ( "-> Obtenemos clave publica de ID {}...OK".format(id_receptor))

	#Aqui encriptamos la clave del AES
	cipher = PKCS1_OAEP.new(clave_pub)
	return cipher.encrypt(clave)

##########################################################
#
# FUNCION: descifrar_clave(clave_enc)
#
# DESCRIPCION: Desencripta la clave apra obtener la clave AES que necesitamos
#
# ARGS_IN:
# clave_enc: clave que queremos desencriptar
#
# ARGS_OUT: clave descifrada
#
##########################################################
def descifrar_clave(clave_enc):

	privada = RSA.importKey(open("./clave/clave_privada.pem", "rb"). read())

	cipher = PKCS1_OAEP.new(privada)

	return cipher.decrypt(clave_enc)


#####################################################
#
# FUNCION: cifrar_mensaje(mensaje, id_receptor, token)
#
# DESCRIPCION: Funcion que cifra un mensaje y su clave
# y los devuelve concatenados
#
# ARGS_IN:
# mensaje: mensaje que queremos cifrar
# id_receptor: id del receptor del mensaje
# token: token de autenticacion
#
# ARGS_OUT: clave encriptada(RSA)+ mensaje cifrado
#
#####################################################
def cifrar_mensaje(mensaje, id_receptor, token):
	#La clave AES es de 32 bytes
	clave = get_random_bytes(32)
	mensaje_enc = encriptar_AES(mensaje, clave)

	if mensaje_enc == None:
		return None

	clave_enc = cifrar_clave(clave, id_receptor, token)

	if clave_enc == None:
		print ( "ERROR: La clave no se ha podido cifrar")
		return None

	return mensaje_enc[:16]+clave_enc + mensaje_enc[16:]

#####################################################
#
# FUNCION: cifrar_fichero(file, id_receptor, token)
#
# DESCRIPCION: Funcion que cifra un fichero
#
# ARGS_IN:
# file: fichero que queremos cifrar
# id_receptor: id del receptor del fichero cifrado
# token: token de autenticacion
#
# ARGS_OUT: None solo en caso de error
#
#####################################################
def cifrar_fichero(file, id_receptor, token):
	f_nombre = os.path.basename(file)

	try:
		with open(file, "rb") as fichero:
			mensaje = fichero.read()
			fichero.close()

	except EnvironmentError:
		print ( "ERROR: No ha sido posible abrir el fichero")
		return None

	clave_mensaje_enc = cifrar_mensaje(mensaje, id_receptor, token)
	print ( "->Cifrando fichero...OK")

	if clave_mensaje_enc == None:
		print ( "ERROR: No ha sido posible encriptar la clave+fichero")
		return None

	#Comprobamos que existan los ficheros, si no los creamos
	directorio = "./ficheros"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	directorio = "./ficheros/encriptados"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	ruta_fichero = "{}/{}".format(directorio, f_nombre)
	with open(ruta_fichero, 'wb') as direccion:
		direccion.write(clave_mensaje_enc)

	print ( "OK")

	return

########################################################
#
# FUNCION: firmar_cifrar_mensaje(mensaje, id_receptor, token)
#
# DESCRIPCION: Funcion que firma y cifra un mensaje
#
# ARGS_IN:
# mensaje: mensaje que queremos cifrar y firmar
# id_receptor: receptor del mensaje firmado-cifrado
# token: token de autenticacion
#
# ARGS_OUT: mensaje cifrado y firmado
#
########################################################

def firmar_cifrar_mensaje(mensaje, id_receptor, token):
	mensaje_fir = firmar_mensaje(mensaje)
	if mensaje_fir == None:
		print ( "ERROR: No ha sido posible firmar")
		return None

	print ( "-> Firmando fichero...OK")

	mensaje_enc = cifrar_mensaje(mensaje_fir, id_receptor, token)

	if mensaje_enc == None:
		print ( "ERROR: No ha sido posible cifrar")
		return None

	print ( "-> Cifrando fichero...OK")

	return mensaje_enc


########################################################
#
# FUNCION: desencriptar_general(mensaje, id_emisor, token)
#
# DESCRIPCION: Valida firma y descifra AES
#
# ARGS_IN:
# mensaje: mensaje que queremos desencriptar
# id_emisor: id del emisor del mensaje encriptado
# token: token de autenticacion
#
# ARGS_OUT: texto en claro del mensaje, None si hay error
#
########################################################
def desencriptar_general(mensaje, id_emisor, token):
	#256 mensaje cifrado RSA
	#IV 16
	#mensaje = clave+iv+firma+mensaje
	print ( "Comenzamos a desencriptar el mensaje...")
	#16 tam iv
	#256 tam rsa
	clave_tmp = mensaje[16:16+256]
	iv = mensaje[0:16]
	firma_mensaje_tmp = mensaje[256+16:]

	clave = descifrar_clave(clave_tmp)
	print ( "-> Recuperando clave de ID {}...OK".format(id_emisor))

	firma_mensaje = desencriptar_AES(firma_mensaje_tmp, clave, iv)
	print ( "-> Descifrando fichero...OK")

	firma = firma_mensaje[0:256]
	mensaje = firma_mensaje[256:]

	if comprobar_firma(mensaje, firma, id_emisor,token) == True:
		print ( "-> Verificando firma...OK")
		return mensaje

	else:
		print ( "ERROR")
		return None

#########################################################
#
# FUNCION: firmar_cifrar_fichero(file, id_receptor, token)
#
# DESCRIPCION: Funcion que firma y cifra un fichero
#
# ARGS_IN:
# file: fichero que queremos firmar y cifrar
# id_receptor: receptor de este fichero firmado y cifrado
# token: token de autenticacion
#
# ARGS_OUT: ruta del fichero, None si hay error
#
#########################################################

def firmar_cifrar_fichero(file, id_receptor, token):

	f_nombre = os.path.basename(file)

	try:
		with open(file, 'rb') as fichero:
			mensaje = fichero.read()
			fichero.close()

	except EnvironmentError:
		print ( "ERROR: No ha sido posible abrir el fichero")
		return None

	print ( "-> Encriptando y cifrando fichero...OK")

	m_enc = firmar_cifrar_mensaje(mensaje, id_receptor, token)
	if m_enc == None:
		return None


	#Comprobamos que existan los ficheros, si no los creamos
	directorio = "./ficheros"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	directorio = "./ficheros/encriptados-firmados"
	if os.path.exists(directorio) == False:
		os.mkdir(directorio)

	ruta_fichero = "{}/{}".format(directorio, f_nombre)
	with open(ruta_fichero, 'wb') as direccion:
		direccion.write(m_enc)

	return ruta_fichero

#########################################################
#
# FUNCION: comprobar_firma(mensaje, firma, id_emisor, token)
#
# DESCRIPCION: Comprueba si la firma es valida
#
# ARGS_IN:
# mensaje: mensaje que esta firmado
# firma: firma que queremos comprobar
# id_emisor id del emisor que lo ha firmado
# token: token de autenticacion
#
# ARGS_OUT: True si esta bien, false si no es asi
#
#########################################################

def comprobar_firma(mensaje, firma, id_emisor, token):

	#Primero aplicamos hash al mensaje
	hash_ = SHA256.new(mensaje)

	#Sacamos la clave publica para comparar con el hash
	aux = usuarios.buscar_clave_publica(id_emisor,token)

	if aux == None:
		print ( "ERROR. No es posible encontrar la clave publica")
		return False

	publica = RSA.import_key(aux)

	#Ahora comprobamos la firma
	try:
		pkcs1_15.new(publica).verify(hash_, firma)

	except(TypeError, ValueError):
		print ( "La firma no es valida")
		return False

	return True
