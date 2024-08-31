#!/usr/bin/env python
__author__ = ["Gahan Saraiya", "ashinde"]

# Built-in Imports
import os
import json

# Custom Imports
from .common import configurations
from .common.logger import log
from . import XmlCliLib as clb
from . import XmlIniParser as prs
from . import UefiFwParser as fwp
from .common.uefi_nvar import get_set_var

BootOrderDict = {}


def cliProcessKnobs(xmlfilename, inifilename, CmdSubType, ignoreXmlgeneration=False, PrintResParams=True, ResBufFilename=0, KnobsVerify=False, KnobsDict={}):
  clb.LastErrorSig = 0x0000
  clb.InitInterface()
  DRAM_MbAddr = clb.GetDramMbAddr() # Get DRam MAilbox Address.
  log.debug(f'CLI Spec Version = {clb.GetCliSpecVersion(DRAM_MbAddr)}')
  DramSharedMBbuf = clb.memBlock(DRAM_MbAddr,0x200) # Read/save parameter buffer

  Operation = 'Prog'
  Retries = 5
  Delay = 2
  if(clb.UfsFlag):
    if((CmdSubType == clb.CLI_KNOB_RESTORE_MODIFY) or (CmdSubType == clb.CLI_KNOB_LOAD_DEFAULTS)):
      if (CmdSubType == clb.CLI_KNOB_RESTORE_MODIFY):
        Operation = 'ResMod'
      elif (CmdSubType == clb.CLI_KNOB_LOAD_DEFAULTS):
        Operation = 'LoadDef'
      CmdSubType = clb.CLI_KNOB_APPEND
    Retries = 10
    Delay = 3
  if(ignoreXmlgeneration):
    log.info('Skipping XML Download, Using the given XML File')
  else:
    if (CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS):
      if ( clb.SaveXml(xmlfilename, 1, MbAddr=DRAM_MbAddr) == 1 ):   # Check and Save the GBT XML knobs section.
        log.error('Aborting due to Error!')
        clb.CloseInterface()
        return 1
  CLI_ReqBuffAddr      = clb.readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Address
  CLI_ResBuffAddr      = clb.readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
  log.info(f'CLI Request Buffer Addr = 0x{CLI_ReqBuffAddr:X}   CLI Response Buffer Addr = 0x{CLI_ResBuffAddr:X}')
  if ( (CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0) ):
    log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  CommandId = 0
  if (CmdSubType == clb.CLI_KNOB_APPEND):
    CommandId = clb.APPEND_BIOS_KNOBS_CMD_ID
  elif (CmdSubType == clb.CLI_KNOB_RESTORE_MODIFY):
    CommandId = clb.RESTOREMODIFY_KNOBS_CMD_ID
  elif (CmdSubType == clb.CLI_KNOB_READ_ONLY):
    CommandId = clb.READ_BIOS_KNOBS_CMD_ID
  elif (CmdSubType == clb.CLI_KNOB_LOAD_DEFAULTS):
    CommandId = clb.LOAD_DEFAULT_KNOBS_CMD_ID

  SmiLoopCount = 1
  if (CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS):
    binfile = os.path.join(clb.TempFolder, 'biosKnobsdata.bin')
    if(clb.FlexConCfgFile):
      prs.generate_bios_knobs_config(xmlfilename, inifilename, clb.TmpKnobsIniFile)
      inifilename = clb.TmpKnobsIniFile
    if(clb.UfsFlag):
      BuffDict,tmpBuff = prs.generate_knobs_data_bin(xmlfilename, inifilename, binfile, Operation)
      if((len(BuffDict) == 0) or (clb.ReadBuffer(tmpBuff, 0, 4, clb.HEX) == 0)) and (CmdSubType != clb.CLI_KNOB_RESTORE_MODIFY):
        log.debug('Request buffer is Empty, No Action required, Aborting...')
        clb.CloseInterface()
        clb.LastErrorSig = 0xC4B0  # XmlCli Request Buffer Empty no action needed on XmlCli Command
        return 0
      SmiLoopCount = len(BuffDict)
      log.debug(f'Number of Nvars to be processed = {SmiLoopCount:d}')
      if (CmdSubType == clb.CLI_KNOB_READ_ONLY):
        SmiLoopCount = 1
    else:
      tmpBuff = prs.parse_cli_ini_xml(xmlfilename, inifilename, binfile)
      if((len(tmpBuff) == 0) or (clb.ReadBuffer(tmpBuff, 0, 4, clb.HEX) == 0)) and (CmdSubType != clb.CLI_KNOB_RESTORE_MODIFY):
        log.debug('Request buffer is Empty, No Action required, Aborting...')
        clb.CloseInterface()
        clb.LastErrorSig = 0xC4B0  # XmlCli Request Buffer Empty no action needed on XmlCli Command
        return 0

  #For Loop for number of current requested NVAR's
  ResParamSize = 0
  for SmiCount in range (0, SmiLoopCount):
    # Clear CLI Command & Response buffer headers
    clb.ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
    if (CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS):
      if(SmiLoopCount == 1):
        log.info(f'Req Buffer Bin file used is {binfile}')
        clb.load_data(binfile, CLI_ReqBuffAddr+clb.CLI_REQ_RES_READY_PARAMSZ_OFF)
      else:
        loopCnt = Index = 0
        for VarId in BuffDict:
          Index = VarId
          if(loopCnt == SmiCount):
            break
          loopCnt = loopCnt + 1
        log.debug(
          f'Processing NVARId = {Index:d} CurrentLoopCount={SmiCount:d} RemCount={(SmiLoopCount - SmiCount - 1):d}')
        NewBinfile = os.path.join(clb.TempFolder, 'biosKnobsdata_%d.bin' %Index)
        log.info(f'Req Buffer Bin file used is {NewBinfile}')
        clb.load_data(NewBinfile, CLI_ReqBuffAddr+clb.CLI_REQ_RES_READY_PARAMSZ_OFF)
        clb.RemoveFile(NewBinfile)
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_CMD_OFF, 4, CommandId)
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG )
    log.info('CLI Mailbox programmed, issuing S/W SMI to program knobs...')

    Status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
    if(Status):
      log.error('Error while triggering CLI Entry Point, Aborting....')
      clb.CloseInterface()
      return 1

    if (clb.WaitForCliResponse(CLI_ResBuffAddr, Delay, Retries) != 0):
      log.error('CLI Response not ready, Aborting....')
      clb.CloseInterface()
      return 1

    CurParamSize = int(clb.memread(CLI_ResBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4))
    ResParambuff = bytearray()
    if(CurParamSize != 0):
      CurParambuff = clb.memBlock((CLI_ResBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE), CurParamSize)
      if(SmiCount == 0):
        ResParambuff = CurParambuff
      else:
        ResParambuff = ResParambuff + CurParambuff
    ResParamSize = ResParamSize + CurParamSize
  #For Loop ends here.
  if (ResParamSize == 0):
    log.debug('BIOS knobs CLI Command ended successfully, CLI Response buffer Parameter size is 0, hence returning..')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC4E0  # XmlCli Resp Buffer Parameter Size is Zero
    return 0

  if (ResBufFilename == 0):
    ResBufFilename = os.path.join(clb.TempFolder, 'RespBuffdata.bin')
  with open(ResBufFilename, 'wb') as out_file:  # opening for writing
    out_file.write(ResParambuff)

  log.debug('BIOS knobs CLI Command ended successfully',)

  offsetIn = 4
  Index = 0
  KnobsDict.clear()
  if( CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS ):
    with open(binfile, 'rb') as InputFile:
      InputFilePart = InputFile.read()
    NumberOfEntries = clb.ReadBuffer(InputFilePart, 0, 4, clb.HEX)
  else:
    NumberOfEntries = 1
  while(NumberOfEntries != 0):
    offsetOut = 0
    if( CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS ):
      InVarId      = clb.ReadBuffer(InputFilePart, offsetIn+0, 1, clb.HEX)
      InKnobOffset = clb.ReadBuffer(InputFilePart, offsetIn+1, 2, clb.HEX)
      InKnobSize   = clb.ReadBuffer(InputFilePart, offsetIn+3, 1, clb.HEX)
      InByteSize = InKnobSize
      if InKnobOffset & 0x8000:
        InKnobOffset = clb.BITWISE_KNOB_PREFIX + ((InKnobOffset & 0x7FFF) * 8) + (InKnobSize & 0x7)
        BitEnd = ( ((InKnobSize >> 3) & 0x3F) + (InKnobSize & 0x7) )
        if BitEnd % 8:
          InByteSize = int(BitEnd / 8) + 1
        else:
          InByteSize = int(BitEnd / 8)
        InKnobSize = ((InKnobSize >> 3) & 0x3F)
      InputValue   = clb.ReadBuffer(InputFilePart, offsetIn+4, InByteSize, clb.HEX)
    else:
      InVarId = InKnobOffset = InKnobSize = InByteSize = InputValue = 0
    while(1):
      if (offsetOut >= ResParamSize):
        break
      OutVarId      = clb.ReadBuffer(ResParambuff, offsetOut+6, 1, clb.HEX)
      OutKnobOffset = clb.ReadBuffer(ResParambuff, offsetOut+7, 2, clb.HEX)
      OutKnobSize   = clb.ReadBuffer(ResParambuff, offsetOut+9, 1, clb.HEX)
      OutByteSize = OutKnobSize
      if OutKnobOffset & 0x8000:
        OutKnobOffset = clb.BITWISE_KNOB_PREFIX + ((OutKnobOffset & 0x7FFF) * 8) + (OutKnobSize & 0x7)
        BitEnd = ( ((OutKnobSize >> 3) & 0x3F) + (OutKnobSize & 0x7) )
        if BitEnd % 8:
          OutByteSize = int(BitEnd / 8) + 1
        else:
          OutByteSize = int(BitEnd / 8)
        OutKnobSize = ((OutKnobSize >> 3) & 0x3F)
      if( ((OutVarId == InVarId) and (OutKnobOffset == InKnobOffset) and (OutKnobSize == InKnobSize)) or  (CmdSubType == clb.CLI_KNOB_LOAD_DEFAULTS) ):
        DefVal           = clb.ReadBuffer(ResParambuff, offsetOut+10, OutByteSize, clb.HEX)
        OutValue         = clb.ReadBuffer(ResParambuff, offsetOut+10+OutByteSize, OutByteSize, clb.HEX)
        KnobEntryAdd     = clb.ReadBuffer(ResParambuff, offsetOut+0, 4, clb.HEX)
        Type, KnobName   = clb.findKnobName(KnobEntryAdd)
        KnobsDict[Index] = {'Type': Type, 'KnobName': KnobName, 'VarId': OutVarId, 'Offset': OutKnobOffset, 'Size': OutKnobSize, 'InValue': InputValue, 'DefValue': DefVal, 'OutValue': OutValue, 'UqiVal': '', 'Prompt': ''}
        Index = Index + 1
        if( CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS ):
          break
      offsetOut = offsetOut + 10 + (OutByteSize*2)
    offsetIn = offsetIn + 4 + InByteSize
    NumberOfEntries = NumberOfEntries-1
  create_json(KnobsDict, CmdSubType) # Function call to create json output
  if (PrintResParams):
    log.debug(', see below for the results..')
    log.debug('|--|-----|------------------------------------------|--|-----------|-----------|')
    if (CmdSubType == clb.CLI_KNOB_LOAD_DEFAULTS):
      log.debug('|VI|Ofset|                 Knob Name                |Sz|PreviousVal|RestoredVal|')
    else:
      log.debug('|VI|Ofset|                 Knob Name                |Sz|   DefVal  |   CurVal  |')
    log.debug('|--|-----|------------------------------------------|--|-----------|-----------|')
    for KnobCount in range (0, len(KnobsDict)):   # read and print the return knobs entry parameters from CLI's response buffer
      if(KnobsDict[KnobCount]['Type'] == 'string'):
        if (KnobsDict[KnobCount]['DefValue'] == 0):
          DefStr = ''
        else:
          DefStr = clb.UnHexLiFy(KnobsDict[KnobCount]['DefValue'])[::-1]
        if (KnobsDict[KnobCount]['OutValue'] == 0):
          OutStr = ''
        else:
          OutStr = clb.UnHexLiFy(KnobsDict[KnobCount]['OutValue'])[::-1]
        log.debug(
          f'|{KnobsDict[KnobCount]["VarId"]:2X}| {KnobsDict[KnobCount]["Offset"]:04X}|{KnobsDict[KnobCount]["KnobName"]:>42}|{KnobsDict[KnobCount]["Size"]:2X}| L\"{DefStr}\" | L\"{OutStr}\" |')
      else:
        if (KnobsDict[KnobCount]['Offset'] >= clb.BITWISE_KNOB_PREFIX):
          OffsetStr = '%05X' %KnobsDict[KnobCount]['Offset']
        else:
          OffsetStr = ' %04X' %KnobsDict[KnobCount]['Offset']
        log.debug(
          f'|{KnobsDict[KnobCount]["VarId"]:2X}|{OffsetStr}|{KnobsDict[KnobCount]["KnobName"]:>42}|{KnobsDict[KnobCount]["Size"]:2X}| {KnobsDict[KnobCount]["DefValue"]:8X}  | {KnobsDict[KnobCount]["OutValue"]:8X}  |')
      log.debug('|--|-----|------------------------------------------|--|-----------|-----------|')
  else:
    log.debug(', Print Parameter buff is disabled..')

  ReturnVal = 0
  if( KnobsVerify and (CmdSubType != clb.CLI_KNOB_LOAD_DEFAULTS) ):
    VerifyErrCnt = 0
    for KnobCount in range (0, len(KnobsDict)):
      if(KnobsDict[KnobCount]['InValue'] != KnobsDict[KnobCount]['OutValue']):
        VerifyErrCnt = VerifyErrCnt + 1
        log.debug(
          f'Verify Fail: Knob = {KnobsDict[KnobCount]["KnobName"]}  ExpectedVal = 0x{KnobsDict[KnobCount]["InValue"]:X}    CurrVal = 0x{KnobsDict[KnobCount]["OutValue"]:X} ')
    if (VerifyErrCnt == 0):
      log.debug('Verify Passed!')
    else:
      log.debug('Verify Failed!')
      ReturnVal = 1
      clb.LastErrorSig = 0xC42F  # XmlCli Knobs Verify Operation Failed
  clb.CloseInterface()
  return ReturnVal


