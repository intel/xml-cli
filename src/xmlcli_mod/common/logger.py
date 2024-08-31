# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import sys
import json
import logging
from datetime import datetime

# Custom imports
from .configurations import XMLCLI_CONFIG, XMLCLI_DIR, OUT_DIR, PLATFORM, PY_VERSION, ENCODING, STATUS_CODE_RECORD_FILE

###############################################################################
# START: LOG Settings #########################################################
LOGGER_TITLE = XMLCLI_CONFIG.get("LOG_SETTINGS", "LOGGER_TITLE")
FILE_LOG = XMLCLI_CONFIG.getboolean("LOG_SETTINGS", "FILE_LOG")  # prints log on console if True
CONSOLE_STREAM_LOG = XMLCLI_CONFIG.getboolean("LOG_SETTINGS", "CONSOLE_STREAM_LOG")  # prints log on console if True
LOG_DIR = os.path.join(OUT_DIR, XMLCLI_CONFIG.get("LOG_SETTINGS", "LOG_DIR"))
LOG_LEVEL = XMLCLI_CONFIG.get("LOG_SETTINGS", "LOG_LEVEL")  # options for LOG_LEVEL = DEBUG|INFO|ERROR|WARN
LOG_FORMAT = XMLCLI_CONFIG.get("LOG_SETTINGS", "{}_LOG_FORMAT".format(LOG_LEVEL.upper()))
CONSOLE_LOG_LEVEL = XMLCLI_CONFIG.get("LOG_SETTINGS", "CONSOLE_LOG_LEVEL")  # override console log to differ from file logging
CONSOLE_LOG_FORMAT = XMLCLI_CONFIG.get("LOG_SETTINGS", "{}_LOG_FORMAT".format(CONSOLE_LOG_LEVEL.upper()))
LOG_DATE_FORMAT = XMLCLI_CONFIG.get("LOG_SETTINGS", "LOG_DATE_FORMAT")
LOG_FILE_NAME_DATE = XMLCLI_CONFIG.get("LOG_SETTINGS", "LOG_FILE_NAME_DATE")
LOG_FILE_NAME = XMLCLI_CONFIG.get("LOG_SETTINGS", "LOG_FILE_NAME")

# END: LOG Settings ###########################################################
