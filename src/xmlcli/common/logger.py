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
RESULT_LEVEL_NUM = 21  # INFO level is 20, RESULT is kept above to always print.

# END: LOG Settings ###########################################################

# Add result LOG_LEVEL
logging.addLevelName(RESULT_LEVEL_NUM, "RESULT")

STATUS_CODE_RECORD = {}
with open(STATUS_CODE_RECORD_FILE, "r") as f:
  STATUS_CODE_RECORD.update(json.load(f))


def result(self, message, *args, **kws):
  """
  Custom log level result is created, one level above the info level
  if info is enabled, it will definitely print result but not vice versa

  :param self: class instance
  :param message: message
  :param args: arguments
  :param kws: keyword arguments
  :return:
  """
  if self.isEnabledFor(RESULT_LEVEL_NUM):
    # Yes, logger takes its '*args' as 'args'.
    self._log(RESULT_LEVEL_NUM, message, args, **kws)


def error(self, message="", error_code="0x1", *args, **kwargs):
  """
  Custom log level exception is created, same level as the error level
  It is to print additional information retrieved from messages.json

  :param self: class instance
  :param message: Message to be overwritten to modify from what exists in json
  :param error_code: error code has hex string is expected
              if integer specified then converted to hex
  :param args:
  :param kwargs: specify any custom hints to tackle problem
  """
  # Call the base class constructor with the parameters it needs
  if self.isEnabledFor(logging.ERROR):
    # Yes, logger takes its '*args' as 'args'.
    hints = "\n".join(kwargs.get("hints", []))
    if error_code:
      error_code = hex(error_code) if isinstance(error_code, int) else error_code
      error_data = STATUS_CODE_RECORD.get(error_code, {})
      if not message:
        message = error_data.get("msg", "!invalid_status_code!")
      if not hints.strip():
        hints = f"{error_data.get('hint', '')}\n{error_data.get('additional_details', '')}"
    message = f"[XmlCliError: {error_code}] {message}" if error_code else f"[XmlCliError] {message}"
    if hints.strip():
      message += f"\nHint: {hints}"
    self._log(logging.ERROR, message, args, **kwargs)


# Updating class instance method with custom log method
logging.Logger.result = result
logging.Logger.error = error


