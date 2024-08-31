#!/usr/bin/env python
"""
To generate BiosKnobs.bin file from BiosKnobs.ini and biosKnobs.xml file
"""
__author__ = ['Amol Shinde', 'Gahan Saraiya']

# Built-in Imports
import os
import re
import binascii


# Custom Imports
from .common.logger import log
from . import XmlCliLib as clb

try:
  from defusedxml import ElementTree as ET
except ModuleNotFoundError as e:
  log.warn("Insecure module import used! Please install all the required dependencies by running `pip install -r requirements.txt`")
  from xml.etree import ElementTree as ET

# Global variable
# -------------------

END_OF_BUFFER = 'F4FBD0E9'
XML_TREE = None
mydebug = 1
SIG_FLAG = 0
SETUP_FLAG = 0
SETUP_MAP = {0: {0: 'biosknobs', 1: 'biosknobs'}, 1: {0: 'setupknobs', 1: 'biosknobs'}}
NVAR_MAP = {}
EXIT_ON_UNKNOWN_KNOB = False

MATH_OPERATIONS = {'and', 'or', 'not', '==', '!=', '<=', '>=', '<', '>', '_LIST_'}
DEPEX_RESULT_MAP = {True : {'Sif': 'Active', 'Gif': 'Active', 'Dif': 'Active', '': 'Active'},
                    False: {'Sif': 'Suppressed', 'Gif': 'GrayedOut', 'Dif': 'Disabled', '': 'Unknown'}}
EQUALITY_MAP = {'==': 'in', '!=': 'not in'}


# User defined Function
# -----------------------

def nstrip(input_string, default=''):
  """
  Strip valid input string for spaces.
  If not valid string then returned default null string

  :param input_string: valid input string
  :param default: default empty string ''
  :return: stripped result of input_string or default string
  """
  return input_string.strip() if isinstance(input_string, str) else default


def populate_nvar_map(file_name='biosKnobs.xml'):
  global NVAR_MAP
  global XML_TREE
  if XML_TREE is None:
    XML_TREE = ET.parse(file_name)
  re_nvar = re.compile('Nvar_(.*)_Size')
  offset = 0x100
  nvar_idx = 0
  for setup_knobs in XML_TREE.iter(tag='biosknobs'):
    for knob in setup_knobs:
      setup_type = (nstrip(knob.get('setupType'))).upper()
      if setup_type == 'STRING':
        continue
      name = (nstrip(knob.get('name')))
      default = int((nstrip(knob.get('default'))), 16)
      x1 = re.search(re_nvar, name)
      if setup_type in ['LEGACY']:
        if x1 is not None:
          nvar_idx = int(x1.group(1))
          NVAR_MAP[nvar_idx] = {'NvarSize': default, 'correction': offset}
          offset = offset + NVAR_MAP[nvar_idx]['NvarSize']
  if offset > 0x100:
    nvar_idx = nvar_idx + 1
    NVAR_MAP[nvar_idx] = {'NvarSize': 0x00, 'correction': offset}
  log.info('Nvar value Corrected')


def get_setup_tag(file_name='biosKnobs.xml'):
  global XML_TREE
  global SETUP_MAP
  global SETUP_FLAG
  global SIG_FLAG
  if XML_TREE is None:
    XML_TREE = ET.parse(file_name)
  SIG_FLAG = 0xF
  SETUP_FLAG = 0xF
  for setup_knobs in XML_TREE.iter(tag='biosknobs'):
    SIG_FLAG = 0
    SETUP_FLAG = 0
    for knob in setup_knobs:
      setup_type = (nstrip(knob.get('setupType'))).upper()
      name = (nstrip(knob.get('name')))
      if name in ['Signature']:
        SIG_FLAG = 1
        if setup_type in ['LEGACY']:
          SETUP_FLAG = 1
        break

  if SIG_FLAG == 0xF and SETUP_FLAG == 0xF:
    setup_tag = 'setupknobs'  # this means <biosknobs> tag was not found in the XML
  else:
    setup_tag = SETUP_MAP[SIG_FLAG][SETUP_FLAG]

  if SIG_FLAG == 1 and SETUP_FLAG == 1:
    log.info('Found XML Knobs in Ganges format')
    populate_nvar_map(file_name)  # populate dictionary NVAR_MAP from xml

  return setup_tag


def get_bios_lookup(file_name='biosKnobs.xml', force_parse_xml=False, build_type=None):
  global XML_TREE
  if XML_TREE is None or force_parse_xml:
    XML_TREE = ET.parse(file_name)
  setup_tag = get_setup_tag(file_name)
  bios_map = {}
  for setup_knobs in XML_TREE.iter(tag=setup_tag):
    if setup_knobs.get('BuildType') != build_type:
      continue
    for knob in setup_knobs:
      setup_type = (nstrip(knob.get('setupType'))).upper()
      if setup_type in ['CHECKBOX', 'NUMRIC', 'NUMERIC', 'ONEOF', 'STRING']:
        bios_map[nstrip(knob.get('name'))] = {
          'size'      : nstrip(knob.get('size')), 'offset': nstrip(knob.get('offset')),
          'vstore'    : nstrip(knob.get('varstoreIndex', '0xFF')),
          'CurrentVal': nstrip(knob.get('CurrentVal'))}
      elif setup_type not in ['LEGACY', 'READONLY']:
        log.warning(f'Setup Type is unknown (Need to add this) biosName[{nstrip(knob.get("name"))}] setupType[{setup_type}].')
  return bios_map


def get_cpu_sv_bios_lookup(file_name='biosKnobs.xml'):
  global XML_TREE
  if XML_TREE is None:
    XML_TREE = ET.parse(file_name)
  setup_tag = 'biosknobs'
  bios_map = {}
  offset_map = {}
  for setup_knobs in XML_TREE.iter(tag=setup_tag):
    for knob in setup_knobs:
      knob_type = (nstrip(knob.get('type'))).upper()
      if knob_type in ['SCALAR']:
        if nstrip(knob.get('name')) not in bios_map:
          bios_map[nstrip(knob.get('name'))] = nstrip(knob.get('offset'))
          offset_map[nstrip(knob.get('offset'))] = {
            'name'  : nstrip(knob.get('name')), 'size': nstrip(knob.get('size')),
            'offset': nstrip(knob.get('offset')), 'default': nstrip(knob.get('default'))}
        else:
          log.warning(f'  Warning - Duplicate Knobs : {nstrip(knob.get("name"))} ')
  log.info(f'Lookup Prepared !! len[{str(len(bios_map))}]')
  return bios_map, offset_map


