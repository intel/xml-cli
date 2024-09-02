#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Built-in imports
import os
import io
import sys
import json
import uuid
import shlex
import ctypes
import binascii
import platform
import warnings
import logging

from xml.etree import ElementTree
from collections import namedtuple
from collections import defaultdict
from collections import OrderedDict

# Custom imports

from .configurations import ENCODING, XMLCLI_DIR, STATUS_CODE_RECORD_FILE
from defusedxml import ElementTree as ET

log = logging.getLogger(__name__)

###############################################################################
# START: Toggle for parser Configuration ######################################
SORT_FV = True
EXTRACT_FV_FFS = False  # [NOT RECOMMENDED to be enabled] extract and store fv/ffs in folder structure as bin file

ParsingLevel = namedtuple("PARSING_LEVEL", ["level", "name", "description"])
PARSING_LEVEL_MAP = {  # Define parsing level to enable what to parse while running the setup
  0: ParsingLevel(0, "PARSE_ALL", "Parses everything"),
  1: ParsingLevel(1, "SKIP_DECOMPRESSION", "Avoid parsing decompression section"),
  2: ParsingLevel(2, "SKIP_ENCAPSULATION", "Avoid parsing encapsulation section"),
  3: ParsingLevel(3, "SKIP_ENCAPSULATION_NESTED_FV", "Avoid parsing encapsulation section and nested FV parsing"),
  4: ParsingLevel(4, "SKIP_SECTION_PARSING", "Avoid parsing sections")
}
# END: Toggle for parser Configuration ########################################

#######################################################################################################################
# START: CONSTANTS ####################################################################################################
MEMORY_SIZE = 4 * (1024 ** 3)  # 4 GB
MAX_BIOS_SIZE = 32 * (1024 ** 2)  # 32 MB
PLATFORM_DETAILS = platform.uname()
SYSTEM_VERSION = (sys.version_info.major, sys.version_info.minor)
VALID_ACCESS_METHODS = ['itpii', 'baseipc', 'ipc', 'dci', 'ltb', 'svhif', 'svlegitp', 'itpsimics', 'linux', 'winssa',
                        'winsdk', 'winhwa', 'winrwe', 'svos', 'simics', 'tssa', 'uefi', 'esxi']
NETWORK_PROTOCOLS = [
  "afp",    # Apple Talk
  "ftp",    # File transfer Protocol
  "ftps",   # File transfer Protocol
  "nfs",    # Network File System
  "smb",    # Samba
  "ssh",    # SSH File transfer Protocol
  "sftp",   # SSH File transfer Protocol
  "dav",    # WebDAV
  "davs",   # WebDAV
]
STATUS_CODE_RECORD = {}
with open(STATUS_CODE_RECORD_FILE, "r") as f:
  STATUS_CODE_RECORD.update(json.load(f))
# END: GLOBAL CONSTANT ################################################################################################


#######################################################################################################################
# BEGIN: Utility methods ##############################################################################################


class XmlCliException(Exception):
  """
  Custom Exception class for raising XmlCli Exception with error codes
  All the error_code used must be available in file `messages.json`
  """
  def __init__(self, message="", error_code=None, *args, **kwargs):
    """
    :param message: Message to be overwritten to modify from what exists in json
    :param error_code: error code has hex string is expected
                if integer specified then converted to hex
    :param args:
    :param kwargs: specify any custom hints to tackle problem
    """
    # Call the base class constructor with the parameters it needs
    hints = "\n".join(kwargs.get("hints", []))
    if error_code:
      error_code = hex(error_code) if isinstance(error_code, int) else error_code
      error_data = STATUS_CODE_RECORD.get(error_code, {})
      if not message:
        message = error_data.get("msg", "!invalid_status_code!")
      if not hints.strip():
        hints = f"{error_data.get('hint', '')}\n{error_data.get('additional_details', '')}"
    self.message = f"[XmlCliError: {error_code}] {message}" if error_code else f"[XmlCliError] {message}"
    if hints.strip():
      self.message += f"\nHint: {hints}"
    log.error(self.message)
    super(XmlCliException, self).__init__(self.message)


def has_admin():
  """Check whether or not scripts having elevated privilege.
  Method is tested with Windows 10 and Ubuntu 20 LTS with Python version 3.8
  """
  if os.name == 'nt':
    try:
      # only windows users with admin privileges can read the C:\windows\temp
      os.listdir(os.path.join(os.environ.get('SystemRoot', 'C:\\windows'), 'temp'))
    except (WindowsError, FileNotFoundError, PermissionError):
      return False
    else:
      return True
  else:
    if 'SUDO_USER' in os.environ and os.geteuid() == 0:
      return True
    else:
      return False


def python_version_not_supported(minimum_version=(3, 7, 5), level="WARN"):
  """Throw warning or raise Exception for unsupported python version

  :param minimum_version: minimum python version require to avoid throwing warning/exception
  :param level: determine level whether to throw exception or raise warning
  :return:
    if exception raised then terminated currently executing scripts
    otherwise continue running the scripts with deprecation warning
  """
  if sys.version_info < minimum_version:
    word = "recommended" if level == "WARN" else "supported"
    exception_msg = f"Current Python version is not {word} to run this scripts."
    exception_msg += f"\nPlease use Python version {'.'.join(str(i) for i in minimum_version)} or above only."
    exception_msg += f"\nCurrent System info: {sys.version}"
    if level == "WARN":
      import warnings
      warnings.warn(exception_msg, DeprecationWarning)
    else:
      raise Exception(exception_msg)


