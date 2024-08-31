# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import binascii
import warnings
import configparser

SMI_TRIGGER_PORT = 0xB2
DEPRECATION_WARNINGS = False


class CliAccessException(Exception):
  def __init__(self, message="CliAccess is a virtual class!", error_code=None, *args, **kwargs):
    # Call the base class constructor with the parameters it needs
    hints = "\n".join(kwargs.get("hints", []))
    self.message = "[CliAccessExceptionError: {}] {}".format(error_code, message) if error_code else "[CliAccessException] {}".format(message)
    if hints:
      self.message += "\nHint: " + hints
    super(CliAccessException, self).__init__(self.message)


class CliOperationException(CliAccessException):
  def __init__(self, message="Operation Error!", error_code=None, *args, **kwargs):
    # Call the base class constructor with the parameters it needs
    hints = "\n".join(kwargs.get("hints", []))
    self.message = "[CliOperationError: {}] {}".format(error_code, message) if error_code else "[CliAccessException] {}".format(message)
    if hints:
      self.message += "\nHint: " + hints
    super(CliOperationException, self).__init__(self.message)


def deprecated(message):
  """
  This is a decorator which can be used to mark functions
  as deprecated. It will result in a warning being emitted
  when the function is used.
  """
  def deprecated_decorator(func):
      def deprecated_func(*args, **kwargs):
        if DEPRECATION_WARNINGS:
          warnings.warn("{} is a deprecated function. {}".format(func.__name__, message),
                        category=DeprecationWarning,
                        stacklevel=2)
          warnings.simplefilter('default', DeprecationWarning)
        return func(*args, **kwargs)
      return deprecated_func
  return deprecated_decorator


class BaseAccess(object):
  def __init__(self, access_name, child_class_directory):
    """

    :param access_name: Name of access method
    :param child_class_directory: Name of child class
    """
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
    data_dump = b""
    data_dump = data.to_bytes(size, byteorder="little", signed=False)
    return data_dump

  def read_config(self):
    try:
      self.config.read(self.config_file)
    except AttributeError:
      # EFI Shell may encounter at this flow while reading config file as .read method uses os.popen which is not available at EFI Python
      with open(self.config_file, "r") as config_file:
        self.config._read(config_file, self.config_file)

  # def __setattr__(self, attribute, value):
  #   # [cli-2.0.0]: why did we explicitly require this method ??, what are its use case?
  #   if attribute not in self.__dict__:
  #     print("Cannot set {}".format(attribute))
  #   else:
  #     self.__dict__[attribute] = value

  def halt_cpu(self, delay):
    raise CliAccessException()

  @deprecated("Please use method halt_cpu")
  def haltcpu(self, delay):
    return self.halt_cpu(delay)

  def run_cpu(self):
    raise CliAccessException()

  @deprecated("Please use method run_cpu")
  def runcpu(self):
    return self.run_cpu()

  def initialize_interface(self):
    raise CliAccessException()

  @deprecated("Please use method initialize_interface")
  def InitInterface(self):
    return self.initialize_interface()

  def close_interface(self):
    raise CliAccessException()

  @deprecated("Please use method close_interface")
  def CloseInterface(self):
    return self.close_interface()

  def warm_reset(self):
    raise CliAccessException()

  @deprecated("Please use method warm_reset")
  def warmreset(self):
    return self.warm_reset()

  def cold_reset(self):
    raise CliAccessException()

  @deprecated("Please use method cold_reset")
  def coldreset(self):
    return self.cold_reset()

  def mem_block(self, address, size):
    raise CliAccessException()

  @deprecated("Please use method mem_block")
  def memBlock(self, address, size):
    return self.mem_block(address, size)

  def mem_save(self, filename, address, size):
    raise CliAccessException()

  @deprecated("Please use method mem_save")
  def memsave(self, filename, address, size):
    return self.mem_save(filename, address, size)

  def mem_read(self, address, size):
    raise CliAccessException()

  @deprecated("Please use method mem_read")
  def memread(self, address, size):
    return self.mem_read(address, size)

  def mem_write(self, address, size, value):
    raise CliAccessException()

  @deprecated("Please use method mem_write")
  def memwrite(self, address, size, value):
    self.mem_write(address, size, value)

  def load_data(self, filename, address):
    raise CliAccessException()

  def read_io(self, address, size):
    raise CliAccessException()

  @deprecated("Please use method read_io")
  def readIO(self, address, size):
    return self.read_io(address, size)

  def write_io(self, address, size, value):
    raise CliAccessException()

  @deprecated("Please use method write_io")
  def writeIO(self, address, size, value):
    return self.write_io(address, size, value)

  def trigger_smi(self, smi_value):
    """
    Trigger Software (S/W) SMI of desired value
    :param smi_value: value of S/W SMI
    """
    raise CliAccessException()

  @deprecated("Please use method trigger_smi")
  def triggerSMI(self, SmiVal):
    """Trigger S/W SMI of desired value"""
    return self.trigger_smi(SmiVal)

  def read_msr(self, Ap, address):
    """
    Read MSR value at given address
    :param Ap:
    :param address: MSR Address
    """
    raise CliAccessException()

  @deprecated("Please use method read_msr")
  def ReadMSR(self, Ap, MSR_Addr):
    return self.read_msr(Ap, MSR_Addr)

  def write_msr(self, Ap, address, value):
    """
    Read MSR value at given address
    :param Ap:
    :param address: MSR Address
    :param value: Value to be written at MSR Address
    """
    raise CliAccessException()

  @deprecated("Please use method write_msr")
  def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
    return self.write_msr(Ap, MSR_Addr, MSR_Val)

  def read_sm_base(self):
    raise CliAccessException()

  @deprecated("Please use method read_sm_base")
  def ReadSmbase(self):
    return self.read_sm_base()

  @staticmethod
  def is_thread_alive(thread):
    raise CliAccessException()

  @deprecated("Please use method is_thread_alive")
  def isThreadAlive(self, thread):
    return self.is_thread_alive(thread)


@deprecated("Please use class BaseAccess")
class CliAccess(BaseAccess):
  pass