def GetSetVar(Operation='get', xmlfile=0, KnobString='', NvarName='', NvarGuidStr='', NvarAttri='0x00', NvarSize='0x00', NvarDataString='', DisplayVarOut=True):
  # method implemented as a result of backward command compatibility!!!

  result = get_set_var(
    operation=Operation,
    xml_file=xmlfile,
    knob_string=KnobString,
    nvar_name=NvarName,
    nvar_guid=utils.guid_formatter(NvarGuidStr, string_format="xmlcli_mod"),
    nvar_attrib=NvarAttri,
    nvar_size=NvarSize,
    nvar_data=NvarDataString,
    display_result=DisplayVarOut
  )
  status = 0 if result and isinstance(result, dict) else 1
  return status


# Descriptor_Region                 = 0
# BIOS_Region                       = 1
# ME_Region                         = 2
# GBE_Region                        = 3
# PDR_Region                        = 4
# Device_Expan_Region               = 5
# Sec_BIOS_Region                   = 6
def CompareFlashRegion(RefBiosFile, NewBiosFile, Region=fwp.ME_Region):
  clb.LastErrorSig = 0x0000
  with open(RefBiosFile, 'rb') as BiosRomFile:
    DescRegionListBuff = list(BiosRomFile.read(0x1000))    # first 4K region is Descriptor region.
  fwp.FlashRegionInfo(DescRegionListBuff, False)
  if(fwp.FwIngredientDict['FlashDescpValid'] != 0):
    Offset = fwp.FwIngredientDict['FlashRegions'][Region]['BaseAddr']
    RegionSize = (fwp.FwIngredientDict['FlashRegions'][Region]['EndAddr'] - Offset + 1)
    with open(RefBiosFile, 'rb') as RefBiosRomFile:
      tmpBuff = RefBiosRomFile.read(Offset)
      RefRegionBuffList = list(RefBiosRomFile.read(RegionSize))
    with open(NewBiosFile, 'rb') as NewBiosRomFile:
      tmpBuff = NewBiosRomFile.read(Offset)
      NewRegionBuffList = list(NewBiosRomFile.read(RegionSize))
    log.info(
      f'Comparing Region \"{fwp.FlashRegionDict[Region]}\" at Flash binary Offset: 0x{Offset:X}  Size: 0x{RegionSize:X} ')
    if(RefRegionBuffList == NewRegionBuffList):
      log.debug(f'Region \"{fwp.FlashRegionDict[Region]}\" matches between the two binaries')
      return 0
    else:
      log.debug(f'Region \"{fwp.FlashRegionDict[Region]}\" is different between the two binaries')
      clb.LastErrorSig = 0xFCFA  # CompareFlashRegion: Flash Compare Result for given Region is FAIL
      return 1


