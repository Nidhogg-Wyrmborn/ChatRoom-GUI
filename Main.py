try:
	# imports
	from Assets.utils import listhas
	import os
	import sys
	import io
	from colorama import Fore, init
	import threading
	if len(sys.argv) > 1:
		if listhas(sys.argv, '-o','--offline'):
			import Assets.OfflineSocket as socket
		else:
			import socket
	else:
		import socket
	import Assets.stdout_helpers as sh
	import Assets.Client as Client
	import Assets.Server as Server
except ImportError as IE:
	print(IE)
	import os, sys
	from pathlib import Path
	if not Path.exists(Path("./requirements.txt")):
		open("./requirements.txt", 'w').close()
	os.system("py -m pip install -r requirements.txt")
	input("Press Enter to continue...")
	os.execv(sys.executable, ["py"] + f"\"{sys.argv}\"")
	exit()

debug = True if listhas(sys.argv, '-d','--debug') else False

# enable proxy
sh.enable_proxy()

# initialize colorama
init(autoreset=True)

def start_server(stop_event):
	io_stream = sh.redirect()
	errors = []
	try:
		server = Server.Server()
		server.start(stop_event)
		server.close()
	except Exception as e:
		# error has occured
		errors.append(e)
	finally:
		rv = sh.stop_redirect()
		print("[SERVER] Logs: ")
		print(rv)
		for e in errors:
			print(e)

def srvr():

	stop_signal = threading.Event()

	server_thread = threading.Thread(target=start_server, args=(stop_signal,), daemon=True)
	server_thread.start()

	input("Press Enter to close the server!\n$> ")
	stop_signal.set()
	server_thread.join()
	sh.disable_proxy()
	quit()

def getMsg(client):
	while client.is_connected():
		if client.has_message(client.DEBUG if debug else client.STRING):
			msg = client.getMsg()
			if msg:
				print(msg)

def clnt():
	uName = input("What is your username?\n$> ")
	colors = {
		"red": Fore.RED,
		"green": Fore.GREEN,
		"yellow": Fore.YELLOW,
		"blue": Fore.BLUE,
		"Barny the Dinosaur Purple": Fore.MAGENTA,
		"cyan": Fore.CYAN,
		"white": Fore.WHITE,
	}
	aColors = [
		"red",
		"green",
		"yellow",
		"blue",
		"Barny the Dinosaur Purple",
		"cyan",
		"white"
	]
	color = "white"
	client = Client.Client()
	servers = client.find_server()
	print(f"Found {len(servers)} servers!")
	if len(servers) == 0:
		return
	if len(servers) > 1:
		for i in range(len(servers)):
			print(f"{i}: {servers[i]}")
		choice = int(input("Select a server:\n$> "))
	else:
		choice = 0
	server = servers[choice]
	print(servers)
	print(server)
	addr, port = server[0], server[1]
	client.connect(addr, port)
	recv_thread = threading.Thread(target=client.recv, args=(), daemon=True)
	recv_thread.start()

	get_thread = threading.Thread(target=getMsg, args=(client,), daemon=True)

	client.sendCode(f"<|SET_UNAME|>{uName}<|END_SET|><|SET_COLOR|>{color}<|END_SET|><|SET_VERSION|>{client.VERSION}<|END_SET|>")
	ack = client.waitAckRet()
	if not ack:
		print(ack.replace("<|EOF|>",""))
		print("Server did not send acknowledge!")
		return
	print(f"Welcome {uName}! You have Connected Successfully!")
	get_thread.start()

	while client.is_connected():
		msg = input("$> ")
		match msg:
			case s if s.startswith('#'):
				match s.lower():
					case "#quit" | "#exit":
						client.disconnect()
					case "#help":
						print("Available commands:")
						print(f"{'quit | exit':>8}")
						print(f"{'uname':>8}")
						print(f"{'color':>8}")
					case "#uname":
						uName = input("type a new username:\n$> ")
						client.sendCode(f"<|SET_UNAME|>{uName}<|END_SET|>")
						ack = client.waitAckRet()
						if not ack:
							print("request not acknowledged")
						else:
							print(ack.replace("<|ACK|>",""))
					case "#color":
						for c in aColors:
							print(colors[c] + c)
						color = input("select a new color:\n$> ")
						client.sendCode(f"<|SET_COLOR|>{color}<|END_SET|>")
						ack = client.waitAckRet()
						if not ack:
							print("request not acknowledged")
						else:
							print(ack.replace("<|ACK|>",""))
					case _:
						print("Unknown command, type #help for a list of commands")
			case _:
				if msg:
					client.send(msg)

	recv_thread.join()
	get_thread.join()

if __name__ == '__main__':
	if listhas(sys.argv, '-o','--offline'):
		raise NotImplementedError("ERROR: OFFLINE FUNCTIONALITY IS NOT PROPERLY IMPLEMENTED")
	if listhas(sys.argv, '-c','--client'):
		clnt()
		input("Press Enter to quit...")
		quit()
	if listhas(sys.argv, '-s','--server'):
		srvr()
		input("Press Enter to quit...")
		quit()
	pType = input("[s]erver or [c]lient?\n$> ")
	match pType:
		case t if t.lower().startswith('s'):
			srvr()
		case t if t.lower().startswith('c'):
			clnt()
		case _:
			print("Not valid")
	input("Press Enter to quit...")
	quit()