def get_bios_ini(ini_file_name):
  with open(ini_file_name) as f:
    bios_knobs_lis = f.readlines()
  knob_map = {}
  knob_start = 0
  i = 0
  knob_lis = []
  while i < len(bios_knobs_lis):
    line = bios_knobs_lis[i]
    if line.strip() == '[BiosKnobs]':
      knob_start = 1
      i = i + 1
      continue
    elif line.strip() == '[Softstraps]':
      knob_start = 0  # to end BiosKnobs section -Added by Cscripts tool
    if knob_start == 1:
      line = line.split(';')[0]
      if line.strip() != '':
        knob_name, knob_value = line.split('=')
        knob_map[knob_name.strip()] = knob_value.strip()
        knob_lis.append(knob_name.strip())
    i = i + 1
  return knob_map, knob_lis


def offset_correction(knob_offset_hex, knob_vstore_hex):
  knob_offset_hex_format = '0x' + knob_offset_hex
  knob_vstore_hex_format = '0x' + knob_vstore_hex
  global NVAR_MAP
  offset_correction_value = int(knob_offset_hex_format, 16) - NVAR_MAP[int(knob_vstore_hex_format, 16)]['correction']
  offset_correction_format = hex(offset_correction_value)[2:].zfill(4)
  return offset_correction_format


def create_bin_file(bin_file, bios_map, ini_map, knob_lis):
  global SETUP_FLAG, SIG_FLAG, EXIT_ON_UNKNOWN_KNOB
  buffer_lis = []
  has_unknown_knob = False
  for knob in knob_lis:
    if knob in bios_map:
      knob_val_hex = '00'
      knobSize_int = 0
      knob_offset_hex = '0000'
      knob_var_store_hex = '00'
      knob_size_hex = '00'
      knob_val = ini_map[knob]
      knob_size = bios_map[knob]['size']
      knob_offset = bios_map[knob]['offset']
      knob_var_store = bios_map[knob]['vstore']
      a1 = re.search('0x(.*)', knob_val)
      a2 = re.search('L"(.*)"', knob_val)
      a3 = re.search('"(.*)"', knob_val)
      b1 = re.search('0x(.*)', knob_size)
      c1 = re.search('0x(.*)', knob_var_store)
      d1 = re.search('0x(.*)', knob_offset)
      if a1 is not None:
        knob_val_hex = a1.group(1)
      elif a2 is not None:
        j = 0
        data = a2.group(1).strip()[::-1]
        total_str = ''
        while j < len(data):
          each_bit = '00' + clb.HexLiFy(data[j]).zfill(2)
          total_str = total_str + each_bit
          j = j + 1
        knob_val_hex = total_str
      elif a3 is not None:
        knob_val_hex = clb.HexLiFy(a3.group(1).strip()[::-1])
      else:
        if knob_val.isdigit():
          knob_val_hex = hex(int(knob_val))[2:]
        else:
          log.warning(f' Knob [{knob}] value [{knob_val}] is not in proper format')
          continue
      if b1 is not None:
        knob_size_hex = b1.group(1).zfill(2)
        knob_size_int = int('0x' + knob_size_hex, 16)
      else:
        knob_size_hex = hex(int(knob_size))[2:].zfill(2)
        knob_size_int = int(knob_size)
      if c1 is not None:
        knob_var_store_hex = c1.group(1).zfill(2)
      else:
        knob_var_store_hex = hex(int(knob_var_store))[2:].zfill(2)
      if d1 is not None:
        knob_offset_hex = d1.group(1).zfill(4)
        knob_offset_int = int(knob_offset_hex, 16)
      else:
        knob_offset_int = int(knob_offset)
        knob_offset_hex = hex(knob_offset_int)[2:].zfill(4)

      knob_size = knob_size_int
      knob_width = knob_size_int
      if knob_offset_int >= clb.BITWISE_KNOB_PREFIX:  # bitwise knob?
        knob_width, knob_offset_int, bit_offset = clb.get_bitwise_knob_details(knob_size_int, knob_offset_int)
        knob_size_int = ((knob_size_int & 0x1F) << 3) + (bit_offset & 0x7)
      knob_size_hex = hex(knob_size_int)[2:].zfill(2)
      knob_offset_hex = hex(knob_offset_int)[2:].zfill(4)

      if SETUP_FLAG == 1 and SIG_FLAG == 1:
        if int('0x' + knob_var_store_hex, 16) != 0xFF:
          knob_offset_hex = offset_correction(knob_offset_hex, knob_var_store_hex)
      if int(knob_width * 2) < len(knob_val_hex):
        log.warning(f'Value [{knob_val}] of knob [{knob}] is larger in size compared to maximum size for the knob[{knob_size}] mentioned in xml')
        continue
      else:
        knob_val_hex = knob_val_hex.zfill(knob_width * 2)
    else:
      log.warning(f'Bios Knob "{knob}" does not currently exist ')
      has_unknown_knob = True
      continue
    value_line = ''
    tbl_desc_line = []
    inc = knob_width * 2
    while inc > 0:
      tbl_desc_line.append(knob_val_hex[inc - 2:inc])
      inc = inc - 2
    value_line = ''.join(tbl_desc_line)
    binline = knob_var_store_hex.strip() + knob_offset_hex[2:].strip() + knob_offset_hex[0:2].strip() + knob_size_hex.strip() + value_line.strip()
    binline_ascii = binline
    buffer_lis.append(binline_ascii)

  if EXIT_ON_UNKNOWN_KNOB and has_unknown_knob:
    log.error('Aborting Since ExitOnAlienKnob was set, see above for details. ')
    return ''

  total_entries = hex(len(buffer_lis))[2:].zfill(8)
  inc = 8
  entries_line = []
  while inc > 0:
    entries_line.append(total_entries[inc - 2:inc])
    inc = inc - 2
  entry_line = ''.join(entries_line)
  buffer_str = entry_line + ''.join(buffer_lis) + END_OF_BUFFER
  request_buffer = binascii.unhexlify(buffer_str)
  with open(bin_file, 'wb') as out_bin:
    out_bin.write(request_buffer)
  return request_buffer