def savexml(filename=clb.PlatformConfigXml, BiosBin=0, BuildType=0xFF):
  """
  Save entire/complete Target XML to desired file.

  In this function we will first check if target XML does exist,
  if XML exists we will compare XML header and if doesn’t matches we will overwrite current XML.
  If XML doesn’t exists we will download complete XML in desired file.

  :param filename: absolute path to xml file
  :param BiosBin: (optional) IFWI/BIOS binary to generate xml from
  :param BuildType:
  :return:
  """
  if BiosBin == 0:
    status = clb.SaveXml(filename)
  else:
    status = fwp.GetsetBiosKnobsFromBin(BiosBin, 0, 'genxml', filename, BuildType=BuildType)
  return status


def CreateTmpIniFile(KnobString):
  if (KnobString == 0):
    return clb.KnobsIniFile
  else:
    with open(clb.TmpKnobsIniFile, 'w') as IniFilePart:
      IniFilePart.write(
        ';-----------------------------------------------------------------\n'
        '; FID XmlCli contact: xmlcli_mod@intel.com\n'
        '; XML Shared MailBox settings for XmlCli based setup\n'
        '; The name entry here should be identical as the name from the XML file (retain the case)\n'
        ';-----------------------------------------------------------------\n'
        '[BiosKnobs]\n'
        )
      KnobString = KnobString.replace(',', '\n')
      IniFilePart.write(f'{KnobString}\n')
    return clb.TmpKnobsIniFile


