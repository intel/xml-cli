# -*- coding: utf-8 -*-

# Built-in imports
import os
import sys
import shutil
import unittest
import warnings

# Custom imports
from xmlcli.common import utils
from xmlcli.common import logger
from xmlcli.common import configurations

__author__ = "Gahan Saraiya"
__all__ = ["UnitTestHelper",
           "ONLINE_MODE", "OFFLINE_MODE", "RUN_OPTIONAL_TEST",
           "TEST_SUITE_CONFIG", "LOG_LEVEL", "LITE_FEATURE_TESTING"]

import configparser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(TEST_DIR, "tests.config")
TEST_SUITE_CONFIG = configparser.RawConfigParser(allow_no_value=True)
with open(CONFIG_FILE, "r") as f:
  TEST_SUITE_CONFIG._read(f, CONFIG_FILE)

# Globals to decide which tests to execute
TEST_SUITE_VERSION = TEST_SUITE_CONFIG.get("GENERAL_CONFIG", "VERSION")
ONLINE_MODE = TEST_SUITE_CONFIG.getboolean("TEST_SETTINGS", "ONLINE_MODE")
OFFLINE_MODE = TEST_SUITE_CONFIG.getboolean("TEST_SETTINGS", "OFFLINE_MODE")
ACCESS_METHOD = TEST_SUITE_CONFIG.get("TEST_SETTINGS", "ACCESS_METHOD")
RUN_OPTIONAL_TEST = TEST_SUITE_CONFIG.getboolean("TEST_SETTINGS", "RUN_OPTIONAL_TEST")
BIOS_IMAGES_DIR = os.path.abspath(TEST_SUITE_CONFIG.get("TEST_SETTINGS", "BIOS_IMAGES_DIR"))
LITE_FEATURE_TESTING = TEST_SUITE_CONFIG.getboolean("TEST_SETTINGS", "LITE_FEATURE_TESTING")

LOG_TITLE = TEST_SUITE_CONFIG.get("LOG_SETTINGS", "LOGGER_TITLE")
LOG_LEVEL = TEST_SUITE_CONFIG.get("LOG_SETTINGS", "LOG_LEVEL")

settings = logger.Setup(log_title=LOG_TITLE,
                       log_level=LOG_LEVEL,
                       log_format=TEST_SUITE_CONFIG.get("LOG_SETTINGS", "LOG_FORMAT"),
                       sub_module=TEST_SUITE_CONFIG.get("LOG_SETTINGS", "SUBMODULE_TITLE"),
                       log_dir=os.path.abspath(os.path.join(configurations.OUT_DIR, TEST_SUITE_CONFIG.get("LOG_SETTINGS", "LOG_FILE_LOCATION"))),
                       write_in_file=TEST_SUITE_CONFIG.getboolean("LOG_SETTINGS", "FILE_LOG"),
                       print_on_console=TEST_SUITE_CONFIG.getboolean("LOG_SETTINGS", "CONSOLE_STREAM_LOG"))


class UnitTestHelper(unittest.TestCase):
  access_mode = ACCESS_METHOD
  logger_settings = settings
  log = settings.logger

  @staticmethod
  def ignore_resource_warning():
    warnings.simplefilter("ignore", ResourceWarning)

  def runTest(self, *args, **kwargs):
    pass

  @staticmethod
  def is_valid_bios_image(file, valid_extensions=(".rom", ".bin")):
    if os.path.splitext(file)[-1] in valid_extensions:
      return True

  @property
  def temp_dir(self):
    return os.path.join(self.bios_image_dir, "temp")

  @property
  def access_method(self):
    if self.access_mode:
      return self.access_mode
    else:
      access_mode = "winhwa"
      _platform = utils.PLATFORM_DETAILS[0].lower()
      if _platform.startswith("linux"):
        access_mode = "linux"
      elif _platform.startswith("vmkernel"):
        access_mode = "esxi"
      elif _platform.startswith("win"):
        access_mode = access_mode
      elif sys.platform == "uefi":
        access_mode = "uefi"
      return access_mode

  @property
  def bios_image_dir(self):
    return BIOS_IMAGES_DIR

  @property
  def bios_image(self):
    return self.bios_roms[0]

  @bios_image.setter
  def bios_image(self, value):
    self._bios_image = value

  @property
  def bios_roms(self):
    bios_rom_location = self.bios_image_dir
    bios_roms = [os.path.join(bios_rom_location, bios_image) for bios_image in os.listdir(bios_rom_location) if self.is_valid_bios_image(bios_image)]
    return bios_roms

  @bios_roms.setter
  def bios_roms(self, value):
    self._bios_roms = value


if __name__ == "__main__":
  unittest.main()
