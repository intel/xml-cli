#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os

# Custom imports
from ..base import base

__all__ = ["StubAccess"]


class StubAccess(base.BaseAccess):
  def __init__(self, access_name="stub"):
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    super(StubAccess, self).__init__(access_name=access_name, child_class_directory=self.current_directory)

  def halt_cpu(self, delay=0):
    return 0

  def run_cpu(self):
    return 0

  def initialize_interface(self):
    return 0

  def close_interface(self):
    return 0

  def warm_reset(self):
    return 0

  def cold_reset(self):
    return 0

  def mem_block(self, address, size):
    return 0

  def mem_save(self, filename, address, size):
    return 0

  def mem_read(self, address, size):
    return 0

  def mem_write(self, address, size, value):
    return 0

  def load_data(self, filename, address):
    return 0

  def read_io(self, address, size):
    return 0

  def write_io(self, address, size, value):
    return 0

  def trigger_smi(self, smi_value):
    return 0

  def read_msr(self, Ap, address):
    return 0

  def write_msr(self, Ap, address, value):
    return 0

  def read_sm_base(self):
    return 0
