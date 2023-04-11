# -*- coding: utf-8 -*-
__author__ = "Gahan Saraiya"

# Built-in imports
import os
import sys

# Custom imports
import xmlcli
from xmlcli.modules.winContextMenu.xmlcli_registry_listener import RegistryListener

XMLCLI_DIR = os.path.dirname(xmlcli.__file__)
CONTEXT_MENU_PROJECT = os.path.join(XMLCLI_DIR, "modules", "winContextMenu")
REGISTRY_HANDLER_FILE = os.path.join(CONTEXT_MENU_PROJECT, "xmlcli_registry_listener.py")
ICON_FILE = os.path.join(CONTEXT_MENU_PROJECT, "XmlCli-square.ico")

REG_FILE = os.path.join(CONTEXT_MENU_PROJECT, "install_xmlcli_menu.reg")

CONTEXT_MENU_NAME = "XmlCli Menu"


def install_context_menu():
  if not sys.platform.startswith('win32'):
    print("Context Menu not supported on this OS")
    return False
  registry_obj = RegistryListener(xmlcli_path=XMLCLI_DIR)
  registry_content = registry_obj.create_registry_file(context_menu_name=CONTEXT_MENU_NAME, icon=ICON_FILE.replace("\\", "\\\\"))

  with open(REG_FILE, "w") as reg_ptr:
    reg_ptr.write(registry_content)

  status = os.system(f"cmd /c {REG_FILE}")
  print(f"Registry install status = {status}")
  return status


if __name__ == "__main__":
  install_context_menu()
