# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

import os
import sys


def cli():
    """Shell Entry function for executable
    """
    try:
      # launch XmlCli modules in shell as default operation to perform
      from xmlcli import XmlCli as cli
      from xmlcli._version import __version__
      from xmlcli.common import bios_fw_parser
      from xmlcli.common import logger
      from xmlcli.common import utils
      from xmlcli.modules import helpers
      from xmlcli.modules.winContextMenu import install_context_menu
      from xmlcli.modules.webgui.main import run_gui

      print(f"xmlcli v{__version__}\n{os.path.dirname(cli.__file__)}")
      if len(sys.argv) > 1:
        if sys.argv[1].lower() in ('--version', '-v'):
          exit(1)
        if sys.argv[1].lower() in ('install', '--install'):
          install_context_menu.install_context_menu()
          if not set(sys.argv).intersection({'py', '--py', 'ipy', '--ipy'}):
            exit(1)
        if sys.argv[1].lower() in ('launch_gui', '--launch_gui'):
          run_gui()

    except Exception as e:
        print(
            f"Exception occurred: {e}\nCould not find XmlCli."
        )

    try:
      if not set(sys.argv).intersection({'py', '--py'}):
        # try to launch interactive python shell
        from IPython import embed

        embed(colors="neutral")
    except (ImportError, TypeError) as e:
        print("IPython needed for interactive usage")


if __name__ == "__main__":
  cli()