# Program given BIOS knobs for CV.
def CvProgKnobs(KnobStr=0, BiosBin=0, BinOutSufix=0, UpdateHiiDbDef=False, BiosOut='', BuildType=0xFF):
  IniFile = CreateTmpIniFile(KnobStr)
  if(BiosBin == 0):
    Status = cliProcessKnobs(clb.PlatformConfigXml, IniFile, clb.CLI_KNOB_APPEND, 0, 1, KnobsVerify=True)
  else:
    Status = fwp.GetsetBiosKnobsFromBin(BiosBin, BinOutSufix, 'prog', clb.PlatformConfigXml, IniFile, UpdateHiiDbDef, BiosOut, BuildType=BuildType)
  return Status

def PrintResults(KnobsDict={}, Operation='read'):
  if(len(KnobsDict) == 0):
    return
  else:
    log.debug(', see below for the results..')
    log.debug('|--|----|------------------------------------------|--|-----------|-----------|')
    if (Operation == 'loaddefaults'):
      log.debug('|VI|Ofst|                 Knob Name                |Sz|PreviousVal|RestoredVal|')
    else:
      log.debug('|VI|Ofst|                 Knob Name                |Sz|   DefVal  |   CurVal  |')
    log.debug('|--|----|------------------------------------------|--|-----------|-----------|')
  for Knob in KnobsDict:
    if(KnobsDict[Knob]['Type'] == 'string'):
      DefStr = clb.UnHexLiFy(KnobsDict[Knob]['DefVal'])[::-1]
      OutStr = clb.UnHexLiFy(KnobsDict[Knob]['CurVal'])[::-1]
      log.debug(
        f'|{KnobsDict[Knob]["VarId"]:2X}|{KnobsDict[Knob]["Offset"]:4X}|{Knob:>42}|{KnobsDict[Knob]["Size"]:2X}| L\"{DefStr}\" | L\"{OutStr}\" |')
    else:
      log.debug(
        f'|{KnobsDict[Knob]["VarId"]:2X}|{KnobsDict[Knob]["Offset"]:4X}|{Knob:>42}|{KnobsDict[Knob]["Size"]:2X}| {KnobsDict[Knob]["DefVal"]:8X}  | {KnobsDict[Knob]["CurVal"]:8X}  |')
    log.debug('|--|----|------------------------------------------|--|-----------|-----------|')
  VerifyStatus = 0
  for Knob in KnobsDict:
    if(KnobsDict[Knob]['ReqVal'] != KnobsDict[Knob]['CurVal']):
      log.debug(
        f'Verify Fail: Knob = {Knob}  ExpectedVal = 0x{KnobsDict[Knob]["ReqVal"]:X}    CurrVal = 0x{KnobsDict[Knob]["CurVal"]:X} ')
      VerifyStatus = VerifyStatus + 1
  if (VerifyStatus == 0):
    log.debug('Verify Passed!')
  else:
    log.debug('Verify Failed!')
  return VerifyStatus

