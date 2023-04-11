#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

import unittest
from .winrwe import WinRweAccess


class WinRweTestCase(unittest.TestCase):
  def test_initialize_interface(self):
    access_method_name = "winrwe"
    self.base_object = WinRweAccess(access_name=access_method_name)
    self.assertEqual(self.base_object.interface, access_method_name)
    self.assertEqual(self.base_object.interface, self.base_object.InterfaceType)


if __name__ == '__main__':
  unittest.main()
