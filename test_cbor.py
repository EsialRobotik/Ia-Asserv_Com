#!/usr/bin/python3

import serial
import cbor2
import crc 


def byteInInt(number, i):
    return (number & (0xff << (i * 8))) >> (i * 8)


def byteToInt(number, byte, byte_idx):
    return number + ()


class SerialCborState_synchroLoopkup:
  def __init__(self):
    self.syncword = 0xDEADBEEF
    self.reset()
    
  def reset(self):
    self.nb_byte_of_syncword_found = 0

  def push_byte(self, byte):
    if byte == byteInInt(self.syncword, self.nb_byte_of_syncword_found) :
        self.nb_byte_of_syncword_found = self.nb_byte_of_syncword_found + 1 
    else :
        self.nb_byte_of_syncword_found = 0

    if self.nb_byte_of_syncword_found == 4 :
        #  Synchro found
        self.reset()
        return ("state_decode", None)
    return (None, None)


class SerialCborState_decode:
  def __init__(self):
    self.reset()
    
  def reset(self):
    self.size = []
    self.size_decoded = 0
    self.crc = []
    self.crc_decoded = 0
    self.payload = bytearray()
 
  def push_byte(self, byte):
    if len(self.crc) < 4 :
        self.crc.append(byte)
        if len(self.crc) == 4 :
            self.crc_decoded = int.from_bytes(self.crc, byteorder='little')
    elif len(self.size) < 4 :
        self.size.append(byte) 
        if len(self.size) == 4 :
            self.size_decoded = int.from_bytes(self.size, byteorder='little')
    elif len(self.payload) < self.size_decoded :
        self.payload.append(byte)
        if len(self.payload) == self.size_decoded:
            calculator = crc.Calculator(crc.Crc32.AUTOSAR)
            crc_computed = calculator.checksum(self.payload)
            if crc_computed == self.crc_decoded :
                return ("state_synchroLookup", self.payload)
            else :
                return ("state_synchroLookup", None)
    return (None, None)
        

class SerialCborStateMachine:
  def __init__(self):
    self.syncword = 0xDEADBEEF
    self.state = SerialCborState_synchroLoopkup()
    self.payloads = []

  def push_byte(self, byte):
    (new_state, payload) = self.state.push_byte(byte)
    if new_state == "state_decode" :
        self.state = SerialCborState_decode()
    elif new_state == "state_synchroLookup" :
        self.state = SerialCborState_synchroLoopkup()

    if payload != None :
        self.payloads.append(payload)

  def pop_payload(self):
    return self.payloads.pop(0)

  def get_nb_payload(self):
    return len(self.payloads)


ser = serial.Serial('/dev/ttyACM0', 115200)

stateMachine = SerialCborStateMachine() 


while True:
    x = ser.read() 
    for val in x :
        stateMachine.push_byte(val)

    if stateMachine.get_nb_payload() > 0 :
        payload = stateMachine.pop_payload()
        cbor_msg = cbor2.loads(payload)
        print(cbor_msg)



def sendMsg(msg):
    syncword = 0xDEADBEEF
    msg_cbor = cbor2.dumps(msg)
    msg_cbor_len = len(msg_cbor)
    calculator = crc.Calculator(crc.Crc32.AUTOSAR)
    crc_computed = calculator.checksum(msg_cbor)
    print("msg_cbor %s  size %d  crc_computed %x " % (str(msg_cbor), msg_cbor_len+3*4, crc_computed))
    ser.write(syncword.to_bytes(length=4, byteorder='little', signed=False))
    ser.write(crc_computed.to_bytes(length=4, byteorder='little', signed=False))
    ser.write(msg_cbor_len.to_bytes(length=4, byteorder='little', signed=False))
    ser.write(msg_cbor)



# msg = {"cmd": 1 ,
#         "X" : 5000.55 ,
#         "Y" : 1000.11 }
# sendMsg(msg)


# msg2 = {"cmd": 2 ,
#         "X" : 5000 ,
#         "Y" : 1000 }
# sendMsg(msg2)
