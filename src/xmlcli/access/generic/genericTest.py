#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

import os
import unittest
from .generic import CommonCliAccess


class GenericTestCase(unittest.TestCase):
  def test_initialize_interface(self):
    access_method_name = "generic"
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    self.base_object = CommonCliAccess(access_name=access_method_name, child_class_directory=self.current_directory)
    self.assertFalse("This Access Method is not meant to be used directly")


if __name__ == '__main__':
  unittest.main()
