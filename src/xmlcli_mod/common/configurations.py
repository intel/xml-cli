#
#  Copyright 2024 Hkxs
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the “Software”), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import configparser
import os
import sys
import tempfile


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

ENCODING = "utf-8"
ACCESS_METHOD = "linux"
ACCESS_METHODS = {"linux": "access/linux/linux.ini"}
PERFORMANCE = False
# BIOS Knobs Configuration file
BIOS_KNOBS_CONFIG = os.path.join(XMLCLI_DIR, 'cfg', 'BiosKnobs.ini')

OUT_DIR = TEMP_DIR
os.makedirs(OUT_DIR, exist_ok=True)

# Tools and Utilities
TIANO_COMPRESS_BIN = ""
BROTLI_COMPRESS_BIN = ""

STATUS_CODE_RECORD_FILE = os.path.join(XMLCLI_DIR, "messages.json")

# Reading other configuration parameters
CLEANUP = True
ENABLE_EXPERIMENTAL_FEATURES = True