class Setup(object):
  """Setup Logging module for project
  """

  def __init__(self, **kwargs):
    """
    :param log_level: (optional) logging mode or level
    :param console_log_level: (optional) logging mode or level for console
      this option allows to override log level for console logging
    :param log_title: (optional) title for logging module
    :param log_format: (optional) format of log
    :param log_dir: (optional) logger title
    :param binary_dir: (optional) logging mode
      default is logging.DEBUG
    :param key_dir: (optional) Date Format for logging
      default is set to `%Y-%d-%m_%H.%M.%S`
    :param out_dir: (optional) output directory for module
    :return: None
  """
    self.log_level = kwargs.get("log_level", LOG_LEVEL).upper()
    self.console_log_level = kwargs.get("console_log_level", CONSOLE_LOG_LEVEL).upper()
    self.console_log_format = kwargs.get("console_log_format", CONSOLE_LOG_FORMAT)
    self.sub_module = kwargs.get("sub_module", "")
    self.log_title = kwargs.get("log_title", LOGGER_TITLE)
    if self.sub_module:
      self.log_title += ".{}".format(self.sub_module)
    self.log_format = kwargs.get("log_format", LOG_FORMAT)
    self.logger = logging.getLogger(self.log_title)
    self.log_dir = kwargs.get("log_dir", LOG_DIR)
    self.out_dir = kwargs.get("out_dir", OUT_DIR)
    self.xmlcli_dir = kwargs.get("xmlcli_dir", XMLCLI_DIR)
    self.log_file_name = kwargs.get("log_file_name", "{}_{}_{}{}.log".format(self.log_title.split(".")[0], datetime.now().strftime(LOG_FILE_NAME_DATE), PLATFORM, PY_VERSION))
    self.write_in_file = kwargs.get("write_in_file", FILE_LOG)
    self.print_on_console = kwargs.get("print_on_console", CONSOLE_STREAM_LOG)
    self.directory_maker()
    self.configure_logger()
  # self.display_system_configs()

  def display_system_configs(self):
    """Display logging configurations
    """
    config_data = "\n" + "="*50 + \
                  " SYSTEM CONFIGS " + "="*50 + \
                  "\n\t\t LOG_TITLE        : {}".format(self.log_title) + \
                  "\n\t\t SYS_VERSION      : {}".format(sys.version) + \
                  "\n\t\t LOG_DIR          : {}".format(self.log_dir) + \
                  "\n\t\t OUT_DIR          : {}".format(self.out_dir) + \
                  "\n\t\t XMLCLI_DIR       : {}".format(self.xmlcli_dir) + \
                  "\n\t\t LOG_LEVEL        : {}".format(self.log_level) + \
                  "\n\t\t CONSOLE LOG_LEVEL: {}".format(self.console_log_level) + \
                  "\n\t\t WRITE IN FILE    : {}".format(self.write_in_file) + \
                  "\n\t\t PRINT ON CONSOLE : {}".format(self.print_on_console) + \
                  "\n" + "="*100
    if not self.print_on_console:
      print(config_data)
    self.logger.info(config_data)
    return config_data

  def directory_maker(self):
    """Creates directories for use if not exist

    Important for new initialization when require directory does not exist
    or directory is removed due to any reason.

    Aimed to prevent FileNotFoundError caused due to non existence of directory.
    """
    directories = [self.log_dir]
    for d in directories:
      if not os.path.exists(d):  # adding condition to support python 2 implementation
        os.makedirs(d)

  def configure_logger(self, **kwargs):
    """Configures logging module

    :param kwargs:
      title: (optional) logger title
      mode: (optional) logging mode
        default is LOG_LEVEL defined globally
      console_mode: (optional) logging mode for console logging
        (if specified it will override value of specified `mode`)
        default is LOG_LEVEL defined globally
      log_file_name: (optional) name of the log file
        autogenerated based on timestamp if not specified
      log_format: (optional) log format
        default is set to `LOG_FORMAT`
      write_in_file: (optional) Boolean value Specifies whether to store log into file or not
        default value set to `FILE_LOG`
      print_on_console: (optional) toggle to `True`/`False`, setting it to True will allow
        print log on console
        default value set to `CONSOLE_STREAM_LOG`

    :return: status value status True if logger configuration successful
    """
    mode = kwargs.get("mode", self.log_level)
    write_in_file = kwargs.get("write_in_file", self.write_in_file)
    console_log_level = kwargs.get("console_log_level", self.console_log_level)
    console_log_format = kwargs.get("console_log_format", self.console_log_format)
    print_on_console = kwargs.get("print_on_console", self.print_on_console)
    title = kwargs.get("title", self.log_title)
    log_format = kwargs.get("log_format", self.log_format)
    logger = logging.getLogger(title)  # create logger with given title
    logger.setLevel(min(mode, console_log_level))  # set log level
    # configure basic logging configurations
    if print_on_console and not (any([isinstance(i, logging.StreamHandler) for i in logger.handlers])):
      handler = self.get_console_handler(console_log_level, console_log_format)
      # add the handlers to the logger
      logger.addHandler(handler)

    if write_in_file:
      log_file_name = kwargs.get("log_file_name", self.log_file_name)
      file_handler = self.get_file_handler(log_file_name, mode, log_format)
      # add the handlers to the logger
      if file_handler not in logger.handlers:
        logger.addHandler(file_handler)
    return True

  def get_console_handler(self, log_level=None, log_format=None):
    """

    :param log_level: logging level
    :param log_format: format for logging
    :return: handler for logging on console
    """
    log_level = log_level if log_level else self.console_log_level
    log_format = log_format if log_format else self.console_log_format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    # create formatter and add it to the handlers
    console_handler.setFormatter(logging.Formatter(log_format))
    return console_handler

  def get_file_handler(self, file_name, log_level=None, log_format=None):
    """

    :param file_name: log file name
    :param log_level: logging level
    :param log_format: format for logging
    :return: handler for logging at file
    """
    log_level = log_level if log_level else self.log_level
    log_format = log_format if log_format else self.log_format
    file_handler = logging.FileHandler(
      filename=os.path.join(self.log_dir, file_name),
      encoding=ENCODING, mode="w")
    file_handler.setLevel(log_level)
    # create formatter and add it to the handlers
    file_handler.setFormatter(logging.Formatter(log_format))
    return file_handler

  def get_logger(self, logger_name, file_name=None):
    logger = logging.getLogger(logger_name)
    logger.setLevel(self.log_level)
    # add the handlers to the logger
    console_handler = self.get_console_handler()
    if console_handler not in logger.handlers and not (any([isinstance(i, logging.StreamHandler) for i in logger.handlers])):
      logger.addHandler(console_handler)
    if file_name:
      file_handler = self.get_file_handler(self.log_file_name)
      if file_handler not in logger.handlers:
        logger.addHandler(file_handler)
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger

  def log_function_entry_and_exit(self, decorated_function):
    """
    Function decorator logging entry + exit and parameters of functions.
    Entry and exit as logging.info, parameters as logging.DEBUG.
    """
    from functools import wraps

    @wraps(decorated_function)
    def wrapper(*dec_fn_args, **dec_fn_kwargs):
      # Log function entry
      func_name = decorated_function.__name__
      self.logger.debug('Entering {}()...'.format(func_name))

      # get function params (args and kwargs)
      arg_names = decorated_function.__code__.co_varnames
      params = dict(
        args=dict(zip(arg_names, dec_fn_args)),
        kwargs=dec_fn_kwargs)

      self.logger.debug(
        func_name + ">> \t" + ', '.join([
          '{}={}'.format(str(k), repr(v)) for k, v in params.items()]))
      # Execute wrapped (decorated) function:
      out = decorated_function(*dec_fn_args, **dec_fn_kwargs)
      self.logger.debug('Done running {}()!'.format(func_name))

      return out
    return wrapper


if LOG_FILE_NAME:
  settings = Setup(log_file_name=LOG_FILE_NAME)
else:
  settings = Setup()
log = settings.logger


if __name__ == "__main__":
  pass
