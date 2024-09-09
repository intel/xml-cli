import os
import binascii
import configparser

SMI_TRIGGER_PORT = 0xB2
DEPRECATION_WARNINGS = False


class BaseAccess(object):
    def __init__(self, access_name, child_class_directory):
        self.InterfaceType = access_name
        self.interface = access_name
        self.config = configparser.RawConfigParser(allow_no_value=True)
        self.config_file = os.path.join(child_class_directory, "{}.ini".format(access_name))
        self.read_config()

    @staticmethod
    def byte_to_int(data):
        return int(binascii.hexlify(bytearray(data)[::-1]), 16)

    @staticmethod
    def int_to_byte(data, size):
        data_dump = data.to_bytes(size, byteorder="little", signed=False)
        return data_dump

    def read_config(self):
        self.config.read(self.config_file)