def deprecated(message):
  """
  This is a decorator which can be used to mark functions
  as deprecated. It will result in a warning being emitted
  when the function is used.
  """
  def deprecated_decorator(func):
      def deprecated_func(*args, **kwargs):
          end_of_deprecated_function = "This method will be removed from XmlCli v3.0.0"
          warnings.warn(f"{func.__name__} is a deprecated function. {message}.\n {end_of_deprecated_function}",
                        category=DeprecationWarning,
                        stacklevel=2)
          warnings.simplefilter('default', DeprecationWarning)
          return func(*args, **kwargs)
      return deprecated_func
  return deprecated_decorator


def get_buffer(buffer):
  """Method to seek buffer of bytes as file pointer

  :param buffer: if buffer is seekable as if file pointer then it is returned
      otherwise it will be converted into seekable buffer
  :return: seekable buffer
  """
  if hasattr(buffer, "seek"):
    return buffer
  else:
    return io.BytesIO(buffer)


def seek_buffer(buffer, location):
  """Seek to specific byte of file buffer or byte array

  :param buffer: file buffer or bytes array
  :param location: location to where to move buffer pointer
  :return: location at what byte address the buffer pointer at
  """
  buffer = get_buffer(buffer)
  return buffer.seek(location)


def clean_directory(dir_path):
  """Utility to remove all files within the directory

  :param dir_path: directory location under which all files to be deleted
  :return: list of file cleared from the directory
  """
  files_removed = []
  if os.path.isdir(dir_path):
    for f in os.listdir(dir_path):
      location = os.path.join(dir_path, f)
      if os.path.isfile(location):
        try:
          os.remove(location)
          files_removed.append(location)
        except (OSError, WindowsError, PermissionError):
          pass
      else:
        files_removed += clean_directory(location)
        try:
          os.removedirs(location)
          files_removed.append(location)
        except (OSError, WindowsError, PermissionError):
          pass
  return files_removed


def clean_cache(top_dir, extensions=(".pyc", ".pyo")):
  """Clean temporary python files such as pyc file, __pycache_ folder

  :param top_dir: top directory from where to recursively cleanup the temp files
  :param extensions: Extensions to file to be cleaned up
  :return: list of absolute path of file/directory which are removed
  """
  import os
  removed_paths = []
  for path, dirs, files in os.walk(top_dir):
    for d in dirs:
      if d == "__pycache__":
        removed_paths += clean_directory(os.path.join(path, d))
        location = os.path.join(path, d)
        os.removedirs(location)
        removed_paths.append(location)
    for f in files:
      if os.path.splitext(f)[-1] in extensions:
        file_location = os.path.join(path, f)
        os.remove(file_location)
        removed_paths.append(file_location)
  return removed_paths


def make_directory(dir_path):
  """Make directory which is to be created

  :param dir_path: directory which is to be created
  :return:
  """
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)
  return dir_path


def get_tools_dir():
  tool_dir = os.path.join(XMLCLI_DIR, "tools")
  if os.path.exists(tool_dir):
    return tool_dir
  else:
    err_msg = "Unable to fetch Tool Directory!"
    log.error(err_msg)
    raise FileExistsError(err_msg)


def is_safe_path(basedir, path, follow_symlinks=True):
  # resolves symbolic links
  if follow_symlinks:
     match_path = os.path.realpath(path)
  else:
     match_path = os.path.abspath(path)
  return basedir == os.path.commonpath((basedir, match_path))


def get_temp_folder():
  try:
    import tempfile
    temp_folder = os.path.join(tempfile.gettempdir(), 'XmlCliOut')
    make_directory(temp_folder)
  except Exception as e:
    err_msg = f"Exception in creating temp folder!!\n>> {e}"
    log.error(err_msg)
    return err_msg
  return temp_folder


def get_top_lvl_dir(path):
  """Get the mount point of the given path

  :param path: path for which mount point to be found
  :return: mount point of the given path
  """
  return os.path.abspath(path).split(os.sep)[0] + os.sep


def get_user_dir():
  """Get the user directory of the system

  :return: absolute path to ser directory of the system
  """
  return os.path.abspath(os.path.expanduser("~"))


def is_network_path(path):
  """Checks whether path is network path or not Note: does not guarantees the whether it is valid path or not!! """
  if sys.platform == "win32":
    if path.startswith(r"\\"):  # for windows platform network path starts with prefix \\
      return True
    else:
      top_lvl_dir = get_top_lvl_dir(path).replace(os.sep, "")
      # print(top_lvl_dir)
      return os.path.ismount(top_lvl_dir)
  else:
    # for linux platform network path starts with prefix schema://
    # some schemas are included in NETWORK_PROTOCOLS
    # if re.findall('^[a-zA-Z]+://', path):
    network_sep = r"://"
    if network_sep in path:
      if path.split(network_sep)[0] in NETWORK_PROTOCOLS:
        return True
      else:
        print("Unsupported schema")
        return -1
  return False


def get_absolute_sizeof(data):
  """Provides absolute size of any data object

  Args:
    data: any data object

  Returns:
    absolute size of the data
  """
  if is_integer(data):
    bit_length = len(bin(data)[2:])
    return bit_length // 8 + (1 if bit_length % 8 else 0)
  return sys.getsizeof(data) - sys.getsizeof(data.__class__())


def round_up(number, multiple=8):
  """Round up the number to the next multiple

  Args:
    number: any integer
    multiple: any multiple

  Returns:  next multiple of the number

  Usage:
  >>> round_up(7, 8)
  8
  >>> round_up(8, 8)
  8
  >>> round_up(10, 8)
  16

  """
  return (number + multiple - 1) & (-multiple)


def generate_unique_id(string_format="xmlcli_mod"):
  guid = str(uuid.uuid4())
  formatted_guid = guid_formatter(guid=guid, string_format=string_format)
  return formatted_guid


