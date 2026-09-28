# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import binascii
import subprocess

# Custom imports
from ..base import base
# Conditional Imports

__all__ = ["WinRweAccess"]


class WinRweAccess(base.BaseAccess):
  def __init__(self, access_name="winrwe"):
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    super(WinRweAccess, self).__init__(access_name=access_name, child_class_directory=self.current_directory)
    self.rw_executable = self.config.get(access_name.upper(), "RW_EXE")
    self.temp_data_bin = self.config.get(access_name.upper(), "TEMP_DATA_BIN")
    self.result_text = self.config.get(access_name.upper(), "RESULT_TEXT")

  def halt_cpu(self, delay=0):
    return 0

  def run_cpu(self):
    return 0

  def initialize_interface(self):
    return 0

  def close_interface(self):
    return 0

  def warm_reset(self):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=O 0xCF9 0x06; RwExit"], shell=False)

  def cold_reset(self):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=O 0xCF9 0x0E; RwExit"], shell=False)

  def mem_block(self, address, size):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=SAVE {} Memory 0x{:x} 0x{:x}; RwExit".format(self.temp_data_bin, address, size)], shell=False)
    with open(self.temp_data_bin, 'rb') as f:
      data_buffer = f.read()
    return data_buffer

  def mem_save(self, filename, address, size):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=SAVE {} Memory 0x{:x} 0x{:x}; RwExit".format(filename, address, size)], shell=False)

  def mem_read(self, address, size):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=SAVE {} Memory 0x{:x} 0x{:x}; RwExit".format(self.temp_data_bin, address, size)], shell=False)
    with open(self.temp_data_bin, 'rb') as f:
      data_buffer = f.read()
    return int(binascii.hexlify(data_buffer[0:size][::-1]), 16)

  def mem_write(self, address, size, value):
    if size in (1, 2, 4, 8):
      word_size = "" if size == 1 else 8*size
      if size != 8 :
        cmd = "W{} 0x{:x} 0x{:x}".format(word_size, address, value)
      else:
        cmd = "W{} 0x{:x} 0x{:x}; W32 0x{:x} 0x{:x}".format(32, address, (value & 0xFFFFFFFF), (address + 4), (value >> 32))
      subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command={}; RwExit".format(cmd)], shell=False)

  def load_data(self, filename, address):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=LOAD {} Memory 0x{:x}; RwExit".format(filename, address)], shell=False)

  def read_io(self, address, size):
    if size in (1, 2, 4):
      cmd = "I{} 0x{:x}".format("" if size == 1 else 8*size, address)
      subprocess.run([self.rw_executable, "/Nologo", "/Min", "/LogFile={}".format(self.result_text), "/Command={}; RwExit".format(cmd)], shell=False)
    with open(self.result_text, 'r') as f:
      result = f.read()
    temp_str = result.split('=')
    if temp_str[0].strip() == 'In Port 0x{:x}'.format(address):
      return int(temp_str[1].strip(), 16)
    else:
      return 0

  def write_io(self, address, size, value):
    if size in (1, 2, 4):
      cmd = "O{} 0x{:x} 0x{:x}".format("" if size == 1 else 8*size, address, value)
      subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command={}; RwExit".format(cmd)], shell=False)

  def trigger_smi(self, smi_value):
    subprocess.run([self.rw_executable, "/Nologo", "/Min", "/Command=O 0x{:x} 0x{:x}; RwExit".format(0xB2, smi_value)], shell=False)

  def read_msr(self, Ap, address):
    return 0

  def write_msr(self, Ap, address, value):
    return 0

  def read_sm_base(self):
    return 0
