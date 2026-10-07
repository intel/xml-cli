# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import shutil
import binascii
import subprocess

# Custom imports
from ..base import base
# Conditional Imports

__all__ = ["WinRweAccess"]

# RW.exe parses its own /Command= mini-language: `;` separates statements and whitespace separates tokens.
_RW_COMMAND_UNSAFE_CHARS = ";\"' \t\r\n"


class WinRweAccess(base.BaseAccess):
  def __init__(self, access_name="winrwe"):
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    super(WinRweAccess, self).__init__(access_name=access_name, child_class_directory=self.current_directory)
    self.rw_executable = self.config.get(access_name.upper(), "RW_EXE")
    self.temp_data_bin = self._validate_rw_path(self.config.get(access_name.upper(), "TEMP_DATA_BIN"), "TEMP_DATA_BIN")
    self.result_text = self._validate_rw_path(self.config.get(access_name.upper(), "RESULT_TEXT"), "RESULT_TEXT")

  @staticmethod
  def _validate_rw_path(path, setting_name):
    if not path or any(character in path for character in _RW_COMMAND_UNSAFE_CHARS):
      raise ValueError("{} must be a non-empty path without whitespace, quotes or ';' (got {!r})".format(setting_name, path))
    return path

  def _run_rw(self, command, log_file=None):
    arguments = [self.rw_executable, "/Nologo", "/Min"]
    if log_file:
      arguments.append("/LogFile={}".format(log_file))
    arguments.append("/Command={}; RwExit".format(command))
    return subprocess.run(arguments, shell=False)  # nosec B603 - fixed argv, no shell, no caller-controlled tokens

  def halt_cpu(self, delay=0):
    return 0

  def run_cpu(self):
    return 0

  def initialize_interface(self):
    return 0

  def close_interface(self):
    return 0

  def warm_reset(self):
    self._run_rw("O 0xCF9 0x06")

  def cold_reset(self):
    self._run_rw("O 0xCF9 0x0E")

  def mem_block(self, address, size):
    self._run_rw("SAVE {} Memory 0x{:x} 0x{:x}".format(self.temp_data_bin, address, size))
    with open(self.temp_data_bin, 'rb') as f:
      data_buffer = f.read()
    return data_buffer

  def mem_save(self, filename, address, size):
    # RW only ever writes to the internal temp path, so `filename` never reaches its command parser.
    self._run_rw("SAVE {} Memory 0x{:x} 0x{:x}".format(self.temp_data_bin, address, size))
    shutil.copyfile(self.temp_data_bin, filename)

  def mem_read(self, address, size):
    self._run_rw("SAVE {} Memory 0x{:x} 0x{:x}".format(self.temp_data_bin, address, size))
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
      self._run_rw(cmd)

  def load_data(self, filename, address):
    # Stage the caller's file through the internal temp path so `filename` never reaches RW's command parser.
    shutil.copyfile(filename, self.temp_data_bin)
    self._run_rw("LOAD {} Memory 0x{:x}".format(self.temp_data_bin, address))

  def read_io(self, address, size):
    if size in (1, 2, 4):
      cmd = "I{} 0x{:x}".format("" if size == 1 else 8*size, address)
      self._run_rw(cmd, log_file=self.result_text)
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
      self._run_rw(cmd)

  def trigger_smi(self, smi_value):
    self._run_rw("O 0x{:x} 0x{:x}".format(0xB2, smi_value))

  def read_msr(self, Ap, address):
    return 0

  def write_msr(self, Ap, address, value):
    return 0

  def read_sm_base(self):
    return 0
