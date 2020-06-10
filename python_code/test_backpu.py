import sys	
import time
import serial 
import threading
import queue

class Protocol(object):
	"""\
	Protocol as used by the ReaderThread. This base class provides empty
	implementations of all methods.
	"""

	def connection_made(self, transport):
		""" Called when reader thread is started """

	def data_received(self, data):
		""" Called with snippets received from the serial port"""

	def connection_lost(self, exc):
		"""\
		Called when the serial port is closed or the reader loop terminated
		otherwise.
		"""
		if isinstance(exc,Exception):
			raise exc
	

class ReaderThread(threading.Thread):
	"""\
	Implement a serial port read loop and dispatch to a Protocol instance (like
	the asyncio.Protocol) but do it with threads.
	Calls to close() will close the serial port but it is also possible to just
	stop() this thread and continue the serial port instance otherwise.
	"""
	def __init__(self,serial_instance, protocol_factory):
		"""\
		Initialize thread.
		Note that the serial_instance' timeout is set to one second!
		Other settings are not chaned.
		"""

		super(ReaderThread, self).__init__()
		self.daemon = True
		self.serial = serial_instance
		self.protocol_factory = protocol_factory
		self.alive = True
		self._lock = threading.Lock()
		self._connection_made = threading.Event()
		self.protocol = None
		
	def stop(self):
		""" Stop the reader thread"""
		self.alive = False
		if hasattr(self.serial,'cancel_read'):
			self.serial.cancel_read()
		self.join(2)

	def run(self):
		""" Reader loop """
		if not hasattr(self.serial, 'cancel_read'):
			self.serial.timeout =1 
		self.protocol = self.protocol_factory()
		try:
			self.protocol.connection_made(self)
		except Exception as e:
			self.alive = False
			self.protocol.connection_lost(e)
			self._connection_made.set()
			return
		error = None
		self._connection_made.set()
		while self.alive and self.serial.is_open:
			try:
				# read all that is ther or wait for one byte(blocking)
				data = self.serial.read(self.serial.in_waiting or 1)
			except serial.SerialException as e:
				# probably some I/O problem such as disconnected USB serial
				# adapters -> Exit
				error = e
				break
			else:
				if data:
					# make a separated try-except for called used code
					try:
						self.protocol.data_received(data)
					except Exception as e:
						error = e
						break
		self.alive = False
		self.protocol.connection_lost(error)
		self.protocol = None

	def write(self, data):
		""" Thread safe writing (uses lock) """
		with self._lock:
			print(data)
			self.serial.write(data)

	def close(self):
		""" Close the serial port and exit reader thread (uses lock) """
		# use the lock to let other threads finish writing
		with self._lock:
			# first stop reading, so that closing can be done on idle port
			self.stop()
			self.serial.close()

	def connect(self):
		"""
		Wait until connection is set up and return the transport and protocol 
		instance.
		"""
		if self.alive:
			self._connection_made.wait()
			if not self.alive:
				raise RuntimeError('connection_lost already called')
			return (self, self.protocol)
		else :
			raise RuntimeError('already stopped')

	# --  context manager, returns protocol

	def __enter__(self):
		"""\
		Enter context handle. may raise RuntimeError in case the connection
		could not be created.
		"""
		self.start()
		self._connection_made.wait()
		if not self.alive:
			raise RuntimeError('connection_lost already called')
		return self.protocol

	def __exit__(self,exc_type, exc_val, exc_tb):
		""" Leave context : close port"""
		self.close()


# 키 인덱스
KEY_LEFT	= 0
KEY_UP		= 1
KEY_RIGHT	= 2
KEY_DOWN	= 3
KEY_SELECT	= 4
KEY_START	= 5
KEY_SQUARE	= 6
KEY_TRIANGLE= 7
KEY_X		= 8
KEY_CIRCLE	= 9


# 키 매핑
Keymap = {
	b'a' : [KEY_LEFT, 'KEY_LEFT'],
	b'w': [KEY_UP, 'KEY_UP'],
	b'd': [KEY_RIGHT, 'KEY_RIGHT'],
	b's': [KEY_DOWN, 'KEY_DOWN'],
	b'1': [KEY_SELECT, 'KEY_SELECT'],
	b'2': [KEY_START, 'KEY_START'],
	b'y': [KEY_SQUARE, 'KEY_SQUARE'],
	b'u': [KEY_TRIANGLE, 'KEY_TRIANGLE'],
	b'h': [KEY_X, 'KEY_X'],
	b'j': [KEY_CIRCLE, 'KEY_CIRCLE'],
	}

# 프로토콜
class rawProtocal(Protocol):
	# 연결 시작시 발생
	def connection_made(self,transport):
		self.transport = transport
		self.running = True
		self.strBuf = ""
		self.msgFlag =0
		

	#연결 종료시 발생
	def connection_lost(self,exc):
		self.transport = None
	
	# 데이터가 들어오면 이곳에서 처리.
	def data_received(self, data):
		#입력된 데이터와 키맵 비교 
		#print(data)
		if data == b'<':
			self.strBuf = ""
		if data == b'\n' :
			self.msgFlag =1

		for i in range(len(data)):
			#self.strBuf = self.strBuf + "%02x" % int.from_bytes(data[i],'big')
			self.strBuf = self.strBuf + "%02x " % data[i]

		if data in Keymap:
			# print string
			#print(Keymap[data][1])
			
			key = Keymap[data][0]

			if key == KEY_CIRCLE:
				self.running = False

	# 데이터를 보낼때 함수
	def write(self,data):
		print(data)
		self.transport.write(data)

	# 종료 체크 
	def isDone(self):
		return self.running

#포트 설정
PORT = '/dev/ttyUSB0'
#연결
ser = serial.serial_for_url(PORT,baudrate=115200,timeout=1)

tmp = 1;
strBuf = "";

#쓰레드 시작
with ReaderThread(ser,rawProtocal) as p:
	with open("log.txt",'w') as f:
		while p.isDone():
			time.sleep(1)
			if p.msgFlag :
				print("msg : " + p.strBuf)
				f.write(p.strBuf)
				p.msgFlag =0




