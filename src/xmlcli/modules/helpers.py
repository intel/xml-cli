# -*- coding: utf-8 -*-
"""
This file consists of various helper methods for the XmlCli existing operations
"""
__author__ = "Gahan Saraiya"

# Built-in imports
import os

# Custom imports
from .. import XmlCli as cli
from .. import XmlCliLib as clb
from ..common import utils
from ..common.logger import log
from ..XmlIniParser import nstrip
from .winContextMenu.install_context_menu import install_context_menu

try:
  from defusedxml import ElementTree as ET
except ModuleNotFoundError as e:
  log.warn("Insecure module import used! Please install all the required dependencies by running `pip install -r requirements.txt`")
  from xml.etree import ElementTree as ET


def move_output_files_to(destination_path):
  """
  Move files from one directory to another

  :param destination_path: destination directory
  :return:
  """
  if not os.path.exists(destination_path):
    log.error(f'{destination_path} does not exists, not able to move out files\n')
    return 1
  new_out_dir = os.path.join(destination_path, 'out')
  os.makedirs(new_out_dir, exist_ok=True)
  for root, dirs, files in os.walk(clb.TempFolder):
    for name in files:
      if not (name == 'Makefile'):
        if os.path.exists(os.path.join(new_out_dir, name)):
          os.remove(os.path.join(new_out_dir, name))
        os.rename(os.path.join(root, name), os.path.join(new_out_dir, name))
  return 0


def move_output_to_current_directory():
  """
  Move xmlcli output directory to current directory
  :return:
  """
  move_output_files_to(os.getcwd())


def print_nvar_response_buffer(nvar_response_buffer_file=None):
  """
  Print nvar response buffer
  :param nvar_response_buffer_file: Nvar response buffer file
  :return:
  """
  if not nvar_response_buffer_file:
    nvar_response_buffer_file = os.path.join(clb.TempFolder, 'NvarRespBuff.bin')
  with open(nvar_response_buffer_file, 'rb') as out_file:  # opening for writing
    current_parameters = list(out_file.read())
  current_parameter_size = len(current_parameters)
  response_buffer_ptr = 0
  header = ['Offset Ptr', 'Status', 'Attribute', 'Data Size', 'Variable Name', 'VarGuid']
  data_lis = []
  for _ in range(0, 0x100):
    if response_buffer_ptr >= current_parameter_size:
      break
    offset = response_buffer_ptr
    guid = clb.FetchGuid(current_parameters, response_buffer_ptr)
    attribute = clb.ReadList(current_parameters, response_buffer_ptr + 0x10, 4)
    size = clb.ReadList(current_parameters, response_buffer_ptr + 0x14, 4)
    status = clb.ReadList(current_parameters, response_buffer_ptr + 0x18, 4)
    operation = clb.ReadList(current_parameters, response_buffer_ptr + 0x1C, 1)
    name = ''
    for VarSizeCount in range(0, 0x80):
      val = clb.ReadList(current_parameters, (response_buffer_ptr + 0x1D + VarSizeCount), 1)
      if val == 0:
        response_buffer_ptr = response_buffer_ptr + 0x1D + VarSizeCount + 1
        break
      name += chr(val)
    response_buffer_ptr = response_buffer_ptr + size
    data_lis.append([hex(offset), hex(status), hex(attribute), hex(size), name, clb.GuidStr(guid)])

  log.result(utils.Table().create_table((header, data_lis)))


