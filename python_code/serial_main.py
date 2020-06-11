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


FLAG_START = 1
FLAG_END = 2
FLAG_WAIT = 0

if ser.isOpen():
	try:
		rawf = open("log_raw.txt",'w')
		strBuf = ""

		dataIdx = 0
		dataLength = 0
		dataParams = [b'']*7
		startFlag = 0
		params =0
		paramIdx=0
		chsum =0

		ser.flushInput()
		ser.flushOutput()
		msgFlag = 0
		now = timer()
		while True:
			response = ser.read()
			if startFlag==FLAG_WAIT:	# Start Message
				chsum =0
				msgFlag =0
				params = 0
				dataIdx =0
				dataLength =0
				dataParams = [b'']*7
				if response == b'<':
					startFlag = FLAG_START
					dataParams[params] = response

			elif startFlag == FLAG_START:
				if params < 5 : 
					chsum = chsum^response[0]
				if ((response==b'*')or(response == b',')) and (params != 4):	
					params = params+1
					if params== 3 : dataIdx =0
				elif params==2:
					dataLength = dataLength*10 + (response[0] - 0x30)
				elif params==4  and (dataIdx>= dataLength-5):
					params = params +1
	
				if (response != b',') and (response != b'*'):
					dataParams[params]=dataParams[params] + response
				elif (params==4) and (len(dataParams[params]) >0):
					dataParams[params]=dataParams[params] + response

				dataIdx = dataIdx +1

			if (params >2) and (dataIdx>=dataLength) :
				dataLength = dataIdx
				dataIdx =0
				startFlag = FLAG_END


			#print("[{:3},{:0},{:1}] {:2}".format(params,dataIdx,dataLength,' '.join(dataParams)))
			if startFlag == FLAG_END :
				chsum = chsum^(b'*'[0])
				#print("{:1}[{:02x}]".format(str(b''.join(dataParams)),chsum))
				if dataParams[3] == b'1':		# BNO Data
					yaw = int.from_bytes(dataParams[4][:2],'little',signed=True)/16.0
					pitch = int.from_bytes(dataParams[4][2:4],'little',signed=True)/16.0
					roll = int.from_bytes(dataParams[4][4:],'little',signed=True)/16.0
					print("BNO[{:1}|{:02x}] {:.3f}\t{:.3f}\t{:.3f}".format(str(dataParams[5][:2].decode()),chsum,roll,pitch,yaw))
					#f.write("BNO[{:1}|{:02x}] {:.3f}\t{:.3f}\t{:.3f}\n".format(str(dataParams[5][:2].decode()),chsum,roll,pitch,yaw))
				elif (dataParams[3] == b'2') and (len(dataParams[4])>=12):		# GPS Data
					gps_valid = dataParams[4][0]
					gps_time = int.from_bytes(dataParams[4][1:5],'little')/1000.0
					gps_lat = int.from_bytes(dataParams[4][5:9],'little')/1000000.0
					gps_lng = int.from_bytes(dataParams[4][9:],'little')/1000000.0
					print("GPS[{:1}|{:02x}] {:.3f}\t{:.6f}\t{:.6f}".format(str(dataParams[5][:2].decode()),chsum,gps_time,gps_lat,gps_lng))
					#f.write("GPS[{:1}|{:02x}] {:.3f}\t{:.6f}\t{:.6f}\n".format(str(dataParams[5][:2].decode()),chsum,gps_time,gps_lat,gps_lng))
					rawf.write("[{:3}] {:1}[0x{:02x} 0x{:02x}]\n".format(gps_time,str(b''.join(dataParams)),(chsum>>4),(chsum&0x0F)))
				else :
					print("Parse Error : ")
					print(str(dataParams))
						

				startFlag = FLAG_WAIT
				rawf.write("{:1}[0x{:02x} 0x{:02x}]\n".format(str(b''.join(dataParams)),(chsum>>4),(chsum&0x0F)))
				
#			if (timer() - now) >= 10:
#break

		ser.close()
		rawf.close()
	except Exception as e:
		print("Error communication...: "+str(e))
		ser.close()
	ser.close()
else :
	print("Cannot open serial port.")

