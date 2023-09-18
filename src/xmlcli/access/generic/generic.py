#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = ["ashinde", "Gahan Saraiya"]

# Built-in imports
import os
import time
import binascii

# Custom imports
from ..base import base

__all__ = ["CommonCliAccess"]


class CommonCliAccess(base.BaseAccess):
  def __init__(self, access_name, child_class_directory):
    super(CommonCliAccess, self).__init__(access_name, child_class_directory=child_class_directory)
    self.level_dal = 0
    self.is_running = 0x00  # initialize IsRunning [bitmap] global variable to False for all bits
    self.thread = None
    self.access = None
    self._set_access()
    self.access.vp = 0
    self.access.base = 16 if not hasattr(self.access, 'base') else self.access.base
    thread_list = self.get_alive_threads()
    self.set_thread(thread_list[0])

  def _set_access(self):
    if not self.access:
      raise base.CliAccessException()

  @property
  @base.deprecated("Please use variable is_running")
  def IsRunning(self):
    # this method is for backward compatibility
    return self.is_running

  @property
  @base.deprecated("Please use variable is_running")
  def level_Dal(self):
    # this method is for backward compatibility
    return self.level_dal

  def halt_cpu(self, delay=0):
    time.sleep(delay)
    if not self.access.threads:
      raise base.CliAccessException(message="halt cpu: Really???", hints=["There are no existing CPU threads?", "Thanks, DAL."])
    if self.thread.cv.isrunning:
      try:
        self.access.halt()
      except Exception as e:
        pass

  def run_cpu(self):
    if not self.thread.cv.isrunning:
      self.access.go()
    return 0

  def initialize_interface(self):
    thread_list = self.get_alive_threads()
    self.set_thread(thread_list[0])
    self.is_running = (self.is_running & (~(0x1 << self.level_dal) & 0xFF)) + ((self.thread.cv.isrunning & 0x1) << self.level_dal)
    self.halt_cpu()
    self.level_dal = self.level_dal + 1
    return 0

  def close_interface(self):
    if (self.is_running >> (self.level_dal - 1)) & 0x1:
      self.run_cpu()
    else:
      self.halt_cpu()
    self.level_dal = self.level_dal - 1
    return 0

  def warm_reset(self):
    self.access.resettarget()

  def cold_reset(self):
    self.access.pulsepwrgood()

  def mem_block(self, address, size):
    result = self.thread.memblock(hex(address).rstrip('L') + 'p', size, 0)
    return binascii.unhexlify((hex(result)[2:]).zfill(size*2))[::-1]

  def mem_save(self, filename, address, size):
    # Due to a bug in IPC (Lauterbach) relative path names do not resolve correctly. To adjust for this, all files must be absolute
    if not os.path.isabs(filename):
      filename = os.path.abspath(filename)
    self.thread.memsave(filename, hex(address).rstrip('L')+'p', size, 1)

  def mem_read(self, address, size):
    return self.thread.mem(hex(address).rstrip('L') + 'p', size)

  def mem_write(self, address, size, value):
    self.thread.mem(hex(address).rstrip('L') + 'p', size, value)

  def load_data(self, filename, address):
    # Due to a bug in IPC (Lauterbach) relative path names do not resolve correctly. To adjust for this, all files must be absolute
    if not os.path.isabs(filename):
      filename = os.path.abspath(filename)
    self.thread.memload(filename, hex(address).rstrip('L') + 'p')

  def read_io(self, address, size):
    if size not in (1, 2, 4):
      raise base.CliOperationException(f"Invalid size to read from io port address: 0x{address:x}")
    if size == 1:
      return self.thread.port(address)
    if size == 2:
      return self.thread.wport(address)
    if size == 4:
      return self.thread.dport(address)

  def write_io(self, address, size, value):
    if size not in (1, 2, 4):
      raise base.CliOperationException(f"Invalid size to write from io port address: 0x{address:x}")
    if size == 1:
      self.thread.port(address, value)
    if size == 2:
      self.thread.wport(address, value)
    if size == 4:
      self.thread.dport(address, value)

  def trigger_smi(self, smi_value):
    self.halt_cpu()
    self.write_io(base.SMI_TRIGGER_PORT, 1, smi_value)
    self.run_cpu()

  def read_msr(self, Ap, address):
    return self.access.threads[Ap].msr(address)

  def write_msr(self, Ap, address, value):
    return self.access.threads[Ap].msr(address, value)

  def read_sm_base(self):
    self.halt_cpu()
    return self.thread.msr(0x171)

  def get_alive_threads(self):
    return list(filter(self.isThreadAlive, self.access.threads))

  def get_thread_by_number(self, thread_number, **kwargs):
    # [cli-2.0.0]: use case of condition???, turns out all will be eventually be True!!
    if 'socketNum' in kwargs:
      kwargs['domainNum'] = 0
      kwargs['packageNum'] = kwargs['socketNum']
      kwargs['dieNum'] = 0
    if 'domainNum' in kwargs:
      pobj = self.access.domains[kwargs['domainNum']]
      if 'packageNum' in kwargs:
        pobj = pobj.packages[kwargs['packageNum']]
        if 'dieNum' in kwargs:
          pobj = pobj.dies[kwargs['dieNum']]
          if 'coreNum' in kwargs:
            pobj = pobj.cores[kwargs['coreNum']]
      thread_list = pobj.getAllByType('thread')
    elif 'coreNum' in kwargs:
      thread_list = self.access.cores[kwargs['coreNum']].getAllByType('thread')
    else:
      thread_list = self.access.threads
    return thread_list[thread_number]

  def set_thread(self, thread):
    self.thread = thread

  @base.deprecated("Please use method get_alive_threads")
  def getAliveThreads(self):
    return self.get_alive_threads()

  @base.deprecated("Please use method get_thread_by_number")
  def getThreadByNumber(self, thread_number, **kwargs):
    return self.get_thread_by_number(thread_number, **kwargs)

  @base.deprecated("Please use method set_thread")
  def setThread(self, thread):
    return self.set_thread(thread)
