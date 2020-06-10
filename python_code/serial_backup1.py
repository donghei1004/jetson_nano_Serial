import serial 
import time

def timer():
	now = time.localtime(time.time())
	return now[5]
#포트 설정
PORT = '/dev/ttyUSB0'
BAUDRATE = 115200

#연결
ser =serial.Serial(PORT,BAUDRATE)
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = None
ser.xonxoff = False
ser.rtscts = False
ser.dsrdtr = False
ser.writeTimeout = 0

print("Starting Up Serial Monitor")

try:
	ser.open()
except Exception as e:
	print("Exception : Opening serial port : " + str(e))



if ser.isOpen():
	try:
		f = open("log.txt",'w')
		strBuf = ""
		strMsg = ""
		ser.flushInput()
		ser.flushOutput()
		numberOfLine =0
		msgFlag = 0
		now = timer()
		t = now
		while True:
#response = ser.readline()
			response = ser.read()
			if response == b'<':
				strBuf = ""
			if response == b'\n':
#print("msg : %s"%strBuf)
				f.write(strBuf+"\n")
				msgFlag = 1
			if response[0]<=0x7F :
				if response.decode().isprintable() :
					strBuf = strBuf + "%c " % response.decode()
				else : 
					strBuf = strBuf + "%02x " % response[0]
			else :
				strBuf = strBuf + "%02x " % response[0]
			
			numberOfLine = numberOfLine + 1
			if (numberOfLine >= 4000000):
				break
#print("num : {:0},{:1},\n".format(numberOfLine,response[0]))
			if (timer() - now) >=10:
				break
		ser.close()
		f.close()
	except Exception as e:
		print("Error communication...: "+str(e))
		ser.close()
	ser.close()
else :
	print("Cannot open serial port.")