def value_to_hex(val):
  val_hex = ''
  a1 = re.search('0x(.*)', val)
  a2 = re.search('L"(.*)"', val)
  a3 = re.search('"(.*)"', val)
  if a1 is not None:
    val_hex = a1.group(1)
  elif a2 is not None:
    j = 0
    data = a2.group(1)
    total_str = ''
    while j < len(data):
      each_bit = clb.HexLiFy(data[j]).zfill(4) + ' '
      total_str = total_str + each_bit
      j = j + 1
    val_hex = total_str

  elif a3 is not None:
    val_hex = clb.HexLiFy(a3.group(1))
  else:
    if val.isdigit():
      val_hex = hex(int(val))[2:]
  val_hex = '0x' + val_hex
  return val_hex


def parse_cli_ini_xml(file_name, ini_file, bin_file='bios.bin', build_type=None):
  global XML_TREE
  XML_TREE = None
  bios_map = get_bios_lookup(file_name, build_type=build_type)
  ini_map, knob_lis = get_bios_ini(ini_file)
  return create_bin_file(bin_file, bios_map, ini_map, knob_lis)


def generate_csv(xml_file, por_default_review=False):
  global XML_TREE
  duplicateKnobs = []
  invalidOption = {}
  nullUQI = []
  unknown_setup_type = []
  knobList = {}
  XML_TREE = None
  if XML_TREE is None:
    XML_TREE = ET.parse(xml_file)

  _bios_version = ''
  for version in XML_TREE.iter(tag='BIOS'):
    _bios_version = version.get('VERSION')
  if _bios_version == '':
    for version in XML_TREE.iter(tag='SVBIOS'):
      _bios_version = version.get('VERSION')
  if _bios_version == '':
    for version in XML_TREE.iter(tag='CPUSVBIOS'):
      _bios_version = version.get('VERSION')

  log.info(f'\nBIOS XML is of VERSION [{_bios_version}]')
  csv_data = ""
  if por_default_review:
    csv_data += 'Name,Description,Grouping,Type,Size(Bytes),Selection [Value],DefaultVal,SetupPagePtr,Depex\n'
  else:
    csv_data += 'Name,Description,Type,Size(Bytes),Selection [Value],DefaultVal,CurrentVal,SetupPagePtr,Depex\n'
  for setup_knobs in XML_TREE.iter(tag='biosknobs'):
    for knob in setup_knobs:
      sel_str = '\"'
      setup_type = (nstrip(knob.get('setupType'))).upper()
      if setup_type == 'ONEOF':
        for options in knob:
          for option in options:
            sel_str += f'{nstrip(option.get("text"))} [{nstrip(option.get("value"))}]\n'
        if sel_str[len(sel_str) - 1] == '\n':
          sel_str = sel_str[0:(len(sel_str) - 1)]
      elif setup_type in ['NUMRIC', 'NUMERIC']:
        sel_str += f'{"min"} [{nstrip(knob.get("min"))}]\n{"max"} [{nstrip(knob.get("max"))}]'
      elif setup_type == 'STRING':
        sel_str += f'{"minsize"} [{nstrip(knob.get("minsize"))}]\n{"maxsize"} [{nstrip(knob.get("maxsize"))}]'
      elif setup_type in ['CHECKBOX']:
        sel_str += f'{"UnChecked"} [{"0"}]\n{"Checked"} [{"1"}]'
      else:
        log.warning(f'Setup Type is unknown for biosName[{nstrip(knob.get("name"))}] setupType[{setup_type}]. ')
        unknown_setup_type.append(setup_type)
      sel_str = sel_str + '\"'
      if setup_type in ['ONEOF', 'CHECKBOX', 'NUMRIC', 'NUMERIC', 'STRING']:
        if por_default_review:
          csv_data += f'{nstrip(knob.get("name"))},{nstrip(knob.get("prompt")).replace(",", ";")}: {nstrip(knob.get("description")).replace(",", ";")},{nstrip(knob.get("Nvar"))},{setup_type},{nstrip(knob.get("size"))},{sel_str},{nstrip(knob.get("default"))},{nstrip(knob.get("SetupPgPtr"))},{nstrip(knob.get("depex"))}\n'
        else:
          csv_data += f'{nstrip(knob.get("name"))},{nstrip(knob.get("prompt")).replace(",", ";")}: {nstrip(knob.get("description")).replace(",", ";")},{setup_type},{nstrip(knob.get("size"))},{sel_str},{nstrip(knob.get("default"))},{nstrip(knob.get("CurrentVal"))},{nstrip(knob.get("SetupPgPtr"))},{nstrip(knob.get("depex"))}\n'

  csv_file_name = f'{_bios_version.replace(".", "_")}_KnobsData.csv'
  csv_file = os.path.join(clb.TempFolder, csv_file_name)
  with open(csv_file, 'w') as file_ptr:
    log.info(f'writing to file : {csv_file}')
    file_ptr.write(csv_data)
  log.info('Csv File generated !')