def sort_all_json(path):
  files = [os.path.join(path, i) for i in os.listdir(path) if i.endswith("json")]
  for file in files:
    print(f"Processing: {file}")
    with open(file, "r", encoding=ENCODING) as f:
      d = json.load(f, encoding=ENCODING)
    print("    Json loaded")
    with open(file, "w", encoding=ENCODING) as f:
      json.dump(d, f, ensure_ascii=False, indent=4, sort_keys=True)
    print("    Json dumped")


def is_integer(val):
  """Check whether the value is integer or not

  :param val: value to check type is integer or not
  :return: boolean value True or False
  """
  result = isinstance(val, int)
  return result


def is_number(val):
  """Check whether the value is number or not

  :param val: value to check type is integer or not
  :return: boolean value True or False
  """
  result = isinstance(val, (int, float)) and '__int__' in dir(type(val))
  return result


def is_string(val):
  """Check whether the value is string or not

  :param val: value to check type is string or not
  :return: boolean value True or False
  """
  result = isinstance(val, str)
  return result


def get_integer_value(number, base=16):
  """Get valid integer number

  :param number: any number - integer, float, hex
  :param base: default base for value to be converted
  :return: integer number if valid integer, float or hex value
    otherwise returns False
  """
  if is_integer(number):
    return number
  elif isinstance(number, float) and '__int__' in dir(type(number)):
    return int(number)
  elif is_string(number):  # handle hex value
    if number.isdigit() and base == 10:
      return int(number)
    if number.isalnum():
      if number.lower().startswith('0o'):
        base = 8
      elif number.lower().startswith('0b'):
        base = 2
      elif number.lower().startswith('0x'):
        base = 16
      try:
        return int(number, base)
      except ValueError:  # invalid number with specified base
        return False
    else:
      return False
  else:
    return False


def get_string(val, encoding=ENCODING):
  """Python2/3 compatible method to get
  string value of given value from type str or unicode

  :param val: value to be converted to string
  :param encoding: expected encoding format of output string
  :return: string value
  """
  if (sys.version_info.major == 3) and isinstance(val, bytes):
    try:
      return val.decode(encoding=encoding)
    except UnicodeDecodeError:
      return val.decode("utf-16", "ignore")
  if isinstance(val, str):
    return val
  return str(val)


def convert_to_bytes(data, size=None, endian='little', **kwargs):
  """Convert data to bytes

  :param data: data to be hexed
    supported type string, integer, bytes
  :param size: (optional) specify if require to be fixed size
    default minimum size will be determined using `sys.getsizeof()`
  :param endian: specify endian style for integer
  :param kwargs:
      encoding: default encoding for string data set to the value of ENCODING from config file
      signed: for integer by default considered signed integer
        boolean type either True or False
  :return: dump: data in bytes format

  Raises:
    TypeError
    if data is neither belong in any of class int, bytes, str

  """
  require_min_size_of_data = get_absolute_sizeof(data)
  size = max(size, require_min_size_of_data) if size else require_min_size_of_data
  if isinstance(data, bytes):
    # data already in bytes, need not to perform any action
    dump = data.zfill(size)
  elif is_integer(data):
    # when data is integer
    signed = kwargs.get("signed", False)
    dump = data.to_bytes(size, byteorder=endian, signed=signed)
  elif isinstance(data, str):
    dump = data.zfill(size).encode(kwargs.get("encoding", ENCODING))
  else:
    error_msg = f"Given data belong to class {data.__class__} \n\tSupported class type for data is only str, int, bytes"
    raise TypeError(error_msg)
  return dump


def string_splitter(text, sep="\n", at=50):
  """Split the string/text content with
  specified separator	equally

  Args:
    text: text to be split
    sep: separator with which text to be split
    at: characters after which split should be done

  Returns: text with separator after every `at` character
  """
  return sep.join([text[i:i + at] for i in range(0, len(text), at)])


class MyJSONEncoder(json.JSONEncoder):
  def iterencode(self, o, _one_shot=False):
    list_lvl = 0
    for s in super(MyJSONEncoder, self).iterencode(o, _one_shot=_one_shot):
      if s.startswith('['):
        list_lvl += 1
        s = s.replace('\n', '').rstrip()
      elif 0 < list_lvl:
        s = s.replace('\n', '').rstrip()
        if s and s[-1] == ',':
          s = s[:-1] + self.item_separator
        elif s and s[-1] == ':':
          s = s[:-1] + self.key_separator
      if s.endswith(']'):
        list_lvl -= 1
      yield s


def guid_lis_to_str(guid_lis):
  """Convert GUID given as list in to guid string

  :param guid_lis: guid passed as list
  :return: string format of guid
  """
  for idx, guid_instance in enumerate(guid_lis):
    number = get_integer_value(guid_instance)
    if is_integer(number):
      if idx == 0:
        guid_lis[idx] = f"{number:0>8x}"
      elif idx == 1 or idx == 2:
        guid_lis[idx] = f"{number:0>4x}"
      elif idx == 3 and len(guid_lis) - 1 == 3:
        guid_lis[idx] = f"{number:0>16x}"
      elif idx == 3 and len(guid_lis) - 1 == 4:
        guid_lis[idx] = f"{number:0>4x}"
      else:
        guid_lis[idx] = f"{number:0>2x}"
    else:
      # Invalid GUID
      log.error(f"Invalid GUID list: {guid_lis}")
      return ""
  formatted_string = "-".join(guid_lis)
  return formatted_string


