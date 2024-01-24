from distutils.version import LooseVersion

# MAJOR ----------
# incremented any time you change the API that may break backwards compatibility
# in a fairly major way
MAJOR = 2
# MINOR ------------
MINOR = 0
# BUILD ------
BUILD = 3  # or __revision__
# TAG -------
TAG = ""
__version__ = LooseVersion("{major}.{minor}.{build}{tag}".format(
  major=MAJOR,
  minor=MINOR,
  build=BUILD,
  tag=TAG
))
