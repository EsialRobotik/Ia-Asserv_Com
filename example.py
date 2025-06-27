import serial
import cbor2
from src.asserv_com_input import *
from src.asserv_com_output import *
import threading
import time

# 1st the uart line to read/write
uart = serial.Serial('/dev/ttyACM0', 115200)

# 2nd, the state machine that decode the input stream
stateMachine = InputCborStateMachine() 


# 3rd, an example of sending a command
def send_thread(name):
    time.sleep(2)
    # cbor = createStraightMessage(666, 1500.0)
    cbor = createGotoMessage(666, 1500.0, 1500.0)
    uart.write(cbor)

x = threading.Thread(target=send_thread, args=(1,))
x.start()


# 4th the "pump"
while True:
    x = uart.read() 
    for val in x :
        stateMachine.push_byte(val)

    if stateMachine.get_nb_payload() > 0 :
        payload = stateMachine.pop_payload()
        print(payload)