def guid_formatter(guid, string_format="default"):
  """Formats the guid for ease of comparing

  :param guid: guid to be formatted to string
  :param string_format: if specified to then format GUID as: 0xZZZZZZZZ-0xZZZZ-0xZZ-0xZZ-0xZZ-0xZZ-0xZZ....
                        otherwise ZZZZZZZZ-ZZZZ-ZZZZ-ZZZZZZZZZZZZZZZZ
  :return: string formatted GUID
  """
  if is_string(guid):
    guid = get_string(guid)
    guid = guid.replace("0x", "")
  elif isinstance(guid, list):
    guid = guid_lis_to_str(guid)
  else:
    err_message = f"Invalid GUID : {guid} [type: {type(guid)}]"
    log.error(err_message)
    raise Exception(err_message)
  hyphens_in_guid = guid.count("-")
  if hyphens_in_guid > 3:
    guid = ''.join(guid.rsplit('-', hyphens_in_guid - 3))
  guid = guid.lower()
  if string_format == "xmlcli_mod":
    guid_lis = guid.split("-")
    guid = '-'.join(
      f'0x{i}'
      for i in guid_lis[:3]) + "-" + '-'.join(list('-'.join(f'0x{i[j:j + 2]}' for j in range(0, len(i), 2)) for i in guid_lis[3:]))
  return guid


def guid_compare(guid1, guid2, string_format="default"):
  """Compare any two GUIDs

  :param guid1:
  :param guid2:
  :param string_format: setting GUID in specified format before comparison
  :return: True if both guid1 and guid2 are the same
  """
  guid1 = guid_formatter(guid1, string_format=string_format).replace("-", "").lower()
  guid2 = guid_formatter(guid2, string_format=string_format).replace("-", "").lower()
  return bool(guid1 == guid2)


def system_call(cmd_lis):
  """A wrapper to call system command to execute scripts

  :param cmd_lis: list of commands, flags to be passed while calling applicable method,
              first call will be attempted to subprocess, if it fails then os.popen
              and os.system will be tried out
  :return: None

  Usage:
  >>> system_call(cmd_lis=["ls", "-la"])
  """
  if cmd_lis:
    try:
      import subprocess
      subprocess.call(cmd_lis)
    except FileNotFoundError as e:
      import subprocess
      subprocess.call([shlex.quote(_cmd.replace(os.sep, "/")) for _cmd in cmd_lis])
    except Exception as e:
      err_msg = f"Exception on subprocess.call: {e}"
      log.error(err_msg)
      cmd = ' '.join([shlex.quote(_cmd.replace(os.sep, "/")) for _cmd in cmd_lis])
      log.debug(f"trying to work with command: {cmd}")
      try:
        result = os.popen(cmd).read()
        log.debug(result)
      except Exception as e:
        err_msg = f"Exception on os.popen: {e}"
        log.error(err_msg)
        os.system(cmd)


class StructureHelper(ctypes.Structure):
  """Helper to ctypes Structure providing features such as
  pretty printing structure

  """
  _pack_ = 1
  _fields_ = []
  start_buffer_address = 0

  @staticmethod
  def array_to_int(val):
    if val:
      flag = is_integer(list(val)[0])
      val = [f"{_val:0>2x}" if is_integer(_val) else _val.dump_dict() for _idx, _val in enumerate(list(val))]
      if flag:
        val = hex(int("".join(val[::-1]), 16))
    else:
      return ""
    return val

  def get_value(self, name):
    val = getattr(self, name)
    if isinstance(val, ctypes.Array):
      val = self.array_to_int(val)
    elif is_integer(val):
      val = f"0x{get_integer_value(val):x}"
    elif isinstance(val, bytes):
      val = get_string(val)
    elif isinstance(val, ctypes.Structure):
      val = val.dump_dict()
    else:
      val = f"{val}"
    return val

  def __get_str_value(self, name, _type, _format="{}"):
    """

    Args:
      name: name of variable in structure (defined in _fields_)
      _format: string formatting

    Returns:
      string representation of variable in structure

    """
    val = self.get_value(name)
    return _format.format(val)

  def __str__(self):
    result = f"{self.__class__.__name__} (@ 0x{self.start_buffer_address:x}):\n"
    max_name = max(get_absolute_sizeof(field[0]) + len(str(field[1])) for field in self._fields_)  # field -> (name, type)
    max_type = max(len(str(field[1]).strip()) for field in self._fields_)  # field -> (name, type)
    log.debug([(str(field[1]), len(str(field[1]).strip())) for field in self._fields_])
    for field in self._fields_:
      name, _type = field[0], field[1]
      result += f"{name:<{max_name}} {str(_type).strip():<{max_type}}: {self.__get_str_value(name, _type)}\n"
    return result

  def __repr__(self):
    return "{0} (0x{1:x}): ({2})".format(
      self.__class__.__name__, self.start_buffer_address,
      ", ".join(f"{field[0]}={self.__get_str_value(field[0], field[1], '{!r}')}" for field in self._fields_))

  @classmethod
  def _typeof(cls, field):
    """Get type of field

      The method should be treated as private method

    Example: A._typeof(A.fld)
    source: stackoverflow.com/a/6061483
    """
    for _field in cls._fields_:
      name, type_ = _field[0], _field[1]
      if getattr(cls, name) is field:
        return type_
    raise KeyError

  @classmethod
  def has_field(cls, field):
    """Check whether field exist or not
    """
    for _field in cls._fields_:
      name, type_ = _field[0], _field[1]
      if name == field:
        return True
    return False

  @property
  def cls_size(self):
    """Returns size of structure

    Note: Method not suitable for dynamic structure!!!
    """
    cls_size = 0
    for field in self._fields_:
      if len(field) == 3:
        cls_size += field[2] / (ctypes.sizeof(field[1])*8)
      else:
        cls_size += ctypes.sizeof(field[1])
    return int(cls_size)

  @classmethod
  def read_from(cls, buffer):
    """Loads binary content from file in to ctypes Structure

    Args:
      buffer: file_pointer to binary file

    Returns:

    """
    result = cls()
    if isinstance(buffer, bytes) or isinstance(buffer, bytearray):
      result = cls.from_buffer_copy(buffer)
    else:
      # print(">>>>>~~~~~~~~>>>> ", type(buffer))
      cls.start_buffer_address = buffer.tell()
      log.debug(f"Reading for STRUCTURE:``` {cls.__name__} @ 0x{cls.start_buffer_address:x}```")
      if buffer.readinto(result) != max(result.cls_size, ctypes.sizeof(cls)):
        log.debug(f"Error while reading: 0x{buffer.readinto(result):x} bytes")
        log.debug(f"Error while reading: 0x{result.cls_size:x} bytes")
        log.debug(f"Error while reading: 0x{ctypes.sizeof(cls):x} bytes")
        raise EOFError
    return result

  def dump_dict(self):
    # result = {name:str(type_) for name, type_ in self._fields_}
    result = {field[0]: self.get_value(field[0]) for field in self._fields_}
    return result

  def get_bytes(self):
    """

    Returns:
      bytearray of structure
    """
    return bytearray(self)


