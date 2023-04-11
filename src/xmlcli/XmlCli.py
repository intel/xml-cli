#!/usr/bin/env python
__author__ = ["Gahan Saraiya", "ashinde"]

# Built-in Imports

# Custom Imports
from .common import configurations
from .common.logger import log

if not configurations.PERFORMANCE:
  # Optional helper utilities
  from .modules import helpers
  from .common import utils

  utils.run_cleaner()