def getKnobsDict(fname):
  with open(fname) as file_ptr:
    biosiniList = file_ptr.readlines()
  iniDict = {}
  knobStart = False
  for LineNo in range (0, len(biosiniList)):
    line = (biosiniList[LineNo].split(';')[0]).strip()
    if(line == ''):
      continue
    if(knobStart):
      (knobName,knobValue)= line.split('=')
      iniDict[knobName.strip()] = knobValue.strip()
    if (line == '[BiosKnobs]'):
      knobStart = True
      continue
  return iniDict

# save entire/complete Target XML to desired file.
def savexmllite(filename=clb.PlatformConfigLiteXml):
  Status = clb.SaveXmlLite(filename)
  return Status

def ReadKnobsLite(KnobStr=0):
  IniFile = CreateTmpIniFile(KnobStr)
  MyKnobDict = getKnobsDict(IniFile)
  if(len(MyKnobDict) == 0):
    log.debug('Input knob List is empty, returning!')
    return 0
  Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='savexml', UserKnobsDict=MyKnobDict)
  if (Status == 0):
    RetDict, PrevDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, MyKnobDict)
    Status = PrintResults(RetDict, Operation='prog')
  return Status

def ProgKnobsLite(KnobStr=0):
  IniFile = CreateTmpIniFile(KnobStr)
  MyKnobDict = getKnobsDict(IniFile)
  if(len(MyKnobDict) == 0):
    log.debug('Input knob List is empty, returning!')
    return 0
  Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='prog', UserKnobsDict=MyKnobDict)
  if (Status == 0):
    RetDict, PrevDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, MyKnobDict)
    Status = PrintResults(RetDict, Operation='prog')
  return Status

