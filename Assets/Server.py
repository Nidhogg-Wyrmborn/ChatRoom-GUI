try:
	# imports
	from Assets.utils import *
	import sys
	import os
	import re
	from colorama import Fore
	import threading
	import Assets.stdout_helpers as sh
	if len(sys.argv) > 1:
		if listhas(sys.argv, '-o','--offline'):
			import Assets.OfflineSocket as socket
		else:
			import socket
	else:
		import socket
except ImportError as IE:
    raise IE

class Server:

	VERSION = "0.2.0" # Release.Major.Minor

	def __init__(self, host: str = "0.0.0.0", port: int = 65242):
		self.redirect()
		self.host = host
		self.port = port
		self.name = "defaultName"
		self.newSock()
		self.clients = {}
		self.running = True
		self.shutdown = True
		self.message_lock = threading.Lock()
		self.message_queue = []
		self.logs = []
		self.log_lock = threading.Lock()
		self.kv_pattern = r"<\|SET_(?P<key>\w+)\|>(?P<val>.*?)<\|END_SET\|>"
		self.colors = {
			"red": Fore.RED,
			"green": Fore.GREEN,
			"yellow": Fore.YELLOW,
			#"blue": Fore.BLUE,
			"barny the dinosaur purple": Fore.MAGENTA,
			"cyan": Fore.CYAN,
			"white": Fore.WHITE
		}

		# a dictionary of commands this server accepts and the packet it expects:
		# when a value inside the asterisk (*) is surrounded by square brackets ([]) it can only accept those values, nothing else.
		# each value inside the square brackets would be separated by pipes (|) and are strings
		# color: <|SET_COLOR|>*value*<|END_SET|>
		# * value is separated by pipes to indicate different options
		# * what is inside the asterisk (*) is what is allowed to be changed
		# uname: <|SET_UNAME|>*value*<|END_SET|>
		# * value is a string (because the packet is received as a string, i don't need to declare type)
		# * what is inside the asterisk (*) is what is allowed to be changed
		self.command2packets = {
			"color": create_packet_template("color", list(self.colors.keys())),
			"uname": create_packet_template("uname"),
		}

	def redirect(self, target=None):
		if target == None:
			self.redirected = False
			self.redirect2 = lambda *kwargs: print(*kwargs)
		else:
			self.redirected = True
			self.redirect2 = target

	def print(self, *kwargs):
		self.redirect2(*kwargs)

	def start(self):
		self.shutdown = False
		self.socket.bind((self.host, self.port))
		self.socket.listen(1)
		self.socket.settimeout(1.0)
		self.print(f"[SERVER] Listening on {self.host}:{self.port}...")

		bm = threading.Thread(target=self._broadcast_message, args=(), daemon=True)
		bm.start()

		try:
			self._accept_handle()
		except KeyboardInterrupt:
			self.print(f"[SERVER] KeyboardInterrupt Detected!")
			self.stop()

		self.print(f"[SERVER] Ending Existing connections!")
		for addr in self.clients:
			self.print(f"[SERVER] Waiting for {addr}")
			self.clients[addr][0].join()

		self.print("[SERVER] Waiting for _broadcast_message")
		bm.join()

		self.print(f"[SERVER] Connection closed.")
		self.socket.close()

		for log in self.logs:
			self.print(log)
		self.shutdown = True

	def _accept_handle(self):
		while self.running:
			try:
				conn, addr = self.socket.accept()
				self.print(f"[SERVER] Connection from {addr}")

				self.clients[addr] = [threading.Thread(target=self._client_handle, args=(conn, addr,), daemon=True), conn]
				self.clients[addr][0].start()

			except socket.timeout:
				# server timed out (DO NOT PRINT TO LOG FOR THE LOVE OF SPAGHETTI)
				# self.print(f"[SERVER] Listen Timeout")
				continue

			except Exception as e:
				if self.running:
					self.print(f"[SERVER] ERROR:\n{e}")
					self.stop()
					
				else:
					pass

	def _broadcast_message(self):
		while self.running:
			with self.message_lock:
				while len(self.message_queue) > 0:
					msg = self.message_queue.pop(0)
					to_remove = []

					for addr in self.clients:
						try:
							self.clients[addr][1].sendall(msg.encode("utf-8"))

						except Exception as e:
							with self.log_lock:
								self.logs.append(f'[_broadcast_message] ERROR: {e}')

							self.clients[addr][1].close()
							to_remove.append(addr)

					for addr in to_remove:
						del self.clients[addr]

	def handle_settingChange(self, data, conn, client_uname, client_color):
		if "VERSION" in data:
			if not version_check(self.VERSION, data.get("VERSION")):
				conn.sendall(("<|EOF|>" + Fore.RED + f"[SERVER] INVALID VERSION! Expected: {self.VERSION}").encode("utf-8"))
				conn.close()
				raise Exception("BAD VERSION")

		if "UNAME" in data:
			client_uname = data.get("UNAME")
			if "COLOR" not in data:
				conn.sendall(("<|ACK|>" + Fore.GREEN + "[SERVER] Name changed successfully").encode("utf-8"))
				self.print(f"[_client_handle] Sent Acknowledge for name change (success)")

		if "COLOR" in data:
			t_color = data.get("COLOR")
			if t_color in self.colors:
				client_color = t_color
				if "UNAME" not in data:
					conn.sendall(("<|ACK|>" + Fore.GREEN + "[SERVER] Color changed successfully").encode("utf-8"))
					self.print(f"[_client_handle] Sent Acknowledge for color change (success)")

			else:
				if "UNAME" not in data:
					conn.sendall(("<|ACK|>" + Fore.RED + "[SERVER] Invalid color selected").encode("utf-8"))
					self.print(f"[_client_handle] Sent Acknowledge for color change (Invalid)")

		if "UNAME" in data and "COLOR" in data and "VERSION" in data:
			ackCode = "<|ACK|>"
			for i, k in enumerate(self.command2packets):
				comm = self.command2packets[k]['command']
				packet = self.command2packets[k]['template']
				ackCode += f"{',' if i != 0 else ''}{comm}:{packet}"
			ackCode += "<|END_ACK|>"

			conn.sendall(ackCode.encode("utf-8"))

			self.print(f"[_client_handle] Sent Acknowledge for setting change")

			with self.message_lock:
				self.message_queue.append(f"{self.colors['green']}{client_uname} has joined the chat!")

		return client_uname, client_color

	def _client_handle(self, conn, addr):
		self.print(f"[_client_handle] started for {addr[0]}:{addr[1]}")

		client_color = "none"
		client_uname = "Anonymous"

		try:
			data = conn.recv(1024)

			if not data:
				log = sh.stop_redirect()
				if log:
					with self.log_lock:
						self.logs.append(f'[_client_handle] for {addr}:\n- ' + log.replace('\n[','\n- ['))
				return


			message = data.decode("utf-8")
			if message.upper().startswith("<|GET_NAME|>"):
				conn.sendall(f"<|ACK|>{self.name}<|END_ACK|>".encode("utf-8"))
				self.print("[_client_handle] Sent name to client")
				conn.close()
				error = False
				return

			data = dict(re.findall(self.kv_pattern, message))
			client_uname, client_color = self.handle_settingChange(data, conn, client_uname, client_color)

			while self.running:
				self.print("[_client_handle] Waiting for data!")
				data = conn.recv(1024)

				if not data:
					break

				message = data.decode("utf-8")
				self.print(f"[_client_handle] Received: {message}")

				data = dict(re.findall(self.kv_pattern, message))
				if len(data) == 0:
					with self.message_lock:
						self.message_queue.append(f"{self.colors[client_color]}{client_uname}: " + message)
				
				else:
					client_uname, client_color = self.handle_settingChange(data, conn, client_uname, client_color)
			error = False

		except socket.error as se:
			self.print(f"[_client_handle] Error: Socket Error: {se}")
			error = True
		except Exception as e:
			self.print(f"[_client_handle] FATAL EXCEPTION: {e}")
			error = True
		finally:
			self.print(f"[_client_handle] Handle has Closed")
			if error:
				with self.message_lock:
					self.message_queue.append(f"{self.colors['red']}{client_uname} has left the chat!")
		log = sh.stop_redirect()
		if log:
			with self.log_lock:
				self.logs.append(f'[_client_handle] for {addr}:\n- ' + log.replace('\n[','\n- ['))


	def stop(self):
		self.running = False

	def reset(self):
		# doesn't do anything for now
		self.newSock()
		self.shutdown = True
		self.running = True
		return

	def newSock(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	def is_running(self) -> bool:
		return not self.shutdown

	def set_name(self, name: str):
		self.name = name