def generate_bios_knobs_config(xml_file, flexcon_cfg_file, knobs_ini_file, build_type=None):
  tree = ET.parse(xml_file)
  bios_knobs_map = {}
  for setup_knobs in tree.iter(tag='biosknobs'):
    if setup_knobs.get('BuildType') != build_type:
      continue
    for knob in setup_knobs:
      setup_type = (nstrip(knob.get('setupType'))).upper()
      knob_name = nstrip(knob.get('name'))
      bios_knobs_map[knob_name] = {}
      bios_knobs_map[knob_name]['$SetUpType'] = setup_type
      if setup_type == 'ONEOF':
        for options in knob:
          for option in options:
            bios_knobs_map[knob_name][nstrip(option.get('text'))] = nstrip(option.get('value'))
  with open(flexcon_cfg_file, "r") as f:
    bios_knobs_lis = f.readlines()
  knob_start = 0
  i = 0
  ini_content = ';-------------------------------------------------\n'
  '; BIOS contact: xmlcli_mod@intel.com\n'
  '; XML Shared MailBox settings for BIOS CLI based setup\n'
  '; The name entry here should be identical as the name from the XML file (retain the case)\n'
  ';-------------------------------------------------\n'
  '[BiosKnobs]\n'
  while i < len(bios_knobs_lis):
    line = bios_knobs_lis[i].strip()
    if (line == '[BIOS Overrides]') or (line == '[BiosKnobs]'):
      knob_start = 1
      i = i + 1
      continue
    if knob_start == 1:
      knob_name = ''
      knob_value = ''
      line = line.split(';')[0]
      if line != '':
        if line[0] == '[':
          if line[-1] == ']':
            break
        knob_name = line.split('=')[0].strip()
        knob_value = line.split('=')[1].strip()
        if knob_name not in bios_knobs_map:
          log.warning(f'Bios Knob \"{knob_name}\" does not currently exist ')
          i = i + 1
          continue
        if bios_knobs_map[knob_name]['$SetUpType'] == 'ONEOF':
          if knob_value in ['Enabled', 'Enable']:
            try:
              ini_content += f'{knob_name} = {bios_knobs_map[knob_name]["Enabled"]} \n'
              i = i + 1
              continue
            except:
              try:
                ini_content += f'{knob_name} = {bios_knobs_map[knob_name]["Enable"]} \n'
                i = i + 1
                continue
              except:
                log.warning(f'InCorrect Knob Value for Bios Knob \"{knob_name}\"')
          elif knob_value in ['Disabled', 'Disable']:
            try:
              ini_content += f'{knob_name} = {bios_knobs_map[knob_name]["Disabled"]} \n'
              i = i + 1
              continue
            except:
              try:
                ini_content += f'{knob_name} = {bios_knobs_map[knob_name]["Disable"]} \n'
                i = i + 1
                continue
              except:
                log.warning(f'InCorrect Knob Value for Bios Knob \"{knob_name}\"')
          else:
            try:
              ini_content += f'{knob_name} = {bios_knobs_map[knob_name][knob_value]} \n'
            except:
              log.warning(f'InCorrect Knob Value for Bios Knob \"{knob_name}\"')
        if bios_knobs_map[knob_name]['$SetUpType'] == 'CHECKBOX':
          if knob_value == 'Checked':
            ini_content += f'{knob_name} = {1:d} \n'
          if knob_value == 'Unchecked':
            ini_content += f'{knob_name} = {0:d} \n'
        if (bios_knobs_map[knob_name]['$SetUpType'] == 'NUMRIC') or (bios_knobs_map[knob_name]['$SetUpType'] == 'NUMERIC'):
          ini_content += f'{line}\n'
    i = i + 1
  with open(knobs_ini_file, 'w') as out_ini:
    out_ini.write(ini_content)