def ResModKnobsLite(KnobStr=0):
  Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='savexml')
  if (Status == 0):
    IniFile = CreateTmpIniFile(KnobStr)
    MyKnobDict = getKnobsDict(IniFile)
    RetDict, PrevDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, MyKnobDict, operation='restore')
    if(len(RetDict) == 0):
      log.debug('Input knob List is empty and other Knobs already thier Defaults, returning!')
      return 0
    Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='prog', UserKnobsDict=RetDict)
    if (Status == 0):
      ResDict, PrevDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, RetDict)
      Status = PrintResults(ResDict, Operation='prog')
  return Status

def LoadDefaultsLite():
  Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='savexml')
  if (Status == 0):
    PreValDict={}
    RetDict, PrevDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, operation='restore')
    if(len(RetDict) == 0):
      log.debug('Current Knobs already at their Defaults!')
      return 0
    Status = clb.SaveXmlLite(clb.PlatformConfigLiteXml, Operation='prog', UserKnobsDict=RetDict)
    if (Status == 0):
      ResDict, tempDict = prs.xml_to_knob_map(clb.PlatformConfigLiteXml, RetDict)
      for knob in PrevDict:
        ResDict[knob]['DefVal'] = clb.Str2Int(PrevDict[knob])
      Status = PrintResults(ResDict, Operation='loaddefaults')
  return Status

# Restore & then modify given BIOS knobs for CV.
def CvRestoreModifyKnobs(KnobStr=0, BiosBin=0):
  IniFile = CreateTmpIniFile(KnobStr)
  if(BiosBin == 0):
    Status = cliProcessKnobs(clb.PlatformConfigXml, IniFile, clb.CLI_KNOB_RESTORE_MODIFY, 0, 1, KnobsVerify=True)
  else:
    log.error('Restore modify operation is not supported in Offline mode, please use CvProgKnobs with pristine Bios binary to get the same effect')
    Status = 0
  return Status

# Load Default BIOS knobs for CV.
def CvLoadDefaults(BiosBin=0):
  if(BiosBin == 0):
    Status = cliProcessKnobs(clb.PlatformConfigXml, clb.KnobsIniFile, clb.CLI_KNOB_LOAD_DEFAULTS, 0, 1, KnobsVerify=False)
  else:
    log.error('Load Defaults operation is not supported in Offline mode, please use pristine Bios binary instead')
    Status = 0
  return Status

# Read BIOS knobs for CV.
def CvReadKnobs(KnobStr=0, BiosBin=0, BuildType=0xFF):
  IniFile = CreateTmpIniFile(KnobStr)
  if(BiosBin == 0):
    Status = cliProcessKnobs(clb.PlatformConfigXml, IniFile, clb.CLI_KNOB_READ_ONLY, 0, 1, KnobsVerify=True)
  else:
    Status = fwp.GetsetBiosKnobsFromBin(BiosBin, 0, 'readonly', clb.PlatformConfigXml, IniFile, BuildType=BuildType, KnobsVerify=True)
  return Status

def GenBootOrderDict(PcXml, NewBootOrderStr=''):
  global BootOrderDict
  clb.LastErrorSig = 0x0000
  Tree = prs.ET.parse(PcXml)
  BootOrderDict = {}
  BootOrderDict['OptionsDict'] = {}
  BootOrderDict['OrderList'] = {}
  OrderIndex = 0
  for SetupKnobs in Tree.iter(tag='biosknobs'):
    for BiosKnob in SetupKnobs:
      SETUPTYPE = (prs.nstrip(BiosKnob.get('setupType'))).upper()
      KnobName = prs.nstrip(BiosKnob.get('name'))
      if (KnobName[0:10] == 'BootOrder_'):
        BootOrderDict['OrderList'][OrderIndex] = int(prs.nstrip(BiosKnob.get('CurrentVal')), 16)
        if ( (SETUPTYPE == 'ONEOF') and (OrderIndex == 0) ):
          OptionsCount = 0
          for options in BiosKnob:
            for option in options:
              BootOrderDict['OptionsDict'][OptionsCount] = { 'OptionText': prs.nstrip(option.get('text')), 'OptionVal': int(prs.nstrip(option.get('value')), 16) }
              OptionsCount = OptionsCount + 1
        OrderIndex = OrderIndex + 1
  if (NewBootOrderStr == ''):
    BootOrderLen = len(BootOrderDict['OrderList'])
    if(BootOrderLen == 0):
      log.debug('\tBoot Order Variable not found in XML!')
      clb.LastErrorSig = 0xB09F  # GenBootOrderDict: Boot Order Variable not found in XML
      return 1
    else:
      if(len(BootOrderDict['OptionsDict']) == 0):
        log.debug('\tBoot Order Options is empty!')
        clb.LastErrorSig = 0xB09E  # GenBootOrderDict: Boot Order Options is empty in XML
        return 1
      BootOrderString = ''
      for count in range (0, BootOrderLen):
        if (count == 0):
          BootOrderString = BootOrderString + '%02X' %(BootOrderDict['OrderList'][count])
        else:
          BootOrderString = BootOrderString + '-%02X' %(BootOrderDict['OrderList'][count])
      log.debug(f'\n\tThe Current Boot Order: {BootOrderString}')
      log.debug('\n\tList of Boot Devices in the Current Boot Order')
      for count in range (0, BootOrderLen):
        for count1 in range (0, len(BootOrderDict['OptionsDict'])):
          if(BootOrderDict['OrderList'][count] == BootOrderDict['OptionsDict'][count1]['OptionVal']):
            log.debug(
              f'\t\t{BootOrderDict["OptionsDict"][count1]["OptionVal"]:02X} - {BootOrderDict["OptionsDict"][count1]["OptionText"]}')
            break
  else:
    NewBootOrder = NewBootOrderStr.split('-')
    KnobString = ''
    if(len(NewBootOrder) != len(BootOrderDict['OrderList'])):
      log.error('\tGiven Boot order list length doesnt match current, aborting')
      clb.LastErrorSig = 0xB09D  # GenBootOrderDict: Given Boot order list length doesn't match current list
      return 1
    for count in range (0, len(NewBootOrder)):
      KnobString = KnobString + 'BootOrder_' + '%d' %count + ' = 0x' + NewBootOrder[count] + ', '
    CvProgKnobs('%s' %KnobString)
  return 0