class Guid(StructureHelper):  # 16 bytes
  # source of structure : Edk2/BaseTools/Source/C/Include/Common/BaseTypes.h
  _fields_ = [
    ("data1", ctypes.c_uint32),
    ("data2", ctypes.c_uint16),
    ("data3", ctypes.c_uint16),
    ("data4", ctypes.ARRAY(ctypes.c_uint8, 8)),
  ]

  def read_guid(self, guid_str=None, guid_lis=None):
    """Read the value of guid in Structure

    :param guid_str: guid string which is to be treated as hex!
    :param guid_lis: Must be list of string kind!!
    :return:
    """
    if guid_lis:
      # TODO:check this method usage to process guid_lis
      guid_str = guid_lis_to_str(guid_lis)
    if guid_str:
      guid = guid_str.replace("0x", "").replace("-", "")
      single_byte_guid_lis = [guid[i:i + 2] for i in range(0, len(guid), 2)]
      setattr(self, "data1", get_integer_value(''.join(single_byte_guid_lis[:4]), base=16))
      setattr(self, "data2", get_integer_value(''.join(single_byte_guid_lis[4:6]), base=16))
      setattr(self, "data3", get_integer_value(''.join(single_byte_guid_lis[6:8]), base=16))
      for idx, val in enumerate(single_byte_guid_lis[8:]):
        getattr(self, "data4")[idx] = get_integer_value(val)
      return True

  def dump_dict(self):
    return self.get_str()

  def array_to_int(self, val):
    val = "".join([f"{_val:0>2x}" if is_integer(_val) else _val.dump_dict() for _idx, _val in enumerate(list(val))])
    return val

  def __get_str_value(self, name, _type, _format="{}"):
    val = getattr(self, name)
    if isinstance(val, ctypes.Array):
      val = self.array_to_int(val)
    elif is_integer(val):
      val = f"{val:0>{2 * ctypes.sizeof(_type)}x}"
    return _format.format(val)

  def __get_lis_value(self, name, _type, hex_display=True, _format="{}"):
    val = getattr(self, name)
    _prefix = "0x" if hex_display else ""
    if isinstance(val, ctypes.Array):
      val = [f"{_prefix}{_val:0>2x}" if hex_display else _val for _val in val]
    elif is_integer(val):
      val = [f"{_prefix}{val:0>{2 * ctypes.sizeof(_type)}x}" if hex_display else val]
    return val

  def get_hex_lis(self):
    result = []
    for name, _type in self._fields_:
      result += self.__get_lis_value(name, _type)
    return result

  def get_lis(self):
    result = []
    for name, _type in self._fields_:
      result += self.__get_lis_value(name, _type, hex_display=False)
    return result

  def get_str(self):
    result = "-".join([self.__get_str_value(name, _type) for name, _type in self._fields_])
    return result.lower()

  @property
  def guid(self):
    guid_lis = self.get_lis()
    return guid_formatter(guid_lis)

  def is_equal_to(self, guid):
    return guid_compare(self.guid, guid)

  def __str__(self):
    return self.get_str()


def load_nvar_xml(xml_file):
  """Loads Nvar XML into the python dictionary

  :param xml_file: XML file location to load
  :return: dictionary of nvars loaded from xml file
  """
  db = OrderedDict()
  if not os.path.exists(xml_file):
    # return empty db
    return db
  tree = ET.parse(xml_file)
  root = tree.getroot()
  for nvar in root:
    occupied_size = 0
    key = f"{nvar.attrib['name']}_{nvar.attrib['guid']}"
    db[key] = {
      "name"       : nvar.attrib["name"],
      "guid"       : nvar.attrib["guid"],
      "size"       : nvar.attrib.get("size", "0x0"),
      "status"     : get_integer_value(nvar.attrib.get("status", "0x0")),
      "is_exist"   : bool(get_integer_value(nvar.attrib.get("status", "0x0")) == 0),
      "next_offset": nvar.attrib.get("size", "0x0"),
      "attributes" : nvar.attrib.get("attributes", "0x7"),
      "operation"  : nvar.attrib.get("operation", "get"),
      "knobs"      : {}
    }
    for knob in nvar:
      knob_details = {
        "name"         : knob.attrib["name"],
        "knob_type"    : knob.attrib["setupType"],
        "value"        : knob.attrib["default"],
        "current_value": knob.attrib["CurrentVal"],
        "size"         : get_integer_value(knob.attrib["size"]),
        "offset"       : get_integer_value(knob.attrib["offset"]),
        "description"  : knob.attrib["description"],
      }
      occupied_size += get_integer_value(knob_details["size"])
      if get_integer_value(knob_details["size"]) + get_integer_value(knob_details["offset"]) > get_integer_value(db[key]["size"]):
        err_msg = f'Knob: "{knob_details["name"]}" sitting at offset {knob_details["offset"]} is overrunning the defined Nvar Size {db[key]["size"]}, Ignoring this entry..'
        log.error(err_msg)
      else:
        # knob_unique_key = utils.generate_unique_id()
        knob_unique_key = knob.attrib["name"]
        db[key]["knobs"][knob_unique_key] = knob_details
        if knob.attrib["setupType"] == "oneof":
          for options in knob:  # one only
            db[key]["knobs"][knob_unique_key]["options"] = [option.attrib for option in options]
        elif knob.attrib["setupType"] == "string":
          db[key]["knobs"][knob_unique_key]["min_characters"] = knob.attrib["minsize"]
          db[key]["knobs"][knob_unique_key]["max_characters"] = knob.attrib["maxsize"]
        elif knob.attrib["setupType"] == "numeric":
          db[key]["knobs"][knob_unique_key]["min_value"] = knob.attrib["min"]
          db[key]["knobs"][knob_unique_key]["max_value"] = knob.attrib["max"]
    db[key]["free_space"] = get_integer_value(db[key]["size"]) - occupied_size
    db[key]["next_offset"] = occupied_size
  return db