def generate_bios_config_ini(xml_file, bios_config_file, knobs_ini_file='', mode='genbiosconf', knobs_map={}):
  tree = ET.parse(xml_file)
  bios_knobs_map = {}
  knob_count = 0
  xml_map = {}
  KnobComments = {}
  knob_start = False
  comment = ''
  comment_map = {}
  for line in open(xml_file, 'r').readlines():
    line = line.strip()
    if line == '':
      continue
    match = re.search(r'\s*\<biosknobs\>\s*', line)
    if match != None:
      knob_start = True
    match = re.search(r'\s*\<\/biosknobs\>\s*', line)
    if match != None:
      knob_start = False
    if knob_start:
      match = re.search(r'\s*\<!--\s*(.*?)\s*--\>\s*', line)
      if match != None:
        comment = comment + '// ' + match.group(1) + '\n'
      match = re.search(r'\s*\<knob\s*(.*?)\s*name=\"(\S*)\"\s*', line)
      if match != None:
        comment_map[match.group(2)] = comment
        comment = ''
  for setup_knobs in tree.iter(tag='biosknobs'):
    for knob in setup_knobs:
      bios_knobs_map[knob_count] = {}
      setup_type = (nstrip(knob.get('setupType'))).upper()
      bios_knobs_map[knob_count]['$KnobName'] = nstrip(knob.get('name'))
      bios_knobs_map[knob_count]['$SetUpType'] = setup_type
      bios_knobs_map[knob_count]['$Prompt'] = nstrip(knob.get('prompt'))
      bios_knobs_map[knob_count]['$KnobSize'] = value_to_hex(nstrip(knob.get('size')))
      bios_knobs_map[knob_count]['$DupUqi'] = False
      knob_uqi_val = nstrip(knob.get('UqiVal'))
      bios_knobs_map[knob_count]['$KnobUqi'] = knob_uqi_val
      if xml_map.get(knob_uqi_val, -1) == -1:
        xml_map[knob_uqi_val] = knob_count
      else:
        bios_knobs_map[knob_count]['$DupUqi'] = True
      if setup_type == 'STRING':
        bios_knobs_map[knob_count]['$CurVal'] = knob.get('CurrentVal')
        bios_knobs_map[knob_count]['$DefVal'] = knob.get('default')
      else:
        bios_knobs_map[knob_count]['$CurVal'] = value_to_hex(nstrip(knob.get('CurrentVal')))
        bios_knobs_map[knob_count]['$DefVal'] = value_to_hex(nstrip(knob.get('default')))
      bios_knobs_map[knob_count]['OptionsDict'] = {}
      if setup_type == 'ONEOF':
        options_count = 0
        for options in knob:
          for option in options:
            bios_knobs_map[knob_count]['OptionsDict'][options_count] = {
              'OptionText': nstrip(option.get('text')), 'OptionVal': value_to_hex(nstrip(option.get('value')))}
            options_count = options_count + 1
      elif setup_type in ['NUMRIC', 'NUMERIC', 'STRING']:
        bios_knobs_map[knob_count]['OptionsDict'][0] = {
          'OptionText': 'Minimum', 'OptionVal': value_to_hex(nstrip(knob.get('min')))}
        bios_knobs_map[knob_count]['OptionsDict'][1] = {
          'OptionText': 'Maximum', 'OptionVal': value_to_hex(nstrip(knob.get('max')))}
        bios_knobs_map[knob_count]['OptionsDict'][2] = {
          'OptionText': 'Step', 'OptionVal': value_to_hex(nstrip(knob.get('step')))}
      elif setup_type in ['CHECKBOX']:
        bios_knobs_map[knob_count]['OptionsDict'][0] = {
          'OptionText': 'Unchecked', 'OptionVal': '0x00'}
        bios_knobs_map[knob_count]['OptionsDict'][1] = {
          'OptionText': 'Checked', 'OptionVal': '0x01'}
      knob_count = knob_count + 1
  if (mode.lower() == 'genbiosconf') or (mode.lower() == 'genbiosconfdef'):
    txt_file_content = '// This File was generate from XmlCli\'s Bios Knobs XML File\n\n'
    for knob_count in range(0, len(bios_knobs_map)):
      if bios_knobs_map[knob_count]['$DupUqi']:
        log.warning(f'Duplicate uqi for Knob ({bios_knobs_map[knob_count]["$KnobName"]}), ignore this entry')
        continue
      temp_uqi = (clb.HexLiFy(bios_knobs_map[knob_count]['$KnobUqi'])).upper()
      setup_type = bios_knobs_map[knob_count]['$SetUpType'].upper()
      size = int(bios_knobs_map[knob_count]['$KnobSize'], 16)
      if mode.lower() == 'genbiosconfdef':
        value_str = bios_knobs_map[knob_count]['$DefVal']
      else:
        value_str = bios_knobs_map[knob_count]['$CurVal']
      if setup_type == 'STRING':
        if value_str[0:2] == '0x':
          temp_str = ''
          for count in range(0, (len(value_str) - 2), 4):
            if value_str[count + 2: count + 6] != '0000':
              temp_str = temp_str + chr(value_str[count + 2: count + 6])
          value_str = temp_str[::-1]
      else:
        value_str = value_str[2:].zfill(size * 2)
      if comment_map.get(bios_knobs_map[knob_count]['$KnobName'], '') != '':
        txt_file_content += f'\n{comment_map[bios_knobs_map[knob_count]["$KnobName"]]}'
      if setup_type == 'ONEOF':
        setup_type = 'ONE_OF'
      if bios_knobs_map[knob_count]['$KnobUqi'] == '':
        txt_file_content += f'\n// [No UQI] {setup_type} {value_str} // {bios_knobs_map[knob_count]["$Prompt"]}\n'
      else:
        txt_file_content += f'\nQ 0006 00{temp_uqi[0:2]} 00{temp_uqi[2:4]} 00{temp_uqi[4:6]} 00{temp_uqi[6:8]} 00{temp_uqi[8:10]} 00{temp_uqi[10:12]} {setup_type} {value_str} // {bios_knobs_map[knob_count]["$Prompt"]}\n'
      if setup_type != 'STRING':
        for OptionCount in range(0, len(bios_knobs_map[knob_count]['OptionsDict'])):
          if setup_type == 'NUMERIC':
            txt_file_content += f'// {bios_knobs_map[knob_count]["OptionsDict"][OptionCount]["OptionText"].ljust(7)} = {bios_knobs_map[knob_count]["OptionsDict"][OptionCount]["OptionVal"][2:].zfill(size * 2)}\n'
          else:
            txt_file_content += f'// {bios_knobs_map[knob_count]["OptionsDict"][OptionCount]["OptionVal"][2:].zfill(size * 2)} = {bios_knobs_map[knob_count]["OptionsDict"][OptionCount]["OptionText"]}\n'
    with open(bios_config_file, 'w') as out_txt_file:
      out_txt_file.write(txt_file_content)
  if mode.lower() == 'genknobsini':
    log.info('Generating BiosKnobs.ini file from BiosConf Text File, will be writing only delta knobs')
    ini_content = ';-------------------------------------------------\n'
    '; BIOS contact: xmlcli_mod@intel.com\n'
    '; XML Shared MailBox settings for BIOS CLI based setup\n'
    '; The name entry here should be identical as the name from the XML file (retain the case)\n'
    ';-------------------------------------------------\n'
    '[BiosKnobs]\n'
    uqi_map = {}
    uqi_count = 0
    for line in open(bios_config_file, 'r').readlines():
      line = line.split('//')[0].strip()
      if line == '':
        continue
      match = re.search(r'\s*Q\s*0006\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*', line)
      if match != None:
        current_uqi_val = binascii.unhexlify(match.group(1))[1] + binascii.unhexlify(match.group(2))[1] + binascii.unhexlify(match.group(3))[1] + \
                          binascii.unhexlify(match.group(4))[1] + binascii.unhexlify(match.group(5))[1] + binascii.unhexlify(match.group(6))[1]
        current_value = match.group(8)
        uqi_map[uqi_count] = {'UqiVal': current_uqi_val, 'KnobVal': current_value}
        knob_count = xml_map[current_uqi_val]
        if uqi_map[uqi_count]['UqiVal'] == bios_knobs_map[knob_count]['$KnobUqi']:
          setup_type = bios_knobs_map[knob_count]['$SetUpType'].upper()
          temp_uqi = (clb.HexLiFy(bios_knobs_map[knob_count]['$KnobUqi'])).upper()
          size = int(bios_knobs_map[knob_count]['$KnobSize'], 16)
          if setup_type == 'STRING':
            if uqi_map[uqi_count]['KnobVal'] != bios_knobs_map[knob_count]['$CurVal']:
              ini_content += f'{bios_knobs_map[knob_count]["$KnobName"]} = L\"{uqi_map[uqi_count]["KnobVal"]}\"    ; Q 0006 00{temp_uqi[0:2]} 00{temp_uqi[2:4]} 00{temp_uqi[4:6]} 00{temp_uqi[6:8]} 00{temp_uqi[8:10]} 00{temp_uqi[10:12]} {setup_type} {uqi_map[uqi_count]["KnobVal"]} // {bios_knobs_map[knob_count]["$Prompt"]}\n'
          else:
            if int(uqi_map[uqi_count]['KnobVal'], 16) != int(bios_knobs_map[knob_count]['$CurVal'], 16):
              ini_content += f'{bios_knobs_map[knob_count]["$KnobName"]} = 0x{int(uqi_map[uqi_count]["KnobVal"], 16):X}    ; Q 0006 00{temp_uqi[0:2]} 00{temp_uqi[2:4]} 00{temp_uqi[4:6]} 00{temp_uqi[6:8]} 00{temp_uqi[8:10]} 00{temp_uqi[10:12]} {setup_type} {hex(int(uqi_map[uqi_count]["KnobVal"], 16))[2:].zfill(size * 2)} // {bios_knobs_map[knob_count]["$Prompt"]}\n'
        uqi_count = uqi_count + 1
    with open(knobs_ini_file, 'w') as out_ini:
      out_ini.write(ini_content)
  if mode.lower() == 'inituqi':
    for KnobsDictCount in range(0, len(knobs_map)):
      for BiosKnobsDictCount in range(0, len(bios_knobs_map)):
        if knobs_map[KnobsDictCount]['KnobName'] == bios_knobs_map[BiosKnobsDictCount]['$KnobName']:
          if int(knobs_map[KnobsDictCount]['Size'], 16) == bios_knobs_map[BiosKnobsDictCount]['$KnobSize']:
            knobs_map[KnobsDictCount]['Prompt'] = bios_knobs_map[BiosKnobsDictCount]['$Prompt']
            knobs_map[KnobsDictCount]['UqiVal'] = bios_knobs_map[BiosKnobsDictCount]['$KnobUqi']


