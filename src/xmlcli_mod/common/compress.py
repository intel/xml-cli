# -*- coding: utf-8 -*-

# Built-in imports
import os
import sys
import shlex
from collections import namedtuple
from datetime import datetime

# Custom imports
from . import utils
from . import logger
from . import configurations

__author__ = "Gahan Saraiya"

log = logger.settings.logger

COMPRESSION_GUIDS = [
  "ee4e5898-3914-4259-9d6edc7bd79403cf",
  "3d532050-5cda-4fd0-879e0f7f630d5afb"
]


def lzma_decompress(compressed_file, decompressed_file, min_python=(3, 7, 5)):
  if sys.version_info >= min_python:
    import lzma
    try:
      import shutil
      with lzma.open(compressed_file, "rb") as compressed_data:
        with open(decompressed_file, "wb") as uncompressed_output:
          shutil.copyfileobj(compressed_data, uncompressed_output)
    except Exception as e:
      log.debug("failed to decompress lzma...\n Trying in-memory decompression")
      with open(compressed_file, "rb") as compressed_data:
        decompressed_data = lzma.decompress(compressed_data.read())
        # write in memory data to file
        with open(decompressed_file, "wb") as f:
          f.write(decompressed_data)
          return True
  else:
    log.error(f"Decompression not supported. Please move to Python version {min_python} or above")


class ProcessEncapsulatedData(object):
  def __init__(self, guid, compressed_data, section, **kwargs):
    self.guid = utils.guid_formatter(guid)
    self.compressed_data = compressed_data
    self.section = section
    self.decompress_map = namedtuple("Decompressor", ["name", "guid", "method"])
    self.decompression_guid_map = {
      "ee4e5898-3914-4259-9d6edc7bd79403cf": self.decompress_map("LZMA_CUSTOM_DECOMPRESS_GUID", [0xEE4E5898, 0x3914, 0x4259, 0x9D, 0x6E, 0xDC, 0x7B, 0xD7, 0x94, 0x03, 0xCF], self.lzma_custom_decompress),
      "3d532050-5cda-4fd0-879e0f7f630d5afb": self.decompress_map("BROTLI_CUSTOM_DECOMPRESS_GUID", [0x3D532050, 0x5CDA, 0x4FD0, 0x87, 0x9E, 0x0F, 0x7F, 0x63, 0x0D, 0x5A, 0xFB], self.brotli_custom_decompress),
      "a31280ad-481e-41b6-95e8127f4c984779": self.decompress_map("TIANO_CUSTOM_DECOMPRESS_GUID", [0xA31280AD, 0x481E, 0x41B6, 0x95, 0xE8, 0x12, 0x7F, 0x4C, 0x98, 0x47, 0x79], self.tiano_custom_decompress),
    }
    self.temp_folder = kwargs.get("temp_folder", utils.get_temp_folder())
    self.tool_dir = kwargs.get("tool_dir", utils.get_tools_dir())
    self.brotli_compression_utility = configurations.BROTLI_COMPRESS_BIN
    self.tiano_compression_utility = configurations.TIANO_COMPRESS_BIN
    self.timestamp = datetime.now().strftime(logger.LOG_DATE_FORMAT)
    self.input_file_path = os.path.join(self.temp_folder, "fv_compressed_{}_{}{}.sec")
    self.output_file_path = os.path.join(self.temp_folder, "fv_decompressed_{}_{}{}.sec")
    self.directory_initialization()

  def directory_initialization(self):
    # write in memory data to file
    with open(self.temp_file_path, "wb") as f:
      f.write(self.compressed_data)

  @property
  def decompressed_file_path(self):
    guid_str = utils.get_string(self.guid)
    return self.output_file_path.format(guid_str, self.timestamp, configurations.PY_VERSION)

  @property
  def temp_file_path(self):
    guid_str = utils.get_string(self.guid)
    return self.input_file_path.format(guid_str, self.timestamp, configurations.PY_VERSION)

  def to_be_implemented(self):
    err_msg = "Given decompression method does not implemented so far, will be implemented in upcoming future"
    raise NotImplementedError(err_msg)

  @staticmethod
  def system_call(output_file_check, cmd=None, cmd_lis=None):
    utils.system_call(cmd_lis)
    if cmd_lis and not os.path.exists(output_file_check):
      import subprocess
      subprocess.call([cmd for cmd in cmd_lis])
    elif cmd and not os.path.exists(output_file_check):
      utils.system_call(shlex.split(cmd, posix=(configurations.PLATFORM != "win32")))

  def lzma_custom_decompress(self):
    if sys.version_info <= (3, 7, 5):
      raise utils.XmlCliException("Decompression not supported on your python version. Please move to Python version 3.7.5 or above")
    else:
      # lzma is built-in compression method since Python 3.4 (using 3.7.5 which has bug fixed)
      import lzma
      decompressed_data = lzma.decompress(self.compressed_data)
      # write in memory data to file
      with open(self.decompressed_file_path, "wb") as f:
        f.write(decompressed_data)
    return decompressed_data

  def tiano_custom_decompress(self):
    # decompress with binary utility
    cmd = f'"{self.tiano_compression_utility}" -d -q "{self.temp_file_path}" -o "{self.decompressed_file_path}"'
    cmd_lis = [self.tiano_compression_utility, "-d", "-q", self.temp_file_path, "-o", self.decompressed_file_path]
    self.system_call(cmd=cmd, cmd_lis=cmd_lis, output_file_check=self.decompressed_file_path)
    with open(self.decompressed_file_path, "rb") as f:
      decompressed_data = f.read()
    return decompressed_data

  def brotli_custom_decompress(self):
    # decompress with binary utility
    cmd = f'"{self.brotli_compression_utility}" -d -i "{self.temp_file_path}" -o "{self.decompressed_file_path}"'
    cmd_lis = [self.brotli_compression_utility, "-d", "-i", self.temp_file_path, "-o", self.decompressed_file_path]
    self.system_call(cmd=cmd, cmd_lis=cmd_lis, output_file_check=self.decompressed_file_path)
    with open(self.decompressed_file_path, "rb") as f:
      decompressed_data = f.read()
    return decompressed_data

  def decompress(self):
    log.info(f"Decompressing File...GUID: {self.guid}")
    decompressor = self.decompression_guid_map.get(self.guid, None)
    decrypter = self.decompression_guid_map.get(self.guid, None)
    if decompressor:
      log.info("Decompressing...")
      log.info(decompressor)
      decompression_method = decompressor.method
      decompressed_data = decompression_method()
      log.info("Returning successful decompressed data")
      return decompressed_data
    elif decrypter:
      log.info("Decrypting...")
      log.info(decrypter)
    else:
      err_msg = f"Given decompression/decrypting method (for GUID: {self.guid})does not exist"
      log.error(err_msg)
    # raise NotImplementedError(err_msg)


if __name__ == "__main__":
  pass
