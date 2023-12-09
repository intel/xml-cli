#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Jayaprakash Nevara"

# Built-in imports
import os
import edk2
from ctypes import create_string_buffer

# Custom imports
from ..base import base

__all__ = ["UefiAccess"]

_RESET_IO_PORT = 0xCF9
_SMI_IO_PORT = 0xB2


class UefiAccess(base.BaseAccess):
    def __init__(self, access_name="uefi"):
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        super(UefiAccess, self).__init__(access_name=access_name, child_class_directory=self.current_directory)

    def halt_cpu(self, delay=0):
        return 0

    def run_cpu(self):
        return 0

    def initialize_interface(self):
        return 0

    def close_interface(self):
        return 0

    def warm_reset(self):
        data = 0x06
        edk2.writeio(_RESET_IO_PORT, 1, data)

    def cold_reset(self):
        data = 0x0E
        edk2.writeio(_RESET_IO_PORT, 1, data)

    def mem_block(self, address, size):
        address_low32 = address & 0xFFFF_FFFF
        address_high32 = (address >> 32) & 0xFFFF_FFFF
        data = edk2.readmem(address_low32, address_high32, size)
        return data

    def mem_save(self, filename, address, size):
        temp_buffer = self.mem_block(address, size)
        with open(filename, 'wb') as out_file:  # opening for writing
            out_file.write(temp_buffer)

    def mem_read(self, address, size):
        address_low32 = address & 0xFFFF_FFFF
        address_high32 = (address >> 32) & 0xFFFF_FFFF
        data_obj = edk2.readmem(address_low32, address_high32, size)
        if size == 1:
            data = data_obj[0]
        elif size == 2:
            data = data_obj[0] | data_obj[1] << 8
        elif size == 4:
            data = data_obj[0] | data_obj[1] << 8 | data_obj[2] << 16 | data_obj[3] << 24
        else:
            data = data_obj[0] | data_obj[1] << 8 | data_obj[2] << 16 | data_obj[3] << 24 | data_obj[4] << 32 | data_obj[5] << 40 | data_obj[6] << 48 | data_obj[7] << 56
        return data

    def mem_write(self, address, size, value):
        # writes 32 bit value to the given address
        address_low32 = address & 0xFFFF_FFFF
        address_high32 = (address >> 32) & 0xFFFF_FFFF
        edk2.writemem_dword(address_low32, address_high32, value)

    def load_data(self, filename, address):
        address_low32 = address & 0xFFFF_FFFF
        address_high32 = (address >> 32) & 0xFFFF_FFFF
        
        with open(filename, 'rb') as in_file:  # opening for [r]eading as [b]inary
            data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)
        size = len(data)
        buf = create_string_buffer(bytes(data))
        edk2.writemem(address_low32, address_high32, buf)

    def read_io(self, address, size):
        # size = 1,2 or 4 only supported
        data = edk2.readio(address, size)
        return data

    def write_io(self, address, size, value):
        edk2.writeio(address, size, value)
        return 0

    def trigger_smi(self, smi_value):
        edk2.writeio(_SMI_IO_PORT, 1, smi_value)

    def read_msr(self, Ap, address):
        # input parameter Ap is not used currently api executes on BSP
        data = edk2.rdmsr(address)
        return (((data[1] & 0xFFFFFFFF) << 32) | (data[0] & 0xFFFFFFFF))

    def write_msr(self, Ap, address, value):
        # input parameter Ap is not used currently api executes on BSP
        low_content = (value & 0xFFFFFFFF)
        high_content = (value >> 32) & 0xFFFFFFFF
        edk2.wrmsr(address, low_content, high_content)
        return 0

    def read_sm_base(self):
        return 0