def generate_all_knobs_ini(xml_file, all_knobs_ini):
  """
  Generate bios knobs config file consisting of all setup options with their
  default value from given xml file

  :param xml_file: xml file to generate all knobs
  :param all_knobs_ini: output file at which all knobs will be stored
  :return:
  """
  xml_tree = ET.parse(xml_file)
  ini_content = ';-------------------------------------------------\n'
  '; BIOS contact: xmlcli_mod@intel.com\n'
  '; XML Shared MailBox settings for BIOS CLI based setup\n'
  '; The name entry here should be identical as the name from the XML file (retain the case)\n'
  ';-------------------------------------------------\n'
  '[BiosKnobs]\n'
  for setup_knobs in xml_tree.iter(tag='biosknobs'):
    for ref_bios_knob in setup_knobs:
      ref_setup_type = (nstrip(ref_bios_knob.get('setupType'))).upper()
      size = int(str_to_hex(nstrip(ref_bios_knob.get('size'))), 16)
      if ref_setup_type in ['ONEOF', 'CHECKBOX', 'NUMRIC', 'NUMERIC', 'STRING']:
        default_value = int(nstrip(ref_bios_knob.get('default')), 16)
        knob_name = nstrip(ref_bios_knob.get('name'))
        if default_value:
          new_value = 0
        else:
          new_value = 1
        if ref_setup_type == 'STRING':
          ini_content += f'{knob_name} = L\"{"IntelSrrBangaloreKarnatakaIndiaAsia"[0:((size // 2) - 1)]}\" \n'
        else:
          ini_content += f'{knob_name} = {new_value:d} \n'
  with open(all_knobs_ini, 'w') as out_ini:
    out_ini.write(ini_content)


def find_duplicates(xml_file):
  """
  Find duplicate setup knobs from given xml file

  :param xml_file: platform config xml file
  :return: list of duplicate setup knob(s) if any else empty list
  """
  xml_tree = None
  xml_tree = ET.parse(xml_file)
  knob_name_lis = []
  duplicate_knobs = []
  for setup_knobs in xml_tree.iter(tag='biosknobs'):
    for ref_bios_knob in setup_knobs:
      knob_name = nstrip(ref_bios_knob.get('name'))
      if knob_name in knob_name_lis:
        if knob_name not in duplicate_knobs:
          duplicate_knobs.append(knob_name)
      else:
        knob_name_lis.append(knob_name)
  if len(duplicate_knobs) != 0:
    log.error(f'Following knobs are duplicates \n [{",".join(duplicate_knobs)}]')
  else:
    log.debug('No duplicates found in the given XML')
  return duplicate_knobs


def xml_to_knob_map(xml_file, knob_map={}, operation='normal'):
  """
  Generate dictionary map for bios setup knobs from given xml file

  :param xml_file: platform config xml file
  :param knob_map: Map of setup knob and corresponding value
  :param operation: operation to perform -> `restore` or `normal`
  :return: tuple of 2 dictionary map consists result values knob map
      and non empty dictionary of old values in case of `restore` operation
  """
  xml_tree = None
  xml_tree = ET.parse(xml_file)
  result_knob_map = {}
  previous_value_map = {}
  for setup_knobs in xml_tree.iter(tag='biosknobs'):
    for ref_bios_knob in setup_knobs:
      knob_name = nstrip(ref_bios_knob.get('name'))
      var_store_idx = clb.Str2Int(ref_bios_knob.get('varstoreIndex'))
      if operation == 'restore':
        if knob_name in knob_map:
          result_knob_map[knob_name] = knob_map[knob_name]
        else:
          default_value = nstrip(ref_bios_knob.get('default'))
          current_value = nstrip(ref_bios_knob.get('CurrentVal'))
          if default_value != current_value:
            result_knob_map[knob_name] = default_value
            previous_value_map[knob_name] = current_value
      else:
        if knob_name in knob_map:
          knob_setup_type = nstrip(ref_bios_knob.get('setupType'))
          size = clb.Str2Int(ref_bios_knob.get('size'))
          offset = clb.Str2Int(ref_bios_knob.get('offset'))
          default_value = clb.Str2Int(ref_bios_knob.get('default'))
          current_value = clb.Str2Int(ref_bios_knob.get('CurrentVal'))
          result_knob_map[knob_name] = {
            'ReqVal': clb.Str2Int(knob_map[knob_name]), 'Type': knob_setup_type,
            'VarId' : var_store_idx, 'CurVal': current_value, 'DefVal': default_value,
            'Size'  : size, 'Offset': offset
          }
  return result_knob_map, previous_value_map


def str_to_hex(value):
  """
  Convert given string value to hex

  :param value: string value
  :return: hex representation of input string value
  """
  val_hex = ''
  a1 = re.search('0x(.*)', value)
  a2 = re.search('L"(.*)"', value)
  a3 = re.search('"(.*)"', value)
  if a1 is not None:
    val_hex = hex(int(a1.group(1), 16))[2:].strip('L')
  elif a2 is not None:
    data = a2.group(1)
    for count in range(0, len(data)):
      val_hex = val_hex + clb.HexLiFy(data[count]).ljust(4, '0')
  elif a3 is not None:
    val_hex = clb.HexLiFy(a3.group(1))
  else:
    if value.isdigit():
      val_hex = hex(int(value))[2:]
  return val_hex


