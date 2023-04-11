# -*- coding: utf-8 -*-
# Built-in imports
import os
import unittest
from random import SystemRandom


# Custom imports
from . import UnitTestHelper
from xmlcli.common import utils
from xmlcli.common import configurations

__author__ = "Gahan Saraiya"

settings = UnitTestHelper.settings
log = settings.logger
random = SystemRandom()


class UtilityTest(UnitTestHelper.UnitTestHelper):
  @settings.log_function_entry_and_exit
  def test_directory_utility(self):
    dir_location = utils.get_temp_folder()
    temp_folder = os.path.join(dir_location, "test_check")
    utils.make_directory(temp_folder)

    self.assertTrue(os.path.exists(temp_folder), "directory hierarchy could not be created")

    max_temp_files = 2 + random.getrandbits(4)
    for i in range(max_temp_files):
      file_path = os.path.join(temp_folder, "file_{}.txt".format(i))
      with open(file_path, "w") as f:
        f.write("random.....")

    self.assertEqual(len(os.listdir(temp_folder)), max_temp_files, "Total File Count does not match!!")

    deleted_files = utils.clean_directory(temp_folder)

    self.assertEqual(len(deleted_files), max_temp_files, "Files deleted does not match to the number of files created!!!")

  @settings.log_function_entry_and_exit
  def test_is_network_path(self):
    self.assertFalse(utils.is_network_path(utils.get_user_dir()),
                     "{} : considered as network path".format(utils.get_user_dir()))

    self.assertFalse(utils.is_network_path(utils.get_temp_folder()),
                     "{} : considered as network path".format(utils.get_temp_folder()))

    self.assertFalse(utils.is_network_path(utils.get_top_lvl_dir(utils.get_user_dir())),
                     "{} : considered as network path".format(utils.get_top_lvl_dir(utils.get_user_dir())))

  @settings.log_function_entry_and_exit
  def test_is_integer(self):
    for i in range(100 + random.getrandbits(10)):
      self.assertTrue(utils.is_integer(10 ** 3 + random.getrandbits(100)))

    self.assertFalse(utils.is_integer("0x15"))
    self.assertFalse(utils.is_integer("random value"))
    self.assertFalse(utils.is_integer(os.path))

  @settings.log_function_entry_and_exit
  def test_get_integer_value(self):
    self.assertEqual(utils.get_integer_value(50), 50)
    self.assertEqual(utils.get_integer_value(50.5), 50)
    self.assertEqual(utils.get_integer_value(10 ** 30), 10 ** 30)
    self.assertEqual(utils.get_integer_value(hex(10 ** 30)), 0xc9f2c9cd04674edea40000000)
    self.assertEqual(utils.get_integer_value(str(10 ** 30), base=10), 10 ** 30)
    self.assertEqual(utils.get_integer_value(str(0xa15), base=10), 0xa15)
    self.assertEqual(utils.get_integer_value("0xa15", base=16), 0xa15)
    self.assertEqual(utils.get_integer_value(50.50), 50)
    self.assertEqual(utils.get_integer_value(oct(32)), 32)
    self.assertEqual(utils.get_integer_value(bin(32)), 32)
    self.assertEqual(utils.get_integer_value(0x20), 32)
    self.assertEqual(utils.get_integer_value(hex(32)), 32)
    self.assertEqual(utils.get_integer_value("0x20"), 32)
    self.assertEqual(utils.get_integer_value("20"), 32)
    self.assertEqual(utils.get_integer_value("20", base=16), 32)
    self.assertEqual(utils.get_integer_value("20", base=10), 20)

    self.assertNotEqual(utils.get_integer_value("32"), 20)
    self.assertNotEqual(utils.get_integer_value("32"), 0)
    self.assertNotEqual(utils.get_integer_value("0x32"), 0)

  @settings.log_function_entry_and_exit
  def test_is_string(self):
    self.assertTrue(utils.is_string("The value is awesome"))
    self.assertTrue(utils.is_string(r"The value is awesome"))
    self.assertTrue(utils.is_string(u"The value is awesome"))
    self.assertFalse(utils.is_string(b"The value is awesome"))

  @settings.log_function_entry_and_exit
  def test_get_string(self):
    self.assertEqual(utils.get_string("The value"), "The value")
    self.assertEqual(utils.get_string(b"The value"), "The value")
    self.assertEqual(utils.get_string("The value".encode('utf-8')), "The value")
    self.assertEqual(utils.get_string("The value".encode(configurations.ENCODING)), "The value")

  @settings.log_function_entry_and_exit
  def test_get_absolute_sizeof(self):
    self.assertEqual(utils.get_absolute_sizeof(2 ** 8 - 1), 1, "size of - {} must be 1 byte!".format(2 ** 8 - 1))

    self.assertEqual(utils.get_absolute_sizeof(0), 1, "size of integer - {} must be 1 byte!".format(0))

    self.assertEqual(utils.get_absolute_sizeof(1), 1, "size of integer - {} must be 1 byte!".format(1))

    self.assertEqual(utils.get_absolute_sizeof((2 ** (8 * 15)) - 1), 15, "size of integer - {} must be 15 bytes!".format((2 ** (8 * 15)) - 1))

    for i in range(10, 50):
      val = 2**(8*i) - 1
      self.assertEqual(utils.get_absolute_sizeof(val), i, "size of integer - {} must be {} bytes!!".format(val, i))

    self.assertEqual(utils.get_absolute_sizeof("value"), len("value"), "String size mismatch!!!")

  @settings.log_function_entry_and_exit
  def test_guid_lis_to_str(self):
    guid1 = "000455a7-999b-01ea-00b25ce0c5a7e706"
    self.assertEqual(utils.guid_lis_to_str(guid1.split("-")), guid1)

    guid2 = "000455a7-999b-01ea-00-b2-5c-e0-c5-a7-e7-06"
    self.assertEqual(utils.guid_lis_to_str(guid2.split("-")), guid2)

  @settings.log_function_entry_and_exit
  def test_guid_formatter(self):
    import uuid
    for i in range(100 + random.getrandbits(10)):
      guid1 = str(uuid.uuid1())
      self.assertEqual(utils.guid_formatter(guid1).replace('-', ''), guid1.replace('-', ''))

    guid2 = "03b455a7-999b-11ea-81b2-5ce0c5a7e7f6"
    self.assertEqual(utils.guid_formatter(guid2), "03b455a7-999b-11ea-81b25ce0c5a7e7f6")
    self.assertEqual(utils.guid_formatter(guid2, string_format="xmlcli"), "0x03b455a7-0x999b-0x11ea-0x81-0xb2-0x5c-0xe0-0xc5-0xa7-0xe7-0xf6")

    guid3 = "000455a7-999b-11ea-00b25ce0c5a7e706"
    self.assertEqual(utils.guid_formatter(guid3), "000455a7-999b-11ea-00b25ce0c5a7e706")
    self.assertEqual(utils.guid_formatter(guid3, string_format="xmlcli"), "0x000455a7-0x999b-0x11ea-0x00-0xb2-0x5c-0xe0-0xc5-0xa7-0xe7-0x06")

    guid4 = "000455a7-999b-01ea-00-b2-5c-e0-c5-a7-e7-06"
    self.assertEqual(utils.guid_formatter(guid4), "000455a7-999b-01ea-00b25ce0c5a7e706")
    self.assertEqual(utils.guid_formatter(guid4, string_format="xmlcli"), "0x000455a7-0x999b-0x01ea-0x00-0xb2-0x5c-0xe0-0xc5-0xa7-0xe7-0x06")

    self.assertEqual(utils.guid_formatter("00000000-0000-0000-0000000000000000"), "00000000-0000-0000-0000000000000000")
    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x0000000000000000"), "00000000-0000-0000-0000000000000000")
    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x0000000000000000"), "00000000-0000-0000-0000000000000000")

    self.assertEqual(utils.guid_formatter("00000000-0000-0000-0000-000000000000"), "00000000-0000-0000-0000000000000000")
    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x0000-0x000000000000"), "00000000-0000-0000-0000000000000000")

    self.assertEqual(utils.guid_formatter("00000000-0000-0000-0000-000000000000", string_format="xmlcli"),
                     "0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00")
    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x0000-0x000000000000", string_format="xmlcli"),
                     "0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00")

    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00"), "00000000-0000-0000-0000000000000000")
    self.assertEqual(utils.guid_formatter("0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00", string_format="xmlcli"),
                     "0x00000000-0x0000-0x0000-0x00-0x00-0x00-0x00-0x00-0x00-0x00-0x00")

  @settings.log_function_entry_and_exit
  def test_create_table(self):
    # variable data length
    data_1 = [1, 2, 3, 7, 8, 9, 10]
    data_2 = [[1, 2, 3], [7, 8, 9, 10], [11, 12, 13], [1, 2, 3, 4, 5], [11, 12, 13]]
    header = ['value1', 'value2', 'value3', 'value4', 'value5', 'value6']
    table_writer = utils.Table()

    # Calling create table without header and 1D data and treat_number = 'hex'
    self.assertEqual(table_writer.create_table(header=0, data=data_1, width=0, treat_number='hex'),
                     "====================================="
                     "\n|0x1 |0x2 |0x3 |0x7 |0x8 |0x9 | 0xa |"
                     "\n=====================================\n")

    # Calling create table without header and 1D data and treat_number = 'int'
    self.assertEqual(table_writer.create_table(header=0, data=data_1, width=0, treat_number='int'),
                     "====================================="
                     "\n| 1  | 2  | 3  | 7  | 8  | 9  | 10  |"
                     "\n=====================================\n")

    # Calling create table without header and 2D data and treat_number = 'hex'
    self.assertEqual(table_writer.create_table(header=0, data=data_2, width=0, treat_number='hex'),
                     "=============================="
                     "\n| 0x1 | 0x2 | 0x3 |     |    |"
                     "\n| 0x7 | 0x8 | 0x9 | 0xa |    |"
                     "\n| 0xb | 0xc | 0xd |     |    |"
                     "\n| 0x1 | 0x2 | 0x3 | 0x4 |0x5 |"
                     "\n| 0xb | 0xc | 0xd |     |    |"
                     "\n==============================\n")

    # Calling create table without header and 2D data and treat_number = 'int'
    self.assertEqual(table_writer.create_table(header=0, data=data_2, width=0, treat_number='int'),
                     "=============================="
                     "\n|  1  |  2  |  3  |     |    |"
                     "\n|  7  |  8  |  9  | 10  |    |"
                     "\n| 11  | 12  | 13  |     |    |"
                     "\n|  1  |  2  |  3  |  4  | 5  |"
                     "\n| 11  | 12  | 13  |     |    |"
                     "\n==============================\n")

    # Calling create table with header and 1D data and treat_number = 'hex'
    self.assertEqual(table_writer.create_table(header=header, data=data_1, width=0, treat_number='hex'),
                     "==================================================================="
                     "\n| value1  | value2  | value3  | value4  | value5  | value6  |     |"
                     "\n==================================================================="
                     "\n|   0x1   |   0x2   |   0x3   |   0x7   |   0x8   |   0x9   | 0xa "
                     "|\n===================================================================\n")

    # Calling create table with header and 1D data and treat_number = 'int'
    self.assertEqual(table_writer.create_table(header=header, data=data_1, width=0, treat_number='int'),
                     "==================================================================="
                     "\n| value1  | value2  | value3  | value4  | value5  | value6  |     |"
                     "\n==================================================================="
                     "\n|    1    |    2    |    3    |    7    |    8    |    9    | 10  |"
                     "\n===================================================================\n")

    # Calling create table with header and 2D data and treat_number = 'hex'
    self.assertEqual(table_writer.create_table(header=header, data=data_2, width=0, treat_number='hex'),
                     "================================================================="
                     "\n| value1  | value2  | value3  | value4  | value5  | value6  |   |"
                     "\n================================================================="
                     "\n|   0x1   |   0x2   |   0x3   |         |         |         |   |"
                     "\n|   0x7   |   0x8   |   0x9   |   0xa   |         |         |   |"
                     "\n|   0xb   |   0xc   |   0xd   |         |         |         |   |"
                     "\n|   0x1   |   0x2   |   0x3   |   0x4   |   0x5   |         |   |"
                     "\n|   0xb   |   0xc   |   0xd   |         |         |         |   |"
                     "\n=================================================================\n")

    # Calling create table with header and 2D data and treat_number = 'hex'
    self.assertEqual(table_writer.create_table(header=header, data=data_2, width=0, treat_number='int'),
                     "================================================================="
                     "\n| value1  | value2  | value3  | value4  | value5  | value6  |   |"
                     "\n================================================================="
                     "\n| value1  | value2  | value3  | value4  | value5  | value6  |   |"
                     "\n|    1    |    2    |    3    |         |         |         |   |"
                     "\n|    7    |    8    |    9    |   10    |         |         |   |"
                     "\n|   11    |   12    |   13    |         |         |         |   |"
                     "\n|    1    |    2    |    3    |    4    |    5    |         |   |"
                     "\n|   11    |   12    |   13    |         |         |         |   |"
                     "\n=================================================================\n")

    # Calling create table with no data and no header
    self.assertEqual(table_writer.create_table(header=0, data=0, width=0, treat_number='hex'), "")

    # Calling create table with both data and header same are of length
    header_list = ['HeaderVersion', 'ModuleSubType', 'ChipsetID', 'Flags', 'ModuleVendor', 'dd.mm.yyyy', 'Size',
                   'Version']
    data_in_list = ['0x30000', '0x1', '0xb00c', '0x8000', '0x8086', '22-10-2021', '0x2f000', '1.18.5']
    self.assertEqual(table_writer.create_table(header=header_list, data=data_in_list, width=0, treat_number='hex'),
                     "=============================================================================================================="
                     "\n| HeaderVersion  | ModuleSubType  | ChipsetID  |  Flags  | ModuleVendor  | dd.mm.yyyy  |   Size   | Version  |"
                     "\n=============================================================================================================="
                     "\n|    0x30000     |      0x1       |   0xb00c   | 0x8000  |    0x8086     | 22-10-2021  | 0x2f000  |  1.18.5  |"
                     "\n==============================================================================================================\n")

    # Calling create table with header , data and width and treat_number='hex'
    Header = ['Reg No', 'Name', 'Address', 'Marks']
    Data = [[124, 'Pavan', 'Banglore', 84], [12, 'Abhinav', 'Mysore', 95], [45, 'Kumar singh', 'Delhi', 97]]
    self.assertEqual(table_writer.create_table(header=Header, data=Data, width=[8, 15, 15, 6], treat_number='hex'),
                     "================================================="
                     "\n| Reg No |     Name      |    Address    |Marks |"
                     "\n================================================="
                     "\n|  0x7c  |     Pavan     |   Banglore    | 0x54 |"
                     "\n|  0xc   |    Abhinav    |    Mysore     | 0x5f |"
                     "\n|  0x2d  |  Kumar singh  |     Delhi     | 0x61 |"
                     "\n=================================================\n")

    # Calling create table with header , data and width and treat_number='hex', here width less than actual width of
    # the column
    Header = ['Reg No', 'Name', 'Address', 'Marks', 'Grade']
    Data = [[124, 'Pavan', 'Banglore', 84, 'A'], [12, 'Abhinav', 'Mysore', 95, 'A+'],
            [45, 'Kumar singh', 'Delhi', 97, 'A+']]
    self.assertEqual(table_writer.create_table(header=Header, data=Data, width=[5, 6, 7, 6, 3], treat_number='hex'),
                     "================================="
                     "\n|Reg N| Name |Address|Marks |Gra|"
                     "\n================================="
                     "\n|0x7c |Pavan |Banglor| 0x54 | A |"
                     "\n| 0xc |Abhina|Mysore | 0x5f |A+ |"
                     "\n|0x2d |Kumar | Delhi | 0x61 |A+ |"
                     "\n=================================\n")


if __name__ == "__main__":
  pass
