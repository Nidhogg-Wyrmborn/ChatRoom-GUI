try:
	# imports
	from Assets.utils import listhas, Timeout
	import sys
	import time
	import os
	import re
	import threading
	from concurrent.futures import ThreadPoolExecutor
	if len(sys.argv) > 1:
		if listhas(sys.argv, '-o','--offline'):
			import Assets.OfflineSocket as socket
		else:
			import socket
	else:
		import socket
except ImportError as IE:
    raise IE

class Client:

	STRING = 0
	CODE = 1
	DEBUG = 2

	VERSION = "0.1.0" # Release.Major.Minor

	def __init__(self):
		self.closed = True
		self.messages = []
		self.message_lock = threading.Lock()
		self.host = None
		self.port = None
		self.tLimit = 3
		self.marker_pattern = re.compile(r"<\|.*?\|>")
		self.socket = self.newSock()

	def newSock(self):
		return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def find_server(self, port: int = 65242):
		# find any servers that are active
		
		ip_base = self._ip_base()
		if not ip_base:
			return

		servers = []

		target_ips = [f"{ip_base}{i}" for i in range(1,255)]

		with ThreadPoolExecutor(max_workers=100) as executor:
			results = executor.map(lambda ip: self._check_ip_port(ip, port), target_ips)

			for result in results:
				if result:
					servers.append(result)

		return servers

	def get_server_name(self, server: tuple) -> str:
		return server[0]

	@staticmethod
	def _check_ip_port(ip, port, timeout=1.0):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.settimeout(timeout)
				result = s.connect_ex((ip, port))
				if result == 0:
					return (ip, port)
		except Exception:
			pass
		return None

	@staticmethod
	def _ip_base():
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			s.connect(('10.255.255.255', 1))
			local_ip = s.getsockname()[0]
			ip_base = '.'.join(local_ip.split('.')[:-1]) + '.'
			return ip_base
		except Exception:
			return None
		finally:
			s.close()

	def connect(self, addr, port):
		self.host = addr
		self.port = port
		self._connect()
		self.closed = False

	def reconnect(self):
		self._connect()

	def _connect(self):
		self.socket.connect((self.host, self.port))
		print(f"[CLIENT] Connected to {self.host}:{self.port}")

	def recv(self):
		while not self.closed:
			try:
				# simulate work
				response = self.socket.recv(1024).decode("utf-8")
				with self.message_lock:
					self.messages.append(response)
				pass
			except socket.error:
				# disconnected
				self.disconnect()

	def is_connected(self) -> bool:
		return not self.closed

	def sendCode(self, msg):
		self.socket.sendall(msg.encode("utf-8"))

	def send(self, msg):
		msg = msg.replace("<","\\<")
		msg = msg.replace("|","\\|")
		msg = msg.replace(">","\\>")
		self.socket.sendall(msg.encode("utf-8"))

	def has_message(self, tp: int = 0) -> bool:
		with self.message_lock:
			if tp == self.STRING:
				if len(self.messages) <= 0:
					return False
				if len(self.messages) > 0:
					result = not self.marker_pattern.search(self.messages[0])
					return result
			elif tp == self.CODE:
				if len(self.messages) > 0:
					return self.marker_pattern.search(self.messages[0])
			elif tp == self.DEBUG:
				return True
			return False

	def getMsg(self):
		with self.message_lock:
			msg = self.messages.pop(0)
			msg = msg.replace("\\<","<")
			msg = msg.replace("\\|","|")
			msg = msg.replace("\\>",">")
			return msg

	def waitAck(self) -> bool:
		is_valid = Timeout(self.tLimit)
		while is_valid():
			# waiting for message
			if self.has_message(self.CODE):
				msg = self.getMsg()
				if msg.startswith("<|ACK|>"):
					return True
				else:
					return False
		return False

	def waitAckRet(self) -> str:
		is_valid = Timeout(self.tLimit)
		while is_valid():
			# waiting for message
			if self.has_message(self.CODE):
				msg = self.getMsg()
				if msg.startswith("<|ACK|>"):
					return msg
				else:
					return msg
		return ""

	def disconnect(self):
		self.socket.close()
		self.socket = self.newSock()
		self.closed = True
		self.messages = []
		return