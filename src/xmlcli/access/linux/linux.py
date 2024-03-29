#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import mmap
import ctypes
import binascii

# Custom imports
from ..base import base

__all__ = ["LinuxAccess"]


class LinuxAccess(base.BaseAccess):
  def __init__(self, access_name="linux"):
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    super(LinuxAccess, self).__init__(access_name=access_name, child_class_directory=self.current_directory)
    self.memory_file = self.config.get(access_name.upper(), "memory_file")
    self.map_mask = mmap.PAGESIZE - 1
    # Read Port library
    self.port_lib_location = os.path.join(self.current_directory, self.config.get(access_name.upper(), "lib_port"))
    self.port_library = ctypes.CDLL(self.port_lib_location)
    # Read Port configuration
    self._read_port = self.port_library.read_port
    self._read_port.argtypes = (ctypes.c_uint16, ctypes.c_uint8)
    self._read_port.restype = (ctypes.POINTER(ctypes.c_uint8))
    # Write port configuration
    self._write_port = self.port_library.write_port
    self._write_port.argtypes = (ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint32)
    self.external_mem = self.config.getboolean(access_name.upper(), "external_mem")
    if self.external_mem:
      self.lib_mem = os.path.join(self.current_directory, self.config.get(access_name.upper(), "lib_mem"))
      self.mem_library = ctypes.CDLL(self.lib_mem)
      # Read Memory configuration
      self._read_mem = self.mem_library.mem_read
      self._read_mem.argtypes = (ctypes.c_ulong, ctypes.c_void_p, ctypes.c_size_t)
      self._read_mem.restype = ctypes.c_int
      # Write Memory configuration
      self._write_mem = self.mem_library.mem_write
      self._write_mem.argtypes = (ctypes.c_ulong, ctypes.c_void_p, ctypes.c_size_t)
      self._write_mem.restype = ctypes.c_int

  def halt_cpu(self, delay=0):
    return 0

  def run_cpu(self):
    return 0

  def initialize_interface(self):
    return 0

  def close_interface(self):
    return 0

  def read_port(self, port, size):
    read_val = 0
    ret = self._read_port(port, size)
    if ret:
      for i in range(0, size):
        read_val += ret[i] << 8 * (i)
    return read_val

  def io(self, port, size, val=None):
    if val is None:
      read_val = self.read_port(port, size)
      return int(read_val)
    else:
      ret = self._write_port(port, size, val)
      return ret

  def read_memory_bytes(self, address, size):
    mem_file_obj = os.open(self.memory_file, os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(mem_file_obj, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ, offset=address & ~self.map_mask)
    data = None
    try:
      mem.seek(address & self.map_mask)
      data = mem.read(size)
      mem.close()
      os.close(mem_file_obj)
      return data
    except Exception as e:  # catch any kind of exception and close /dev/mem file
      mem.close()
      os.close(mem_file_obj)
    if data is None:
      raise Exception("Unable to read memory on the platform")
    return data

  def read_memory(self, address, size):
    if self.external_mem:
      dest = (ctypes.c_ubyte * size)()
      self._read_mem(address, ctypes.cast(dest, ctypes.c_void_p), size)
      result = 0
      ctypes.cast(dest, ctypes.c_char_p)
      for i in range(0, size):
        result += dest[i] << 8 * i
    else:
      result = self.read_memory_bytes(address, size)
      result = int.from_bytes(result, byteorder="little", signed=False)
    return result

  def write_memory_bytes(self, address, data, size):
    mem_file_obj = os.open(self.memory_file, os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(mem_file_obj, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ, offset=address & ~self.map_mask)
    bytes_written = 0
    try:
      data_dump = data if isinstance(data, bytes) else self.int_to_byte(data, size)
      if data_dump:
        mem.seek(address & self.map_mask)
        bytes_written = mem.write(data_dump)
      mem.close()
      os.close(mem_file_obj)
      return data
    except Exception as e:  # catch any kind of exception and close /dev/mem file
      mem.close()
      os.close(mem_file_obj)
    if bytes_written == 0:
      raise Exception("Unable to write memory on the platform")
    return bytes_written

  def write_memory(self, address, data, size):
    if self.external_mem:
      if isinstance(data, int):
        data = ctypes.c_ulonglong(data)
        _data = ctypes.byref(data)
      else:
        _data = data
      bytes_written = self._write_mem(address, _data, size)
    else:
      bytes_written = self.write_memory_bytes(address, data, size)
    return bytes_written

  def mem(self, address, size, val=None):
    if val is None:
      read_val = self.read_memory(address, size)
      return int(read_val)
    else:
      ret = self.write_memory(address, val, size)
      return ret

  def read_memory_block(self, address, size, val=None):
    if val is None:
      read_val = self.read_memory(address, size)
      return binascii.unhexlify(hex(read_val)[2:].strip('L').zfill(size * 2))[::-1]
    else:
      ret = self.write_memory(address, val, size)
      return ret

  def warm_reset(self):
    self.io(0xCF9, 1, 0x06)

  def cold_reset(self):
    self.io(0xCF9, 1, 0x0E)

  def mem_block(self, address, size):
    end_address = address + size
    temp_address = address & 0xFFFFF000
    result1 = []
    if (end_address - temp_address) <= 0x1000:
      result = self.read_memory_block(address, size)
      result1.extend(result)
    else:
      first_end_page_address = (address + 0xFFF) & 0xFFFFF000
      if first_end_page_address > address:
        result = self.read_memory_block(address, (first_end_page_address - address))
        result1.extend(result)
      block_count = 0
      block_size = (end_address - first_end_page_address)
      block_number = int(block_size/0x1000)
      for block_count in range(0, block_number):
        result = self.read_memory_block(first_end_page_address + (block_count * 0x1000), 0x1000)
        result1.extend(result)
      if block_number != 0:
        block_count = block_count+1
      if block_size % 0x1000:
        result = self.read_memory_block(first_end_page_address + (block_count * 0x1000), (block_size % 0x1000))
        result1.extend(result)
    return bytearray(result1)

  def mem_save(self, filename, address, size):
    temp_buffer = self.mem_block(address, size)
    with open(filename, 'wb') as out_file:  # opening for writing
      out_file.write(temp_buffer)

  def mem_read(self, address, size):
    return self.mem(address, size)  # list of size entries of 1 Byte

  def mem_write(self, address, size, value):
    self.mem(address, size, value)  # list of size entries of 1 Byte

  def load_data(self, filename, address):
    with open(filename, 'rb') as in_file:  # opening for [r]eading as [b]inary
      data = in_file.read()  # if you only wanted to read 512 bytes, do .read(512)
    size = len(data)
    self.read_memory_block(address, size, data)  # list of size entries of 1 Byte

  def read_io(self, address, size):
    return self.io(address, size)

  def write_io(self, address, size, value):
    self.io(address, size, value)

  def trigger_smi(self, smi_value):
    self.io(0xB2, 1, smi_value)

  def read_msr(self, Ap, address):
    return 0

  def write_msr(self, Ap, address, value):
    return 0

  def read_sm_base(self):
    return 0
