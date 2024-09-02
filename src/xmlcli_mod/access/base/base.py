import os
import binascii
import configparser

SMI_TRIGGER_PORT = 0xB2
DEPRECATION_WARNINGS = False


class CliAccessException(Exception):
    def __init__(self, message="CliAccess is a virtual class!", error_code=None, *args, **kwargs):
        hints = "\n".join(kwargs.get("hints", []))
        self.message = "[CliAccessExceptionError: {}] {}".format(error_code, message) if error_code else "[CliAccessException] {}".format(message)
        if hints:
            self.message += "\nHint: " + hints
        super(CliAccessException, self).__init__(self.message)


class CliOperationException(CliAccessException):
    def __init__(self, message="Operation Error!", error_code=None, *args, **kwargs):
        hints = "\n".join(kwargs.get("hints", []))
        self.message = "[CliOperationError: {}] {}".format(error_code, message) if error_code else "[CliAccessException] {}".format( message)
        if hints:
            self.message += "\nHint: " + hints
        super(CliOperationException, self).__init__(self.message)


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
        try:
            self.config.read(self.config_file)
        except AttributeError:
            # EFI Shell may encounter at this flow while reading config file as .read method uses os.popen which is not available at EFI Python
            with open(self.config_file, "r") as config_file:
                self.config._read(config_file, self.config_file)

    def halt_cpu(self, delay):
        raise CliAccessException()

    def run_cpu(self):
        raise CliAccessException()

    def initialize_interface(self):
        raise CliAccessException()

    def close_interface(self):
        raise CliAccessException()

    def warm_reset(self):
        raise CliAccessException()

    def cold_reset(self):
        raise CliAccessException()

    def mem_block(self, address, size):
        raise CliAccessException()

    def mem_save(self, filename, address, size):
        raise CliAccessException()

    def mem_read(self, address, size):
        raise CliAccessException()

    def mem_write(self, address, size, value):
        raise CliAccessException()

    def load_data(self, filename, address):
        raise CliAccessException()

    def read_io(self, address, size):
        raise CliAccessException()

    def write_io(self, address, size, value):
        raise CliAccessException()

    def trigger_smi(self, smi_value):
        raise CliAccessException()

    def read_msr(self, ap, address):
        raise CliAccessException()

    def write_msr(self, ap, address, value):
        raise CliAccessException()


    def read_sm_base(self):
        raise CliAccessException()

    @staticmethod
    def is_thread_alive(thread):
        raise CliAccessException()
