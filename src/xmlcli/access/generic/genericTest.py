#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

import unittest
from .generic import CommonCliAccess


class GenericTestCase(unittest.TestCase):
  def test_initialize_interface(self):
    access_method_name = "generic"
    self.assertFalse("This Access Method is not meant to be used directly")


if __name__ == '__main__':
  unittest.main()
