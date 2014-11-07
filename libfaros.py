#!/usr/bin/env python2

# This library implements the Bluetooth protocol
# for the Mega Electronics Ltd. Faros device.
#
# Copyright 2014
# Andreas Henelius <andreas.henelius@ttl.fi>
# Finnish Institute of Occupational Health
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
#
# Please see the file LICENSE for details.


import serial
from construct import *


def get_firmware(ser):
    ser.write(bytes("\\wbainf\r"))
    res = ser.read(9).decode("UTF-8").strip()
    return(res)

def get_firmware_build_date(ser):
    ser.write(bytes("\\wbaind\r"))
    res = ser.read(9).decode("UTF-8").strip()
    return(res)

def set_ecg_fs(ser, fs):
    fs_map = {1000: "\\wbafs1\r",
              500:  "\\wbafs2\r",
              250:  "\\wbafs4\r",
              125:  "\\wbafs8\r",
              100:  "\\wbafst\r"}

    ser.write(bytes(fs_map[int(fs)]))


def set_acc_fs(ser, fs):
    fs_map = {100: "\\wbaas1\r",
              50:  "\\wbaas2\r",
              40:  "\\wbaas3\r",
              25:  "\\wbafs4\r",
              20:  "\\wbaast\r"}

    ser.write(bytes(fs_map[int(fs)]))


def set_ecg_res(ser, res):
    res_map = {"0.20": "\\wbasg0\r",
              "1.00":  "\\wbasg1\r"}

    ser.write(bytes(res_map[str(res)]))

def set_acc_res(ser, res):
    res_map = {"0.25": "\\wbaar0\r",
              "1.00":  "\\wbaar1\r"}

    ser.write(bytes(res_map[str(res)]))

def set_ecg_hpf(ser, f):
    res_map = {1: "\\wbash0\r",
              10: "\\wbash1\r"}

    ser.write(bytes(res_map[int(f)]))
    

def start_measurement(ser, data_format):
    ser.write(bytes("\\wbaom" + str(data_format) + "\r"))
    res = ser.read(7).decode("UTF-8").strip()
    return(res)

def stop_measurement(ser, state):
    if state == "idle":
        command = "\\wbaoms\r"
    if state == "power_off":
        command = "\\wbaom0\r"

    for i in range(6):
        try:
            ser.write(bytes(command))
            ser.flushInput()
            res = ser.read(6).decode("UTF-8").strip()
            if (res == "wbaack"):
                break
        except UnicodeDecodeError:
            pass

def connect(port):
    return serial.Serial(port)

def get_packet_size(fs_ecg, fs_acc):
    k = str(fs_ecg) + "_" + str(fs_acc)

    packet_size_map = {"1000_40" : 70,
                       "500_100" : 94,
                       "500_20"  : 70,
                       "250_100" : 124,
                       "250_50"  : 94,
                       "250_20"  : 76,
                       "125_100" : 184,
                       "125_50"  : 124,
                       "125_25"  : 94,
                       "125_20"  : 88,
                       "100_100" : 214,
                       "100_20"  : 94}

    return(packet_size_map[k])

def get_packet_format(packetsize):
    N = (packetsize - 64) / 2
    
    packet_format = Struct('packet_format',
                        Bytes('start_1', 1),
                        Bytes('start_2', 1),
                        ULInt8('protocol_version_major'),
                        ULInt8('protocol_version_minor'),
                        BitStruct("packet_number",
                        BitField("pn", 24, swapped = True)),
                        BitStruct("flag",
                            BitField("battery_2", 1),
                            BitField("battery_1", 1), 
                            BitField("rr_error", 1), 
                            BitField("dummy_3", 1), 
                            BitField("adaptation_failed", 1), 
                            BitField("dummy_2", 1), 
                            BitField("dummy_1", 1), 
                            BitField("rr_in_packet", 1)),
                        Array(25, SLInt16("ECG")),
                        UBInt16("rr"),
                        UBInt32("rr_absolute"),
                        Array(N, SLInt16("acc")))
    return packet_format