def GetBootOrder():
  Return=savexml(clb.PlatformConfigXml)
  if (Return==0):
    GenBootOrderDict(clb.PlatformConfigXml)
    log.debug('\n\tRequested operations completed successfully.\n')
    return 0
  else:
    log.error('\n\tRequested operation is Incomplete\n')
    return 1

def SetBootOrder(NewBootOrderStr=''):
  clb.LastErrorSig = 0x0000
  try:
    Return=savexml(clb.PlatformConfigXml)
    if (Return==0):
      set_operation=GenBootOrderDict(clb.PlatformConfigXml, NewBootOrderStr)
      if (set_operation==0):
        Return1=savexml(clb.PlatformConfigXml)
        if (Return1==0):
          GenBootOrderDict(clb.PlatformConfigXml)
          log.debug('\tRequested operations completed successfully.\n')
          return 0
        else:
          log.error('\tRequested operation is Incomplete\n')
      else:
        log.error('\n\tRequested operation is Incomplete\n')
    else:
      log.error('\n\tRequested operation is Incomplete\n')
    clb.LastErrorSig = 0x5B01  # SetBootOrder: Requested operation is Incomplete
  except IndexError:
    log.error('\n\tInvalid format to bootorder!!!\n')
    clb.LastErrorSig = 0x5B1F  # SetBootOrder: Invalid format to Set BootOrder
  return 1


def MsrAccess(operation, MsrNumber=0xFFFFFFFF, ApicId=0xFFFFFFFF, MsrValue=0):
  clb.LastErrorSig = 0x0000
  if( (MsrNumber == 0xFFFFFFFF) or (ApicId == 0xFFFFFFFF)):
    return 0
  clb.InitInterface()
  DRAM_MbAddr = clb.GetDramMbAddr()  # Get Dram Mailbox Address.
  log.debug(f'CLI Spec Version = {clb.GetCliSpecVersion(DRAM_MbAddr)}')
  DramSharedMBbuf = clb.memBlock(DRAM_MbAddr,0x110) # Read/save parameter buffer
  CLI_ReqBuffAddr = clb.readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Adderss
  CLI_ResBuffAddr = clb.readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
  log.info(f'CLI Request Buffer Addr = 0x{CLI_ReqBuffAddr:X}   CLI Response Buffer Addr = 0x{CLI_ResBuffAddr:X}')
  if ( (CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0) ):
    log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  # Clear CLI Command & Response buffer headers
  clb.ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
  for Count in range (0, 0x20):
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + Count, 8, 0 )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_CMD_OFF, 8, operation )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 8 )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, 4, MsrNumber )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 4, 4, ApicId )
  if (operation == clb.WRITE_MSR_OPCODE):
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 8, 8, MsrValue )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG )
  log.info('CLI Mailbox programmed, now issuing S/W SMI to execute the given command..')

  Status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
  if(Status):
    log.error('Error while triggering CLI Entry Point, Aborting....')
    clb.CloseInterface()
    return 1
  if (clb.WaitForCliResponse(CLI_ResBuffAddr, 8) != 0):
    log.error('CLI Response not ready, Aborting....')
    clb.CloseInterface()
    return 1

  if (operation == clb.READ_MSR_OPCODE):
    MsrValue = int(clb.memread(CLI_ResBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, 8))
  log.debug(f'Msr No. 0x{MsrNumber:X}  ApicId = 0x{ApicId:X}  MsrValue = 0x{MsrValue:X} ')
  clb.CloseInterface()
  return 0

