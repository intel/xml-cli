# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import sys
import tempfile
import configparser


def config_read(config_file):
  """As the UEFI Python has limitation,
  this method is to handle exception for the same in order to read configuration

  :param config_file: file to read in to config parser object
  :return: config parser object with config read from file
  """
  configparser_object = configparser.RawConfigParser(allow_no_value=True)
  try:
    configparser_object.read(config_file)
  except AttributeError:
    # EFI Shell may encounter at this flow while reading config file as .read method uses os.popen which is not available at EFI Python
    with open(config_file, "r") as f:
      configparser_object._read(f, config_file)
  return configparser_object


# Platform Details
PY3 = bool(sys.version_info.major == 3)
PLATFORM = sys.platform
PY_VERSION = f"_py{sys.version_info.major}.{sys.version_info.minor}"
SYSTEM_VERSION = (sys.version_info.major, sys.version_info.minor)

# Current directory src/common
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# XmlCli source directory
XMLCLI_DIR = os.path.dirname(CURRENT_DIRECTORY)
# Tools directory
TOOL_DIR = os.path.join(XMLCLI_DIR, "tools")
# directory in OS temporary location
TEMP_DIR = os.path.join(tempfile.gettempdir(), "XmlCliOut")

# Configuration parser object
CONFIG_FILE = os.path.join(XMLCLI_DIR, "xmlcli_mod.config")
XMLCLI_CONFIG = config_read(CONFIG_FILE)

ENCODING = XMLCLI_CONFIG.get("GENERAL_SETTINGS", "ENCODING")
ACCESS_METHOD = XMLCLI_CONFIG.get("GENERAL_SETTINGS", "ACCESS_METHOD")
PERFORMANCE = XMLCLI_CONFIG.getboolean("GENERAL_SETTINGS", "PERFORMANCE")
# BIOS Knobs Configuration file
BIOS_KNOBS_CONFIG = os.path.join(XMLCLI_DIR, 'cfg', 'BiosKnobs.ini')

OUT_DIR = os.path.join(XMLCLI_DIR, "out")
# output directory to be overridden if specified in config file
_OUT_DIR = XMLCLI_CONFIG.get("DIRECTORY_SETTINGS", "OUT_DIR")
if _OUT_DIR:
  if os.path.exists(os.path.abspath(_OUT_DIR)) and os.access(os.path.abspath(_OUT_DIR), os.W_OK):
    # check for absolute directory path and write permission
    OUT_DIR = os.path.abspath(_OUT_DIR)
  elif os.path.exists(os.path.join(XMLCLI_DIR, _OUT_DIR)) and os.access(os.path.join(XMLCLI_DIR, _OUT_DIR), os.W_OK):
    # check for relative directory path and write permission
    OUT_DIR = os.path.join(XMLCLI_DIR, _OUT_DIR)
  else:
    OUT_DIR = TEMP_DIR

if PLATFORM == "uefi":
  if not os.path.isdir(OUT_DIR):
    os.makedirs(OUT_DIR)
else:
  os.makedirs(OUT_DIR, exist_ok=True)

# Tools and Utilities

TIANO_COMPRESS_BIN = XMLCLI_CONFIG.get("TOOL_SETTINGS", "TIANO_COMPRESS_BIN")
if not os.path.isfile(os.path.abspath(TIANO_COMPRESS_BIN)):
  TIANO_COMPRESS_BIN = os.path.join(TOOL_DIR, TIANO_COMPRESS_BIN)
  TIANO_COMPRESS_BIN = f"{TIANO_COMPRESS_BIN}{'.exe' if PLATFORM == 'win32' and not TIANO_COMPRESS_BIN.endswith('.exe') else ''}"
  if not os.path.isfile(TIANO_COMPRESS_BIN):
    TIANO_COMPRESS_BIN = os.path.abspath(TIANO_COMPRESS_BIN)

BROTLI_COMPRESS_BIN = XMLCLI_CONFIG.get("TOOL_SETTINGS", "BROTLI_COMPRESS_BIN")

if not os.path.isfile(os.path.abspath(BROTLI_COMPRESS_BIN)):
  BROTLI_COMPRESS_BIN = os.path.join(TOOL_DIR, BROTLI_COMPRESS_BIN)
  BROTLI_COMPRESS_BIN = f"{BROTLI_COMPRESS_BIN}{'.exe' if PLATFORM == 'win32' and not BROTLI_COMPRESS_BIN.endswith('.exe') else ''}"
  if not os.path.isfile(BROTLI_COMPRESS_BIN):
    BROTLI_COMPRESS_BIN = os.path.abspath(BROTLI_COMPRESS_BIN)

STATUS_CODE_RECORD_FILE = os.path.join(XMLCLI_DIR, "messages.json")

# Reading other configuration parameters
CLEANUP = XMLCLI_CONFIG.getboolean("INITIAL_CLEANUP", "CLEANUP")

ENABLE_EXPERIMENTAL_FEATURES = XMLCLI_CONFIG.getboolean("EXPERIMENTAL_FEATURES_SETTINGS", "ENABLE_EXPERIMENTAL_FEATURES")


__all__ = ["XMLCLI_CONFIG",
           "PY3", "PY_VERSION", "SYSTEM_VERSION", "PLATFORM",
           "XMLCLI_DIR", "TEMP_DIR", "OUT_DIR",
           "ACCESS_METHOD", "ENCODING", "PERFORMANCE",
           "TIANO_COMPRESS_BIN", "BROTLI_COMPRESS_BIN",
           "STATUS_CODE_RECORD_FILE",
           "ENABLE_EXPERIMENTAL_FEATURES"
           ]


if __name__ == "__main__":
  pass