def little_endian(hex_val):
  """
  Convert hex value in to equivalent little endian format

  :param hex_val: input hex value which is represented as string
  :return: little endian string of given hex value
  """
  result = ''
  for count in range(0, len(hex_val), 2):
    result = hex_val[count:count + 2] + result
  return result


def generate_knobs_data_bin(xml_file, knobs_ini_file, bin_file, operation='Prog'):
  """
  Generate BIOS knobs data binary

  :param xml_file: platform config xml file
  :param knobs_ini_file: bios config file consists of `<knob-name>=<value>`
  :param bin_file: output binary file location
  :param operation: Operation to perform -> Prog | LoadDef | ResMod
  :return: tuple of 2 values -> (dictionary of buffer map, buffer value string)
  """
  tree = ET.parse(xml_file)
  bios_knobs_map = {}
  delta_map = {}
  for setup_knobs in tree.iter(tag='biosknobs'):
    for knob in setup_knobs:
      knob_name = nstrip(knob.get('name'))
      setup_type = (nstrip(knob.get('setupType'))).upper()
      offset = nstrip(knob.get('offset'))
      size = nstrip(knob.get('size'))
      var_store_idx = nstrip(knob.get('varstoreIndex'))
      default_val = nstrip(knob.get('default'))
      current_value = nstrip(knob.get('CurrentVal'))
      bios_knobs_map[knob_name] = {'VarId': var_store_idx, 'Type': setup_type, 'Size': size, 'offset': offset, 'DefVal': default_val, 'CurVal': current_value}
      if default_val != current_value:
        delta_map[knob_name] = default_val
  request_knob_map = {}
  if operation != 'LoadDef':
    knob_start = 0
    for line in open(knobs_ini_file, 'r').readlines():
      line = line.split(';')[0]
      line = line.strip()
      if line == '':
        continue
      if line == '[BiosKnobs]':
        knob_start = 1
        continue
      if knob_start:
        name = line.split('=')[0].strip()
        request_knob_map[name] = line.split('=')[1].strip()
    if operation == 'ResMod':
      for knob_name in delta_map:
        if knob_name not in request_knob_map:
          request_knob_map[knob_name] = delta_map[knob_name]
  else:
    request_knob_map = delta_map
  buffer_map = {}
  for name in request_knob_map:
    try:
      var_store = bios_knobs_map[name]['VarId']
      offset = bios_knobs_map[name]['offset']
      knob_offset = str_to_hex(offset)
      size = int(str_to_hex(bios_knobs_map[name]['Size']), 16)
      knob_width = size
      var_store_idx = int(str_to_hex(var_store), 16)
      if knob_offset >= clb.BITWISE_KNOB_PREFIX:  # bitwise knob?
        knob_width, knob_offset, bit_offset = clb.get_bitwise_knob_details(size, knob_offset)
        size = ((size & 0x1F) << 3) + (bit_offset & 0x7)  # Embed Bit Offset 7 Bit size info in size variable
    except:
      log.warning(f'Knob name \"{name}\" not found in XML, Skipping')
      continue
    if bios_knobs_map[name]['Type'] == 'STRING':
      request_val_str = str_to_hex(request_knob_map[name]).ljust(knob_width * 2, '0')
    else:
      request_val_str = little_endian(str_to_hex(request_knob_map[name]).zfill(knob_width * 2))
    if len(request_val_str) > (knob_width * 2):
      log.warning(f'Requested Knob \"{name}\" Value exceeds the allowed size limit({(knob_width / 2):d} chars), Ignoring this entry')
      continue
    try:
      len(buffer_map[var_store_idx])
    except:
      buffer_map[var_store_idx] = {}
    buffer_map[var_store_idx][len(buffer_map[var_store_idx])] = str_to_hex(var_store).zfill(2) + little_endian(str_to_hex(offset).zfill(4)) + str_to_hex(size).zfill(2) + request_val_str
  knob_buffer_str = ''
  if len(buffer_map):
    knob_count = 0
    for Index in buffer_map:
      current_buffer_str = ''
      for count in range(0, len(buffer_map[Index])):
        current_buffer_str = current_buffer_str + buffer_map[Index][count]
        knob_count = knob_count + 1
      if current_buffer_str != '':
        current_bin_buffer_str = (little_endian(str_to_hex(hex(len(buffer_map[Index]))).zfill(8)) + current_buffer_str + END_OF_BUFFER).upper()
        new_var_bin_file = os.path.join(clb.TempFolder, f'biosKnobsdata_{Index:d}.bin')
        with open(new_var_bin_file, 'wb') as file_ptr:
          file_ptr.write(binascii.unhexlify(current_bin_buffer_str))
      knob_buffer_str = knob_buffer_str + current_buffer_str
    knob_buffer_str = f"{little_endian(str_to_hex(hex(knob_count)).zfill(8))}{knob_buffer_str}{END_OF_BUFFER}".upper()
    with open(bin_file, 'wb') as file_ptr:
      file_ptr.write(binascii.unhexlify(knob_buffer_str))
  return buffer_map, knob_buffer_str