def store_buffer(dir_path, buffer, start, end, guid="", _type="FV", extract=False):
  """Utility to store content of buffer in file system.
  Enabling this utility will actually decomposes all the binaries in BIOS file system to
  folder structure

  :param dir_path: directory path where buffer bin to be stored
  :param buffer: buffer which is to be stored
  :param start: start region from where to binary to be stored
  :param end: end region at which binary should hold storing the value
  :param guid: unique guid if available otherwise empty string
  :param _type: type of the buffer to be stored
  :param extract: specifies whether extraction process to store buffer should be ignored or not.
  :return:
  """
  if EXTRACT_FV_FFS:
    # timestamp = datetime.now().strftime("%Y-%d-%m_%H.%M.%S")
    timestamp = ""
    dir_path = make_directory(dir_path)
    log.debug(f"PARAMS: \nDIR: {dir_path} \nstart: 0x{start:x}\nend: 0x{end:x}")
    buffer.seek(start)
    content = buffer.read(end-start)
    buffer.seek(start)
    # file_name = f"{guid}{_type.upper()}_0x{start:x}_to_0x{end:x}_T[{timestamp}].{_type.lower()}"
    file_name = f"{guid}_0x{start:x}_to_0x{end:x}.{_type.lower()}"
    with open(os.path.join(dir_path, file_name), "wb") as f:
      f.write(content)


