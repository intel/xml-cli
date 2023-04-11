import os
import sys

from setuptools import setup
from setuptools.command.install import install


class PostInstall(install):
  def run(self):
    super().run()  # Up to here is the default installation flow
    if sys.platform.startswith('linux'):  # Just for linux, change the attributes
      for filepath in self.get_outputs():
        if filepath.find("LzmaCompress") > -1 or filepath.find("TianoCompress") > -1 or filepath.find("Brotli") > -1:
          os.chmod(filepath, 0o777)


if __name__ == "__main__":
    setup(cmdclass={'install': PostInstall})
