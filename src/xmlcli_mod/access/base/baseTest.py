# coding=utf-8
"""
As Base Test method demonstrating contributors guidelines
and example to write test cases.
"""
import os
import unittest
from .base import BaseAccess


class BaseTestCase(unittest.TestCase):
  def setUp(self):
    """Initialize interface setup for usage in test methods

    :return:
    """
    access_method_name = "base"
    self.current_directory = os.path.dirname(os.path.abspath(__file__))
    self.base_object = BaseAccess(access_name=access_method_name, child_class_directory=self.current_directory)
    self.assertEqual(self.base_object.interface, access_method_name)
    self.assertEqual(self.base_object.interface, self.base_object.InterfaceType)

  def test_mem_read(self):
    result = self.base_object.mem_read(0xFFFFFFC0, 4)
    self.assertGreaterEqual(result, 0xFF000000, "Read value not as expected")
    value = self.base_object.mem_read(result, 8)
    self.assertEqual(value, int.from_bytes(bytes('_FIT_   '.encode()), "little"), "Read Signature mismatch")

  def test_mem_write(self):
    write_val = 0xff
    result = self.base_object.mem_write(0x43760000, 1, write_val)
    read_val = self.base_object.mem_read(0x43760000, 1)
    self.assertEqual(read_val, write_val, "Write Value does not match!!")

  def test_io_operation(self):
    write_val = 0xf1
    self.base_object.write_io(0x70, 1, write_val)
    read_val = self.base_object.read_io(0x70, 1)
    self.assertEqual(read_val, write_val, "Write Value does not match!!")


if __name__ == '__main__':
  unittest.main()