def etree_to_dict(root):
  """Convert XMl to dictionary

  Args:
    root: root/node of the xml from which content is to be read

  Returns: dictionary of xml structure

  """
  result = {root.tag: {} if root.attrib else None}
  children = list(root)
  if children:
    dd = defaultdict(list)
    for dc in map(etree_to_dict, children):
      for k, v in dc.items():
        dd[k].append(v)
    result = {root.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
  if root.attrib:
    result[root.tag].update(('@' + k, v) for k, v in root.attrib.items())
  if root.text:
    text = root.text.strip()
    if children or root.attrib:
      if text:
        result[root.tag]['#text'] = text
    else:
      result[root.tag] = text
  return result


def dict_to_etree(d):
  """Convert dictionary to xml file

  Args:
    d: dictionary

  Returns:

  """

  def _to_etree(d, root):
    if not d:
      pass
    elif isinstance(d, str):
      root.text = d
    elif isinstance(d, dict):
      for k, v in d.items():
        assert isinstance(k, str)
        if k.startswith('#'):
          assert k == '#text' and isinstance(v, str)
          root.text = v
        elif k.startswith('@'):
          assert isinstance(v, str)
          root.set(k[1:], v)
        elif isinstance(v, list):
          for e in v:
            _to_etree(e, ElementTree.SubElement(root, k))
        else:
          _to_etree(v, ElementTree.SubElement(root, k))
    else:
      raise TypeError('invalid type: ' + str(type(d)))

  assert isinstance(d, dict) and len(d) == 1
  tag, body = next(iter(d.items()))
  node = ElementTree.Element(tag)
  _to_etree(body, node)
  return ElementTree.tostring(node)


def get_bios_knobs(file_path):
  """Parse the knobs from given xml file

  :param file_path: xml file location
  :return: dict of knobs
  """
  if not os.path.exists(file_path):
    err_msg = "File not exist"
    return False
  tree = ET.parse(file_path)
  root = tree.getroot()
  # get list of bios knobs from xml
  xml_dict = etree_to_dict(root)
  # filter out for only biosknobs from whole xml dictionary
  biosknobs = xml_dict.get("SYSTEM", {}).get("biosknobs", {}).get("knob", [])
  return biosknobs


def get_bios_version(file_path):
  """Get bios version from given xml file

  :param file_path: xml file location
  :return: Bios version string
  """
  if not os.path.exists(file_path):
    err_msg = "File not exist"
    return False
  tree = ET.parse(file_path)
  root = tree.getroot()
  bios_tag = root.find("BIOS") if root.find("BIOS") is not None else root.find("SVBIOS")
  bios_version = bios_tag.attrib.get("VERSION", "")
  return bios_version

def save_binary(input_bin_file, out_bin_file, offset, size):
  """
  Save specified chunk from original input binary to specified output file
  :param input_bin_file: input binary file
  :param out_bin_file: output binary file
  :param offset: start offset to read from input binary
  :param size: size to read from offset
  :return: path of saved output file
  """
  with open(input_bin_file, 'rb') as file_ptr:
    file_ptr.seek(offset)
    data = file_ptr.read(size)
  with open(out_bin_file, 'wb') as file_ptr:
    file_ptr.write(data)
  return out_bin_file


def stitch_binary(input_file, output_file, offset, stitch_file):
  """
  Stitch given file into given input binary to generate new output binary

  :param input_file: input binary file
  :param output_file: output binary file with stitched result
  :param offset: offset to start stitch from
  :param stitch_file: file to be stitched
  :return: output file path
  """
  with open(stitch_file, 'rb') as stitch_file_ptr:
    stitch_file_data = stitch_file_ptr.read()

  with open(input_file, 'rb') as input_file_ptr:
    result = input_file_ptr.read(offset) + stitch_file_data
    if os.path.getsize(input_file) > len(result):
      input_file_ptr.seek(len(result))
      result += input_file_ptr.read()

  with open(output_file, 'wb') as output_file_ptr:
    output_file_ptr.write(result)

  log.info(f'output binary {output_file} \nsize = 0x{os.path.getsize(output_file):X}')
  return output_file


class Table(object):
  def __init__(self, width=[], separator="="):
    self.separator = separator
    if width:
      self.width = width

  @staticmethod
  def _max_col_width(data=[[], []]):
    """Private class method Used within class member to dynamically calculate width if user does not provides width
    however, to calculate the same at least 2 data row required.

    :param data: a list contains data (2D list)
    :return: returns a list which contains width of each column
    """
    column_width = 0
    if isinstance(data, list):
      data_length = [len(row) for row in data]
      for row in data:  # handling data with different length.
        while len(row) < max(data_length):
          row.append("")
      column_width = [(max([len(str(row[i])) for row in data]) + 3) for i in range(len(data[0]))]
    return column_width

  def data_separator(self, width=[]):
    """Function to create a separator

    :param width: a list contains width [1D]
    :return: returns a string contains separator of length is equal to sum of width
    """
    if width:
      return self.separator * (sum(width, len(width))+1) + '\n'
    else:
      return self.separator * (sum(self.width, len(self.width))+1) + '\n'

  def create_header(self, header=[], width=[]):
    """Function to create header in tabular format

    :param header: a list contains header [must be a 1D list]
    :param width: a list contains width of each column [1D]
    :return: returns a string which contains header with separator before and after the header in the tabular format

    Usage:
    Calling create_header function with width
      self.create_header(data=<data-in-list>, width=<width-of-each-column>)
      # Here <data-in-list> is a list of data which can be 1D or 2D list and width is a list contains width of column

    Calling create_header function without width
      self.create_header(data=<data-in-list>, width=0) # Here data_in_list is a list of data which can be 1D or 2D list
      self.create_header(data=<data-in-list>) # Here data_in_list is a list of data which can be 1D or 2D list

    Example:
    >>> head=['Admission No','Firstname','Surname','DoB']
    >>> self.create_header(header=head, width=0)  # calling create_header with header and without width
    >>> self.create_header(header=head, width=[6,8,8,10])  # calling create_header with header and  width
    >>> self.create_header(header=head)  # calling create_data with data and without width
    """
    result = ""
    if isinstance(header, list) and not isinstance(header[0], list):
      if not width:  # if width not provided by user then calculate the width dynamically
        width = self._max_col_width([header])
      width = width if len(header) == len(width) else self._max_col_width([header])  # to handle when user provides wrong width
      result += self.data_separator(width)  # adding separator before starting of header
      for col_idx in range(len(header)):
        row_format = "|"+"{:^"+str(width[col_idx])+"}"
        result += row_format.format(header[col_idx][:width[col_idx]])
      result += "|"+"\n"+self.data_separator(width)
    else:
      log.error("Header must be 1D list")
    return result

  def create_data(self, data=[[]], width=[], treat_number='hex'):
    """Function to create data in tabular format

    :param data: a list contains data [1D or 2D]
    :param width: a list contains width of each column [1D]
    :param treat_number: if treat_number='hex' convert integer value to hex else treat it as integer
    :return: returns a string which contains data in the tabular format

    Usage:
    Calling create_data function with width
      # Here <data-in-list> is a list of data which can be 1D or 2D list and width is a list contains width of column
      create_data(data=<data-in-list>, width=<width-of-each-column>, treat_number='hex')
      create_data(data=<data-in-list>, width=<width-of-each-column>, treat_number='int')

    Calling create_data function without width
      # Here <data-in-list> is a list of data which can be 1D or 2D list
      create_data(data=<data-in-list>, width=0, treat_number='hex')
      create_data(data=<data-in-list>, width=0, treat_number='int')

    Example:
    >>> data_in_list = [[68103, 'Darren','Kirk','12/19/1994'], [68104, 'Sophie','Meadows','12/20/1993']]
    >>> self.create_data(data=data_in_list, width=0, treat_number='hex')  # calling create_data with data and without width and treating integer value as hex
    >>> self.create_data(data=data_in_list, width=[6,8,8,10], treat_number='hex')  # calling create_data with data, width and treating integer value as hex
    >>> self.create_data(data=data_in_list, width=0, treat_number='int')  # calling create_data with data, without width and treating integer value as integer
    >>> self.create_data(data=data_in_list, width=[6,8,8,10], treat_number='int')  # calling create_data with data, without width and treating integer value as integer
    """
    result = ""
    if isinstance(data, list) and not isinstance(data[0], list):  # if data is 1D then convert it to 2D list
      data = [data]
    data_length = []
    _data = []
    for row in data:  # converting integer value to hex if treat_number == 'hex'
      _data.append([hex(row_data) if treat_number == 'hex' and isinstance(row_data, int) else f'{row_data}' for row_data in row])
      data_length.append(len(row))
    for row in _data:  # making all the rows in data with same length by padding "" if there is a mismatch in length
      while len(row) < max(data_length):
        row.append("")
    if not width:  # if width not provided by user then calculate the width dynamically
      width = self._max_col_width(data)
    width = width if len(_data[0]) == len(width) else self._max_col_width(_data)  # to handle when user provides wrong width
    for row in _data:
      for col_idx in range(len(width)):
        row_format = "|" + "{:^" + str(width[col_idx]) + "}"
        result += row_format.format(row[col_idx][:width[col_idx]])
      result += "|"+'\n'
    return result

  def create_table(self, header=[], data=[[]], width=[], treat_number='hex'):
    """Function to convert list of data into tabular form

    :param header: a list contains column header (1D)
    :param data: a list contains data [1D or 2D]
    :param width: a list contains width of each column [1D]
    :param treat_number:if treat_number='hex' convert integer value to hex else treat it as integer
    :return: returns the string which contains given data in tabular format with separator between header and data

    Usage:
    Calling create_table function without header
      <data-in-list> is a list of data which can be 1D or 2D list and width is a list contains width of column
      create_table(header=0, data=<data-in-list>, width=<width-of-each-column>)
      create_table(header=0, data=<data-in-list>, width=<width-of-each-column>, treat_number='hex')

    Calling create_table function without header and width
      <data-in-list> is a list of data which can be 1D or 2D list
      create_table(header=0, data=<data-in-list>, width=0, treat_number='int')
      create_table(header=0, data=<data-in-list>)

    Calling create_table function with header
      <header-list> is a list of column headers in 1D and
      <data-in-list> is a list of data which can be 1D or 2D list and width is a list contains width of column
      create_table(header=<header-list>, data=<data-in-list>, width=<width-of-each-column>)
      create_table(header=<header-list>, data=<data-in-list>, width=<width-of-each-column>, treat_number='hex')

    Calling create_table function with header and without width
      Here <header-list> is a list of column headers in 1D and
      <data-in-list> is a list of data which can be 1D or 2D list
      create_table(header=<header-list>, data=<data-in-list>, width=0, treat_number='hex')
      create_table(header=<header-list>, data=<data-in-list>)

    Example:
    >>> header_list = ['HeaderVersion', 'ModuleSubType', 'ChipsetID', 'Flags', 'ModuleVendor', 'dd.mm.yyyy', 'Size', 'Version']
    >>> data_in_list = [['0x30000', '0x1', '0xb00c', '0x8000', '0x8086', '22-10-2021', '0x2f000', '1.18.5'], ['0x30000', '0x1', '0xb00c', '0x8000', '0x8086', '22-10-2021', '0x2f000', '1.18.10']]

    >>> self.create_table(header=0, data=data_in_list, width=width_in_list)  # with data, width and without header
    >>> self.create_table(header=0, data=data_in_list)  # with data and without header, width
    >>> self.create_table(header=header_list, data=data_in_list, width=width_in_list) # with header,data and width
    >>> self.create_table(header=header_list, data=data_in_list)  # with header, data and without width
    >>> self.create_table(header=0, data=data_in_list, width=width_in_list, treat_number='hex') # with data, width and without header
    >>> self.create_table(header=0, data=data_in_list, width=0, treat_number='hex')  # with data and without header, width
    >>> self.create_table(header=header_list, data=data_in_list, width=width_in_list, treat_number='hex')  # with header,data and width
    >>> self.create_table(header=header_list, data=data_in_list, width=0, treat_number='hex')  # with header, data and without width
    """
    result = ""
    if isinstance(data, list) and not isinstance(data[0], list):
      data = [data]
    if isinstance(header, list) and not isinstance(header[0], list) and isinstance(data, list):
      row_length = max(len(header), max([len(row) for row in data]))
      for row in data:  # making all the rows in data as same length by padding ""
        while len(row) < row_length:
          row.append("")
      if len(header) < row_length:
        for i in range(row_length - len(header)):
          header.append("")
      data.insert(0, header)
      if not width:  # if width not provided by user then calculate the width dynamically
        width = self._max_col_width(data)
      width = width if len(data[0]) == len(width) else self._max_col_width(data)  # handle when user provides wrong width
      result = self.create_header(header, width) + self.create_data(data[1:], width, treat_number) + self.data_separator(width)
    elif isinstance(data, list) and header == 0:
      if not width:  # if width not provided by user then calculate the width dynamically
        width = self._max_col_width(data)
      width = width if len(data[0]) == len(width) else self._max_col_width(data)  # handle when user provides wrong width
      result = self.data_separator(width) + self.create_data(data, width, treat_number) + self.data_separator(width)
    return result


def is_read_ok(file_path):
  """
  Function to check the given file path is valid and has read permission

  :param file_path: input binary file
  :return: True if path exists and have read permission
  """
  if isinstance(file_path, str) and os.path.isfile(os.path.abspath(file_path)) and os.access(
    os.path.abspath(file_path), os.R_OK):
    return True


def is_write_ok(file_path):
  """
  Function to check the given file path is valid and has write permission

  :param file_path: input binary file
  :return: True if given file path exists and have write permission
  """

  if isinstance(file_path, str) and os.access(os.path.abspath(os.path.dirname(file_path)), os.W_OK):
    return True


def zero_padding(binary, size):
  """
  Function to pad zero's to the binary file

  :param binary: input binary Bytearray
  :param size : Number of bytes to be padded for the given binary
  :return: zero Padded binary
  """

  binary_file = bytearray(binary)
  zero_pad = bytearray(size)
  binary_file.extend(zero_pad)
  return binary_file

def unhex_lify(integer):
  """
  Function to convert an integer to its corresponding string representation using hexadecimal encoding.

  :param integer: The integer to be converted.
  :return: the string representation of the integer
  """
  return binascii.unhexlify((hex(integer)[2:]).strip('L')).decode()


def is_root():
  return os.geteuid() == 0