def IoAccess(operation, IoPort=0xFFFF, Size=0xFF, IoValue=0):
  clb.LastErrorSig = 0x0000
  if( (IoPort == 0xFFFF) or (Size == 0xFF)):
    return 0
  clb.InitInterface()
  DRAM_MbAddr = clb.GetDramMbAddr()  # Get Dram Mailbox Address.
  log.debug(f'CLI Spec Version = {clb.GetCliSpecVersion(DRAM_MbAddr)}')
  DramSharedMBbuf = clb.memBlock(DRAM_MbAddr,0x110) # Read/save parameter buffer
  CLI_ReqBuffAddr = clb.readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Address
  CLI_ResBuffAddr = clb.readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
  log.info(f'CLI Request Buffer Addr = 0x{CLI_ReqBuffAddr:X}   CLI Response Buffer Addr = 0x{CLI_ResBuffAddr:X}')
  if ( (CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0) ):
    log.error('CLI buffers are not valid or not supported, Aborting due to Error!')
    clb.CloseInterface()
    clb.LastErrorSig = 0xC140  # XmlCli Req or Resp Buffer Address is Zero
    return 1

  # Clear CLI Command & Response buffer headers
  clb.ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
  for Count in range (0, 0x8):
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + Count, 8, 0 )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_CMD_OFF, 8, operation )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, 8 )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, 4, IoPort )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 4, 4, Size )
  if (operation == clb.IO_WRITE_OPCODE):
    clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE + 8, 4, IoValue )
  clb.memwrite( CLI_ReqBuffAddr + clb.CLI_REQ_RES_READY_SIG_OFF, 4, clb.CLI_REQ_READY_SIG )
  log.info('CLI Mailbox programmed, now issuing S/W SMI to execute the given command..')

  Status = clb.TriggerXmlCliEntry()  # trigger S/W SMI for CLI Entry
  if(Status):
    log.error('Error while triggering CLI Entry Point, Aborting....')
    clb.CloseInterface()
    return 1
  if (clb.WaitForCliResponse(CLI_ResBuffAddr, 8) != 0):
    log.error('CLI Response not ready, Aborting....')
    clb.CloseInterface()
    return 1

  if (operation == clb.IO_READ_OPCODE):
    IoValue = int(clb.memread(CLI_ResBuffAddr + clb.CLI_REQ_RES_BUFF_HEADER_SIZE, 8))
  log.debug(f'IO Port 0x{IoPort:X}  Size = 0x{Size:X}  Value = 0x{IoValue:X} ')
  clb.CloseInterface()
  return 0

def create_json(knobs_dict=[], cmd_subtype=None):
  """Generates JSON output file for the online mode operations

    :param knobs_dict: dictionary which contains knobs entry parameters from CLI's response buffer.
    :param cmd_subtype: type of the operation performed
    :return:
  """
  json_dict = {}
  current_value = 0
  default_value = 0
  json_filename = clb.JSON_OUT_FILE
  for knob_count in range (0, len(knobs_dict)):  # read and print the return knobs entry parameters from CLI's response buffer
    if knobs_dict[knob_count]['Type'] == 'string':
      if knobs_dict[knob_count]['DefValue'] == 0:
        def_str = ''
      else:
        def_str = utils.unhex_lify(knobs_dict[knob_count]['DefValue'])[::-1]
      if knobs_dict[knob_count]['OutValue'] == 0:
        out_str = ''
      else:
        out_str = utils.unhex_lify(knobs_dict[knob_count]['OutValue'])[::-1]
      default_value = def_str
      current_value = out_str
    else:
      default_value = knobs_dict[knob_count]["DefValue"]
      current_value = knobs_dict[knob_count]["OutValue"]
    expected_value = knobs_dict[knob_count]['InValue']
    result = 'Pass' if knobs_dict[knob_count]['InValue'] == knobs_dict[knob_count]['OutValue'] else 'Fail'
    if cmd_subtype == clb.CLI_KNOB_LOAD_DEFAULTS:
      json_dict[knob_count] = {'KnobName': knobs_dict[knob_count]["KnobName"], 'PreviousVal': default_value, 'RestoredVal': current_value,'ExpectedValue':expected_value,'Result':result}
    else:
      json_dict[knob_count] = {'KnobName': knobs_dict[knob_count]["KnobName"], 'ExpectedValue':expected_value, 'CurrentValue': current_value,'Result':result}
  with open(json_filename, 'w') as fp:
    json.dump(json_dict, fp)
