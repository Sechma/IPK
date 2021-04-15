
#!/usr/bin/env python


import socket 
import sys
import re
import select
import os
from re import search

def check_argv (argv):
	ip_port = -1
	path_f = "Q"
	previous_argc = ""

	if len(argv) != 5:
		print("Wrong numbers of arguments!")
		exit(1)
	else:
		for index, argc in enumerate(argv):
			if(index == 4 or index == 2):

				m = re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+',(argc))
				if(m and previous_argc == "-n" ):
					ip_port = m[0]

				n = re.findall(r'^fsp.*',(argc))
				if(n and previous_argc =="-f"):
					path_f = n[0]

			previous_argc = argc

	if(path_f == "Q"):
		print("Wrong parametr with path, without FSP prefix or previous parametr -f!")
		exit(1)
	if(ip_port == -1):
		print("Wrong IPv4 or port or previous parametr: -n!")
		exit(1)

	return ip_port,path_f


def destroy_header(file):
	destroy = 0

	with open(file,"rb") as fi:
		data = fi.read().splitlines(True)
		tmp = (data[0]).decode()
	
		if(search("Not Found",tmp)):
			destroy = 1
			for line in data:
				print((line).decode())

		elif(search("Bad Request",tmp)):
			destroy = 1
			for line in data:
				print((line).decode())

		elif(search("Server Error",tmp)):
			destroy = 1
			for line in data:
				print((line).decode())
			
		fi.close()
	with open(file,"wb") as fo:
		fo.writelines(data[3:])
		fo.close()

	if(destroy):
		os.remove(file)
		exit(1)

def get_file(filename,tcp_sock):
	data = ""
	try:
		f = open(filename,"wb")
		while 1:

			try:
				data = tcp_sock.recv(2048)
			except:
				print(data.decode())
				exit(1)

			f.write(data)
			if not data:
				break

		f.close()
	except: 
		f.close()
		print("This file cannot be made!")
		exit(1)

	destroy_header(filename)


def get_next_files(hostname,filename,adr,port):

	tcp_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	tcp_sock.connect((adr,int(port)))
	tcp_sock.settimeout(30.0)
	tcp_msg = "GET "+filename+" FSP/1.0\r\n"+"Hostname: "+hostname+"\r\nAgent: xsechr00\r\n\r\n"
	msg =str.encode(tcp_msg)
	try:
		tcp_sock.send(msg)
	except tcp_sock.timeout: 
		print("something wrong with send!")
		exit(1)

	get_file(parse_path(filename),tcp_sock)
	tcp_sock.close()

def parse_path(filename):
	parts = filename.split('/')
	return(parts[-1])
# **************************************************MAIN**************************************************



IP_port,path = check_argv(sys.argv)
ip, port = IP_port.split(':')
data = ""
addr = ""
index = 0
parts_path = path.split('/')
filename = parts_path[-1]

hostname = parts_path[2]
last_part_path = ""# its can be file or * or index
for i,s in enumerate(parts_path[3:]):
	last_part_path += s
	if i != len(parts_path[3:]) - 1:
		last_part_path += "/"

if(last_part_path == "*"):
	index = 1
	last_part_path = "index"
	filename = "index"

#************UDP************
client_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
client_sock.settimeout(30.0)
msg_client = "WHEREIS "+hostname+"\r\n"

msg = str.encode(msg_client)
client_sock.sendto(msg,(ip,int(port)))


try: 
	data = client_sock.recvfrom(2048)

except client_sock.timeout:
	print("Waiting for long time!")
	exit(1)

data = str(data[0])
data,adrr = data.split(" ")
adr,port = adrr.split(":")

port,_ = port.split("'")

client_sock.close()

# TCP ******************

complete_data = ""
tcp_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcp_sock.settimeout(30.0)
tcp_sock.connect((adr,int(port)))

tcp_msg = "GET "+last_part_path+" FSP/1.0\r\n"+"Hostname: "+hostname+"\r\nAgent: xsechr00\r\n\r\n"
msg =str.encode(tcp_msg)
try:
	tcp_sock.send(msg)

except tcp_sock.timeout: 
	print("Waiting for long time!")
	exit(1)


get_file(filename,tcp_sock)

if(index):
	with open('index',"r") as file:
		row = file.readline()
		while row:
			get_next_files(hostname,row.strip(),adr,port)
			row = file.readline()

	file.close()

	

tcp_sock.close()