def generate_knobs_delta(ref_xml, new_xml, out_file=r'KnobsDiff.log', compare_tag='default'):
  """
  Take difference of Setup Option between two BIOS/IFWI xml file

  :param ref_xml: reference bios/ifwi binary
  :param new_xml: another bios/ifwi binary to compare against reference file
  :param out_file: output file location to store difference result at
  :param compare_tag: xml attribute to be compared against (default|CurrentVal|size|prompt|depex|...)
  :return: file content of result_log_file

  Usage:
  >>> generate_knobs_delta("/path/to/PlatformConfig.2277_FwInfo.xml", "/path/to/PlatformConfig.2283_FwInfo.xml", "KnobsDiff.log")
  """
  ref_tree = None
  new_tree = None
  ref_tree = ET.parse(ref_xml)
  new_tree = ET.parse(new_xml)
  ref_knobs_map = {}
  new_knobs_map = {}
  bios_tag = ['BIOS', 'SVBIOS', 'CPUSVBIOS']
  ref_knobs_bios_version = ''
  new_knobs_bios_version = ''
  internal_compare_tags = ['default', 'offset', 'CurrentVal', 'size', 'varstoreIndex']
  all_compare_tags = ['default', 'offset', 'CurrentVal', 'size', 'prompt', 'description', 'depex', 'setupType', 'varstoreIndex']
  current_compare_tags = []
  for tag_value in compare_tag.split(','):
    tag_value = tag_value.strip()
    if tag_value in all_compare_tags:
      current_compare_tags.append(tag_value)

  for count in range(0, 3):
    if ref_knobs_bios_version == '':
      for ref_xml_bios in ref_tree.iter(tag=bios_tag[count]):
        ref_knobs_bios_version = nstrip(ref_xml_bios.get('VERSION'))
        break

  for count in range(0, 3):
    if new_knobs_bios_version == '':
      for MyXmlBios in new_tree.iter(tag=bios_tag[count]):
        new_knobs_bios_version = nstrip(MyXmlBios.get('VERSION'))
        break

  for ref_setup_knobs in ref_tree.iter(tag='biosknobs'):
    for ref_bios_knob in ref_setup_knobs:
      ref_setup_type = (nstrip(ref_bios_knob.get('setupType'))).upper()
      if ref_setup_type in ['ONEOF', 'CHECKBOX', 'NUMRIC', 'NUMERIC', 'STRING']:
        ref_knob_name = nstrip(ref_bios_knob.get('name'))
        ref_knobs_map[ref_knob_name] = {}
        for current_tag in current_compare_tags:
          if current_tag in internal_compare_tags:
            ref_value = int(nstrip(ref_bios_knob.get(current_tag)), 16)
          else:
            ref_value = nstrip(ref_bios_knob.get(current_tag))
          ref_knobs_map[ref_knob_name][current_tag] = ref_value
  for new_setup_knobs in new_tree.iter(tag='biosknobs'):
    for new_bios_knob in new_setup_knobs:
      current_setup_type = (nstrip(new_bios_knob.get('setupType'))).upper()
      if current_setup_type in ['ONEOF', 'CHECKBOX', 'NUMRIC', 'NUMERIC', 'STRING']:
        new_knob_name = nstrip(new_bios_knob.get('name'))
        new_knobs_map[new_knob_name] = {}
        for current_tag in current_compare_tags:
          if current_tag in internal_compare_tags:
            new_value = int(nstrip(new_bios_knob.get(current_tag)), 16)
          else:
            new_value = nstrip(new_bios_knob.get(current_tag))
          new_knobs_map[new_knob_name][current_tag] = new_value

  file_content = ""
  log_msg = f'\n\nWriting delta knobs for comparing following fields \"{compare_tag}\"\n   RefXmlBiosVer = Arg 1 File = {ref_knobs_bios_version} \n   MyXmlBiosVer = Arg 2 File = {new_knobs_bios_version}\n'
  log.info(log_msg)
  if os.path.splitext(out_file)[-1].lower() not in ['.ini', '.cfg']:
    file_content += log_msg
  else:
    file_content += ';-------------------------------------------------\n; Knob Entries for XmlCli based setup, trying to clone {current_compare_tags[0]} from File 2\n; The name entry here should be identical as the name from the XML file (retain the case)\n;-------------------------------------------------\n[BiosKnobs]\n'
  header_list = ['Knob Name (compare_tag)', 'RefXmlDefVal (Arg 1 File)', 'MyXmlDefVal (Arg 2 File)']
  missing_in_new_knobs = []
  knobs_dictionary=[]
  for knob in ref_knobs_map:
    if knob not in new_knobs_map:
      missing_in_new_knobs.append(knob)
    else:
      print_first_tag = True
      for current_tag in current_compare_tags:
        ref_str_value = ref_knobs_map[knob][current_tag]
        new_str_value = new_knobs_map[knob][current_tag]
        if ref_str_value != new_str_value:
          knobs_dictionary.append([f"{knob} ({current_tag})",ref_str_value,new_str_value])
          if os.path.splitext(out_file)[-1].lower() in ['.ini', '.cfg']:
            if print_first_tag:
              file_content += f'{knob} = {new_str_value}\n'
              print_first_tag = False
      new_knobs_map.pop(knob)
  missing_in_ref_knobs = []
  for knob in new_knobs_map:
    missing_in_ref_knobs.append(knob)
  if os.path.splitext(out_file)[-1].lower() not in ['.ini', '.cfg']:
    file_content += utils.Table().create_table(header=header_list, data=knobs_dictionary, width=0)
  log.result(utils.Table().create_table(header=header_list, data=knobs_dictionary, width=0))
  

  if len(missing_in_ref_knobs) != 0:
    log.info(f'Following Knobs are missing in Arg 1 File\n\t [ {", ".join(missing_in_ref_knobs)} ]')
    if os.path.splitext(out_file)[-1].lower() not in ['.ini', '.cfg']:
      file_content += f'Following Knobs are missing in Arg 1 File\n\t [ {", ".join(missing_in_ref_knobs)} ]\n'
  if len(missing_in_new_knobs) != 0:
    log.info(f'Following Knobs are missing in Arg 2 File\n\t [ {", ".join(missing_in_new_knobs)} ]')
    if os.path.splitext(out_file)[-1].lower() not in ['.ini', '.cfg']:
      file_content += f'Following Knobs are missing in Arg 2 File\n\t [ {", ".join(missing_in_new_knobs)} ]\n'

  with open(out_file, 'w') as out:
    out.write(file_content)

def compare_bios_knobs(reference_bin_file, new_bin_file, result_log_file=r'KnobsDifference.log', compare_tag='default'):
  """Take difference of Setup Option between two BIOS/IFWI

  :param reference_bin_file: reference bios/ifwi binary
  :param new_bin_file: another bios/ifwi binary to compare against reference file
  :param result_log_file: output file location to store difference result at
  :param compare_tag: xml attribute to be compared against (default|CurrentVal|size|prompt|depex|...)
  :return: file content of result_log_file
  """
  reference_xml = clb.KnobsXmlFile.replace('BiosKnobs', 'RefBiosKnobs')
  new_xml = clb.KnobsXmlFile.replace('BiosKnobs', 'MyBiosKnobs')
  cli.savexml(reference_xml, reference_bin_file)
  cli.savexml(new_xml, new_bin_file)
  generate_knobs_delta(reference_xml, new_xml, result_log_file, compare_tag)


def launch_web_gui():
  from xmlcli.modules.webgui import main

  main.run_gui()


if __name__ == "__main__":
  install_context_menu()
