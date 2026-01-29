class Version:
  def __init__(self, major, minor, build, tag=""):
    self.major=major
    self.minor=minor
    self.build=build
    self.tag=tag

  def __str__(self):
    return f"{self.major}.{self.minor}.{self.build}{self.tag}"

# MAJOR ----------
# incremented any time you change the API that may break backwards compatibility
# in a fairly major way
MAJOR = 2
# MINOR ------------
MINOR = 0
# BUILD ------
BUILD = 6  # or __revision__
# TAG -------
TAG = ""

version_instance = Version(MAJOR, MINOR, BUILD, TAG)

__version__ = str(version_instance)
