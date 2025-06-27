#!/usr/bin/python3

import serial
import cbor2
import crc 
from enum import Enum


class _MsgId(Enum):

    # No param messages
        emergency_stop=10
        emergency_stop_reset=11
        normal_speed_acc_mode=15
        slow_speed_acc_mode=16
    # Two param messages  
        max_motor_speed=17 # Only one param mandatory here, but add a dummy ID one
        turn=20
        straight=21
    # Three param messages
        face=22
        goto_front=23
        goto_back=24
        goto_nostop=25
        
        



def createEmergencyStopMessage() -> bytes:
    msg = {"cmd": _MsgId.emergency_stop.value}
    return _formatMsg(msg)

def createEmergencyStopResetMessage() -> bytes:
    msg = {"cmd": _MsgId.emergency_stop_reset.value}
    return _formatMsg(msg)

def createNormalAccSpeedModeMessage() -> bytes:
    msg = {"cmd": _MsgId.normal_speed_acc_mode.value}
    return _formatMsg(msg)  

def createSlowAccSpeedModeMessage() -> bytes:
    msg = {"cmd": _MsgId.slow_speed_acc_mode.value}
    return _formatMsg(msg)  


def createMaxMotorSpeedMessage( percentage : float ) -> bytes:
    msg = {"cmd": _MsgId.max_motor_speed.value,
    "P" : float(percentage),
    "ID": int(4242)} # Add a dummy ID to make the decoding part easier
    return _formatMsg(msg)  


def createTurnMessage(cmd_id : int, angle_in_deg : float) -> bytes:
    msg = {"cmd": _MsgId.turn.value,
    "A" : float(angle_in_deg),
    "ID": int(cmd_id)}
    return _formatMsg(msg)

def createStraightMessage(cmd_id : int, dist_in_mm : float) -> bytes:
    msg = {"cmd": _MsgId.straight.value,
    "D" : float(dist_in_mm),
    "ID": int(cmd_id)}
    return _formatMsg(msg)


def createFaceMessage(cmd_id : int, X : float, Y : float ) -> bytes:
    msg = {"cmd": _MsgId.face.value,
    "X" : float(X) ,
    "Y" : float(Y) ,
    "ID": int(cmd_id)}
    return _formatMsg(msg)    

def createGotoMessage(cmd_id : int, X : float, Y : float ) -> bytes:
    msg = {"cmd": _MsgId.goto_front.value,
    "X" : float(X),
    "Y" : float(Y),
    "ID": int(cmd_id) }
    return _formatMsg(msg)

def createGotoBackMessage(cmd_id : int, X : float, Y : float ) -> bytes:
    msg = {"cmd": _MsgId.goto_back.value,
    "X" : float(X),
    "Y" : float(Y),
    "ID": int(cmd_id) }
    return _formatMsg(msg)    

def createGotoNoStopMessage(cmd_id : int, X : float, Y : float ) -> bytes:
    msg = {"cmd": _MsgId.goto_nostop.value,
    "X" : float(X),
    "Y" : float(Y),
    "ID": int(cmd_id) }
    return _formatMsg(msg)  



def _formatMsg(msg):
    syncword = 0xDEADBEEF
    msg_cbor = cbor2.dumps(msg)
    msg_cbor_len = len(msg_cbor)
    calculator = crc.Calculator(crc.Crc32.AUTOSAR)
    crc_computed = calculator.checksum(msg_cbor)
    return ( syncword.to_bytes(length=4, byteorder='little', signed=False)     +
                crc_computed.to_bytes(length=4, byteorder='little', signed=False) +
                msg_cbor_len.to_bytes(length=4, byteorder='little', signed=False) +
                msg_cbor)
