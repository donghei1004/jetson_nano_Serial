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

if ser.isOpen():
	ser.close()
try:
	ser.open()
except Exception as e:
	print("Exception : Opening serial port : " + str(e))



if ser.isOpen():
	try:
		f = open("log.txt",'w')
		strBuf = ""

		dataIdx = 0
		dataLength = 0
		dataParams = ['']*10
		params =0
		paramIdx=0
		chsum =0

		ser.flushInput()
		ser.flushOutput()
		msgFlag = 0
		now = timer()
		while True:
			response = ser.read()
			chsum = chsum ^ response[0]
			if dataIdx ==0:	# Start Message
				if response == b'<':
					chsum =0
					msgFlag =0
					params = 0
					dataIdx =0
					dataLength =0
					dataParams = ['']*6
			elif ((response==b'*')or(response == b',')) and (params != 4):	
				params = params+1
			elif params==2:
				dataLength = dataLength*10 + (response[0] - 0x30)
			elif params==3:
				dataIdx =1
	
			if response != b',' and response != b'*':
				if response[0]<=0x7F:
					if response.decode().isprintable() :
						dataParams[params] = dataParams[params] + "%c"%response.decode()	
					else:
						dataParams[params] = dataParams[params] + " 0x%02x "%response[0]
					
				else : 
					dataParams[params] = dataParams[params] + " 0x%02x "%response[0]
			dataIdx = dataIdx +1
			if (dataIdx >= (dataLength-4)) and (params==4) :
				params = params +1
			if (params >2) and (dataIdx>=dataLength) :
				msgFlag =1
				dataLength = dataIdx
				dataIdx =0
			elif (params<1) and (dataIdx > 2):
				dataIdx =0
				dataParams = ['']*6


			if msgFlag :
				#print(dataParams)
				strdata = '\t'.join(dataParams)
				f.write(strdata)
				print(strdata+'\n')
				f.write("\n")
				msgFlag =0

			if response[0]<=0x7F :
				if response.decode().isprintable() :
					strBuf = strBuf + "%c " % response.decode()
				else : 
					strBuf = strBuf + "%02x " % response[0]
			else :
				strBuf = strBuf + "%02x " % response[0]
			
#print("num : {:0},\n".format(response[0]))
				 
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

