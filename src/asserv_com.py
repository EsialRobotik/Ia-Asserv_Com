#!/usr/bin/python3

import serial
import cbor2
import crc 


def _byteInInt(number, i):
    return (number & (0xff << (i * 8))) >> (i * 8)


class _SerialCborState_synchroLoopkup:
  def __init__(self):
    self.syncword = 0xDEADBEEF
    self.reset()
    
  def reset(self):
    self.nb_byte_of_syncword_found = 0

  def push_byte(self, byte):
    if byte == _byteInInt(self.syncword, self.nb_byte_of_syncword_found) :
        self.nb_byte_of_syncword_found = self.nb_byte_of_syncword_found + 1 
    else :
        self.nb_byte_of_syncword_found = 0

    if self.nb_byte_of_syncword_found == 4 :
        #  Synchro found
        self.reset()
        return ("state_decode", None)
    return (None, None)


class _SerialCborState_decode:
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
    self.state = _SerialCborState_synchroLoopkup()
    self.payloads = []

  def push_byte(self, byte):
    (new_state, payload) = self.state.push_byte(byte)
    if new_state == "state_decode" :
        self.state = _SerialCborState_decode()
    elif new_state == "state_synchroLookup" :
        self.state = _SerialCborState_synchroLoopkup()

    if payload != None :
        self.payloads.append(payload)

  def pop_payload(self):
    return self.payloads.pop(0)

  def get_nb_payload(self):
    return len(self.payloads)



def sendMsg(serial, msg):
    syncword = 0xDEADBEEF
    msg_cbor = cbor2.dumps(msg)
    msg_cbor_len = len(msg_cbor)
    calculator = crc.Calculator(crc.Crc32.AUTOSAR)
    crc_computed = calculator.checksum(msg_cbor)
    serial.write(syncword.to_bytes(length=4, byteorder='little', signed=False))
    serial.write(crc_computed.to_bytes(length=4, byteorder='little', signed=False))
    serial.write(msg_cbor_len.to_bytes(length=4, byteorder='little', signed=False))
    serial.write(msg_cbor)
