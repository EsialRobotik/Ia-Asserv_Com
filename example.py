import serial
import cbor2
from src.asserv_com import *

ser = serial.Serial('/dev/ttyACM0', 115200)

stateMachine = SerialCborStateMachine() 

msg = {"cmd": MsgId.emergency_stop.value ,
        "X" : 5000.55 ,
        "Y" : 1000.11 }
sendMsg(ser, msg)


# msg2 = {"cmd": 2 ,
#         "X" : 5000 ,
#         "Y" : 1000 }
# sendMsg(ser, msg2)


while True:
    x = ser.read() 
    for val in x :
        stateMachine.push_byte(val)

    if stateMachine.get_nb_payload() > 0 :
        payload = stateMachine.pop_payload()
        cbor_msg = cbor2.loads(payload)
        print(cbor_msg)