def evaluate_depex(depex, knob_name, knobs_value_map):
  """
  Evaluate dependency expression `depex`
  :param depex: Dependency Expression
  :param knob_name: Name of bios setup knob
  :param knobs_value_map: dictionary of bios knob and corresponding value
  :return:
  """
  overall_operation = ''
  overall_result = True
  main_exp = depex.replace('_EQU_', '==').replace('_NEQ_', '!=').replace('_LTE_', '<=').replace('_GTE_', '>=').replace('_LT_', '<').replace(
    '_GT_', '>'
    ).replace(
    ' AND ', ' and '
    ).replace(' OR ', ' or ').strip()
  exp_array = main_exp.split('_AND_')
  for count in range(0, len(exp_array), 1):
    operation = ''
    if exp_array[count].strip() == 'TRUE':
      continue
    match = re.search(r'\s*(Sif|Gif|Dif)\s*\((.*)\)\s*', exp_array[count])
    if match != None:
      operation = match.group(1).strip()
      sub_expression = '( ' + match.group(2).strip() + ' )'
    else:
      match = re.search(r'\s*\((.*?)\)\s*', exp_array[count])
      if match != None:
        sub_expression = '( ' + match.group(1).strip() + ' )'
      else:
        log.warning(f'skipping this ({knob_name}) iteration')
        continue
    for mat1 in re.finditer(r'\s*(\w+)\s', sub_expression):
      variable = mat1.group(1).strip()
      if variable not in MATH_OPERATIONS:
        try:
          int(variable, 16)
          continue
        except:
          pass
        if variable in knobs_value_map:
          sub_expression = sub_expression.replace(' ' + variable + ' ', ' ' + knobs_value_map[variable]['CurVal'] + ' ')
    match = re.search(r'\s*_LIST_\s*(.*?)\s*(==|!=)\s*(.*?)\s*(\)|or|and|not)\s*', sub_expression)
    if match != None:
      sub_expression = '( ' + match.group(1).strip() + ' ' + EQUALITY_MAP[match.group(2).strip()] + ' [%s] )' % re.sub(r'\s\s*', ', ', match.group(3).strip())
    sub_expression = sub_expression.replace('OR', 'or')
    sub_expression = sub_expression.replace('AND', 'and')
    try:
      result = eval(sub_expression)
      if operation in ['Gif', 'Sif', 'Dif']:
        result = not result
    except Exception as ex:
      log.error(f'{ex}')
      result = True
    if result == False:
      overall_operation = operation
      overall_result = result
      if operation in ['Sif', 'Dif']:
        break
  status = DEPEX_RESULT_MAP[overall_result][overall_operation]
  return status


def eval_knob_depex(xml_file=0, bios_knobs_map=0, csv_file=0):
  """
  Evaluate knob's dependency expression (depex)

  :param xml_file: platform config xml file
  :param bios_knobs_map:
  :param csv_file:
  :return:
  """
  if bios_knobs_map == 0:
    bios_knobs_map = {}
  bios_knobs_lis = {}
  if (len(bios_knobs_map) == 0) and (xml_file != 0):
    tree = ET.parse(xml_file)
    knob_idx = 0
    log.info(f'Parsing Xml File {xml_file}')
    for setup_knobs in tree.iter(tag='biosknobs'):
      for knob in setup_knobs:
        setup_type = knob.get('setupType').strip().upper()
        knob_name = knob.get('name').strip()
        current_value = knob.get('CurrentVal').strip()
        default_val = knob.get('default').strip()
        depex = 'TRUE'
        setup_page_ptr = 'N.A.'
        prompt = ''
        _help = ''
        options_map = {}
        if setup_type in ['ONEOF', 'CHECKBOX', 'NUMRIC', 'NUMERIC', 'STRING']:
          depex = knob.get('depex').strip()
          prompt = knob.get('prompt').strip()
          _help = knob.get('description').strip()
          if setup_type == 'ONEOF':
            options_count = 0
            for options in knob:
              for option in options:
                options_map[options_count] = {'Text': nstrip(option.get('text')), 'Val': value_to_hex(nstrip(option.get('value')))}
                options_count = options_count + 1
          elif setup_type in ['NUMRIC', 'NUMERIC']:
            options_map[0] = {'Text': 'Min', 'Val': int(value_to_hex(nstrip(knob.get('min'))), 16)}
            options_map[1] = {'Text': 'Max', 'Val': int(value_to_hex(nstrip(knob.get('max'))), 16)}
            options_map[2] = {'Text': 'Step', 'Val': int(value_to_hex(nstrip(knob.get('step'))), 16)}
          elif setup_type == 'STRING':
            options_map[0] = {'Text': 'Min', 'Val': int(value_to_hex(nstrip(knob.get('minsize'))), 16)}
            options_map[1] = {'Text': 'Max', 'Val': int(value_to_hex(nstrip(knob.get('maxsize'))), 16)}
            options_map[2] = {'Text': 'Step', 'Val': 0x01}
          try:
            setup_page_ptr = knob.get('SetupPgPtr').strip()
          except:
            pass
        bios_knobs_lis[knob_idx] = knob_name
        knob_idx = knob_idx + 1
        if knob_name[0:4] == 'Nvar':
          temp_name = knob_name[6::]
          if temp_name not in bios_knobs_map:
            bios_knobs_map[temp_name] = {
              'SetupType' : setup_type, 'CurVal': current_value,
              'DefVal': default_val, 'Depex': depex, 'SetupPgPtr': setup_page_ptr,
              'SetupPgSts': 'Unknown', 'Prompt': prompt, 'Help': _help, 'OptionsDict': options_map}
        bios_knobs_map[knob_name] = {'SetupType' : setup_type, 'CurVal': current_value, 'DefVal': default_val, 'Depex': depex, 'SetupPgPtr': setup_page_ptr,
                                     'SetupPgSts': 'Unknown', 'Prompt': prompt, 'Help': _help, 'OptionsDict': options_map}
  else:
    log.warning('Skipped Parsing Xml, will directly operate & update the Knobs Dict that was passed as an Arg')
  for Knob in bios_knobs_map:
    if bios_knobs_map[Knob]['SetupType'] == 'READONLY':
      continue
    if bios_knobs_map[Knob]['SetupPgPtr'][0:4] == '???/':
      bios_knobs_map[Knob]['SetupPgSts'] = 'Disabled'
    else:
      bios_knobs_map[Knob]['SetupPgSts'] = evaluate_depex(bios_knobs_map[Knob]['Depex'], Knob, bios_knobs_map)
  if (csv_file != 0) and (xml_file != 0) and (len(bios_knobs_lis) != 0):
    with open(csv_file, 'w') as csv_file_ptr:
      csv_file_ptr.write('Name,SetupPgSts,SetupPgPtr,Depex\n')
      for Index in range(0, len(bios_knobs_lis), 1):
        csv_file_ptr.write(f'{bios_knobs_lis[Index]},{bios_knobs_map[bios_knobs_lis[Index]]["SetupPgSts"]},\"{bios_knobs_map[bios_knobs_lis[Index]]["SetupPgPtr"]}\",{bios_knobs_map[bios_knobs_lis[Index]]["Depex"]}\n')
      csv_file_ptr.close()
    log.info(f'generated csv file {csv_file} ')
  return 0
