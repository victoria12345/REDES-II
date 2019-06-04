#######################################################################
#
# Autores: Victoria Pelayo e Ignacio Rabunnal
#
# Redes de Comunicaciones II
#
#######################################################################

"""

Usage:
	securebox_client.py --create_id <nombre> <email> [<alias>]
	securebox_client.py --search_id <cadena>
	securebox_client.py --delete_id <id>
	securebox_client.py --upload <fichero> --dest_id <id>
	securebox_client.py --upload_files --dest_id <id> <ficheros>...
	securebox_client.py --upload_file_ids --f <fichero> <ids>...
	securebox_client.py --download <id_fichero> --source_id <id>
	securebox_client.py --download_files --source_id <id> <id_ficheros>...
	securebox_client.py --list_files
	securebox_client.py --delete_file <id_fichero>
	securebox_client.py --delete_files <ficheros>...
	securebox_client.py --encrypt <fichero> --dest_id <id>
	securebox_client.py --sign <fichero>
	securebox_client.py --enc_sign <fichero> --dest_id <id>
	securebox_client.py (--help)

Options:
	--create_id registra un usuario
	--search_id busca un usuario en funcion de la cadena introducida
	--delete_id borra el usuario(si existe) con ese id
	--upload sube un fichero, el id destino se sebe especificar
	--upload_files sube varios ficheros destinados al mismo usuario
		ejemplo de uso:
		--upload_files --dest_id ID_USUARIO fich1.txt fich2.txt fich3.txt
	--upload_file_ids: sube un fichero para varias personar
		ejemplo de uso:
		--upload_file_ids --f fich.txt id1 id2 id3
	--download descarga un fichero, el id destino se debe especificar
	--download_files descarga varios ficheros, se introducen los ids seguidos
		ejemplo de uso:
		--download_files --source_id ID-USER IDF1 IDF2 IDF3
	--list_files muestra los ficheros del usuario
	--delete_file borra el fichero que tenga ese id
	--delete_files borra varios ficheros a la vez
		ejemplo: --delete_files fich1 fich2 fich3
	--encrypt encripta un fichero como si fuese dirigido al destino
	--sign firma un fichero
	--enc_sign encripta y firma un fichero


"""
from docopt import docopt

if __name__ == '__main__':
	args = docopt(__doc__)
	import json
	import sys
	
	sys.path.insert(0, './src')
	
	import securebox_files as files
	import securebox_encrypt as encrypt
	import securebox_user as user

token = "c6dF3752BAb984C0"

#CREAR UNA IDENTIDAD
if args['--create_id']:
	nombre = args['<nombre>']
	email = args['<email>']

	if args['<alias>']:
		alias = args['<alias>']
		exit = user.crear_identidad(nombre,email,token,alias)
	else:
		exit = user.crear_identidad(nombre,email,token)

	if exit == None:
		sys.exit(1)

#BUSCAR UNA IDENTIDAD
elif args['--search_id']:
	cadena = args['<cadena>']

	exit = user.buscar(cadena, token)

	if exit == None:
		sys.exit(1)

#BORRAR UNA IDENTIDAD
elif args['--delete_id']:
	id = args['<id>']
	exit = user.borrar(id, token)

	if exit == None:
		sys.exit(1)

#SUBIR FICHERO
elif args['--upload']:
	id_receptor = args['<id>']
	fichero = args['<fichero>']
	exit = files.subir_fichero(fichero, id_receptor, token)

	if exit == None:
		sys.exit(1)

#SUBIR FICHEROS
elif args['--upload_files']:
	id_receptor = args['<id>']
	num = len(args['<ficheros>'])
	i = 0
	for i in range(num):
		exit = files.subir_fichero(args['<ficheros>'][i], id_receptor, token)

	if exit == None:
		sys.exit(1)

#SUBIR FICHERO PARA VARIAS PERSONAS
elif args['--upload_file_ids']:
	fichero = args['<fichero>']
	num = len(args['<ids>'])
	i = 0
	for i in range(num):
		exit = files.subir_fichero(fichero, args['<ids>'][i], token)

	if exit == None:
		sys.exit(1)

#DESCARGAR FICHERO
elif args['--download']:
	id_fichero = args['<id_fichero>']
	id = args['<id>']
	exit = files.descargar_fichero(id_fichero, id, token)

	if exit == None:
		sys.exit(1)

#DESCARGAR FICHEROS
elif args['--download_files']:
	num = len(args['<id_ficheros>'])
	id = args['<id>']

	for i in range(num):
		print("descargado fichero con ID: "+args['<id_ficheros>'][i]+"\n")
		exit = files.descargar_fichero(args['<id_ficheros>'][i], id, token)

	if exit == None:
		sys.exit(1)


#MOSTRAR FICHEROS
elif args['--list_files']:
	exit = files.listar_ficheros(token)

	if exit == None:
		sys.exit(1)

#ELIMINAR FICHERO
elif args['--delete_file']:
	id_fichero = args['<id_fichero>']

	exit = files.borrar_fichero(id_fichero,token)

	if exit == None:
		sys.exit(1)

#ELIMINAR FICHEROS
elif args['--delete_files']:
	num = len(args['<ficheros>'])

	for i in range(num):
		print("Eliminando fichero con ID: "+args['<ficheros>'][i]+"\n")
		exit = files.borrar_fichero(args['<ficheros>'][i], token)

	if exit == None:
		sys.exit(1)

#ENCRIPTAR FICHERO
elif args['--encrypt']:
	fichero = args['<fichero>']
	id = args['<id>']

	exit = encrypt.cifrar_fichero(fichero,id,token)

	if exit == None:
		sys.exit(1)

#FIRMAR FICHERO
elif args['--sign']:
	fichero = args['<fichero>']

	exit = encrypt.firmar_fichero(fichero)

	if exit == None:
		sys.exit(1)

#FIRMAR Y ENCRIPTAR FICHERO
elif args['--enc_sign']:
	fichero = args['<fichero>']
	id = args['<id>']

	exit = encrypt.firmar_cifrar_fichero(fichero,id,token)

	if exit == None:
		sys.exit(1)
