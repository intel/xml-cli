#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Built-in imports
import os
import sys
import json

# tkinter imports for gui
import tkinter as tk
from tkinter import tix
from tkinter import messagebox
from tkinter import filedialog
from xmlcli.common.logger import log

try:
  from defusedxml import ElementTree as ET
except ModuleNotFoundError as e:
  log.warn("Insecure module import used! Please install all the required dependencies by running `pip install -r requirements.txt`")
  from xml.etree import cElementTree as ET


# Custom imports
from xmlcli import XmlCli as cli
from xmlcli.common import utils
from xmlcli.common import configurations

__all__ = ["gen_gui", "MainView", "PromptGui"]
__version__ = "0.0.6"
__author__ = "Gahan Saraiya"

########################################################################################################################
# BEGIN:CONSTANTS ######################################################################################################
# COLORS
BLUE = "#2a2c99"
DARK_BLUE = "#0f15b3"
GREY = "#bababa"
WHITE = "#fefcfc"
DARK_GREEN = "#013220"
YELLOW = "#ffffe0"
COLOR_PAIR = [BLUE, GREY]
INVERTED_COLOR_PAIR = COLOR_PAIR[::-1]

# PADDING
LISTBOX_HEIGHT = 1
BUTTON_PADDING_X = 2
BUTTON_PADDING_Y = 2
PAD_X = 15
PAD_Y = 4
MAX_COLUMN_SIZE = 35

DEFAULT_CHOICE = "◇"
CURRENT_CHOICE = "◈"
BOTH_CHOICE = "◆"

# WINDOW Config
WINDOW_TITLE = "Virtual BIOS Setup Page - via XmlCli"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_SIZE = "{}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT)

# FONTS
LABEL_FONT = "Verdana 10 bold"
DESCRIPTION_FONT = "Verdana 8"

OUTPUT_INI_LOCATION = os.path.join(configurations.XMLCLI_DIR, "cfg")
KNOB_JSON_PATH = "knobs.json"
PADDING_INDENT = 5

VALID_OFFLINE_EXTENSIONS = [".rom", ".bin", ".xml"]


# END:CONSTANTS ########################################################################################################


########################################################################################################################
# BEGIN:Generic Section ################################################################################################

class VerticalScrolledFrame:
  """A vertically scrolled Frame that can be treated like any other Frame
  i.e. it needs a master and layout and it can be a master.

  Note: A widget lying out in this frame will have a self.master 3 layers deep,
  (outer Frame, Canvas, inner Frame) so
  if you subclass this there is no built in way for the children to access it.
  You need to provide the controller separately.

  reference: https://gist.github.com/novel-yet-trivial/3eddfce704db3082e38c84664fc1fdf8
  """

  def __init__(self, master, **kwargs):
    """

    :param master: parent window
    :param kwargs:
      :width:, :height:, :bg: are passed to the underlying Canvas
      :bg: and all other keyword arguments are passed to the inner Frame
    """
    width = kwargs.pop('width', None)
    height = kwargs.pop('height', None)
    bg = kwargs.pop('bg', kwargs.pop('background', None))
    self.outer = tk.Frame(master, **kwargs)

    self.vsb = tk.Scrollbar(self.outer, orient=tk.VERTICAL)
    self.vsb.pack(fill=tk.Y, side=tk.RIGHT)
    self.canvas = tk.Canvas(self.outer, highlightthickness=0, width=width, height=height, bg=bg)
    self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    self.canvas['yscrollcommand'] = self.vsb.set
    # mouse scroll does not seem to work with just "bind"; You have
    # to use "bind_all". Therefore to use multiple windows you have
    # to bind_all in the current widget
    self.canvas.bind("<Enter>", self._bind_mouse)
    self.canvas.bind("<Leave>", self._unbind_mouse)
    self.vsb['command'] = self.canvas.yview

    self.inner = tk.Frame(self.canvas, bg=bg)
    # pack the inner Frame into the Canvas with the top left corner 4 pixels offset
    self.canvas.create_window(4, 4, window=self.inner, anchor='nw')
    self.inner.bind("<Configure>", self._on_frame_configure)

    self.outer_attr = set(dir(tk.Widget))

  def __getattr__(self, item):
    if item in self.outer_attr:
      # geometry attributes etc (eg pack, destroy, tkraise) are passed on to self.outer
      return getattr(self.outer, item)
    else:
      # all other attributes (_w, children, etc) are passed to self.inner
      return getattr(self.inner, item)

  def _on_frame_configure(self, event=None):
    x1, y1, x2, y2 = self.canvas.bbox("all")
    height = self.canvas.winfo_height()
    self.canvas.config(scrollregion=(0, 0, x2, max(y2, height)))

  def _bind_mouse(self, event=None):
    self.canvas.bind_all("<4>", self._on_mousewheel)
    self.canvas.bind_all("<5>", self._on_mousewheel)
    self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

  def _unbind_mouse(self, event=None):
    self.canvas.unbind_all("<4>")
    self.canvas.unbind_all("<5>")
    self.canvas.unbind_all("<MouseWheel>")

  def _on_mousewheel(self, event):
    """Linux uses event.num; Windows / Mac uses event.delta"""
    if event.num == 4 or event.delta > 0:
      self.canvas.yview_scroll(-1, "units")
    elif event.num == 5 or event.delta < 0:
      self.canvas.yview_scroll(1, "units")


class IntegerEntry(tk.Entry):
  """Manual Created Integer Entry widget
  to validate input checks
  """

  def __init__(self, master=None, **kwargs):
    self.var = kwargs.pop("textvariable", tk.StringVar())
    self.old_value = hex(kwargs.pop("current_value"))
    tk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
    self.var.trace('w', self.check)
    self.get, self.set = self.var.get, self.var.set

  def check(self, *args):
    """Check for entered value at every keystroke
    """
    val = self.get()

    if val.isdigit() or val in ("0x", ""):
      # the current value is only digits; or starts with hex/blank
      self.old_value = val
    elif val.startswith("0x"):
      # validate valid hex number else revert to previous value
      try:
        int(val, 16)
        self.old_value = val
      except ValueError:
        self.set(self.old_value)
    else:
      # Invalid integer or hex characters in the input; reject this
      self.set(self.old_value)


class ToolTip(object):
  """Class implementation of tooltip to be displayed on hover
  """

  def __init__(self, widget):
    self.widget = widget
    self.tipwindow = None
    self.id = None
    self.x = self.y = 0

  def showtip(self, text):
    """Display text in tooltip window when hover on widget
    """
    self.text = utils.string_splitter(text)
    if self.tipwindow or not self.text:
      return
    x, y, cx, cy = self.widget.bbox("insert")
    x = x + self.widget.winfo_rootx() + 57
    y = y + cy + self.widget.winfo_rooty() + 27
    self.tipwindow = tw = tk.Toplevel(self.widget)
    tw.wm_overrideredirect(1)
    tw.wm_geometry("+%d+%d" % (x, y))
    label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                     background=YELLOW, relief=tk.SOLID, borderwidth=1,
                     font=("tahoma", "8", "normal"))
    label.pack(ipadx=1)

  def hidetip(self):
    """Hide tool tip when hover out of the widget
    """
    tw = self.tipwindow
    self.tipwindow = None
    if tw:
      tw.destroy()


def create_tool_tip(widget, text):
  """Create tool tip over widget

  Args:
    widget: target widget to put tooltip on
    text: text to be specified in tooltip

  Returns:
    just create a tooltip
  """
  tool_tip = ToolTip(widget)

  def enter(event):
    """Displays tooltip on widget on event specified

    Args:
      event: event on which tooltip to be displayed

    Returns:

    """
    tool_tip.showtip(text)

  def leave(event):
    """Hides tooltip from widget on event specified

    Args:
      event: event on which tooltip to be hide

    Returns:

    """
    tool_tip.hidetip()

  # bind tooltip to widget on event
  widget.bind('<Enter>', enter)
  widget.bind('<Leave>', leave)


class BasePage(tk.Frame):
  """Base Page for the class"""

  def __init__(self, *args, **kwargs):
    tk.Frame.__init__(self, *args, **kwargs)

  def show(self):
    self.lift()


def log(level="INFO", title="", message="", alert=True):
  """Log/Display alert

  Args:
    level: level for tkinter messagebox
    title: title to be displayed on alert box
    message: message to be displayed on alert box
    alert:
      True - also shows alert message box
      False - log message on console only

  Returns:

  """
  methods = {
    "INFO"   : "showinfo",
    "ERROR"  : "showerror",
    "WARNING": "showwarning"
  }
  print(message)
  if alert and level in methods:
    getattr(messagebox, methods.get(level))(title=title if title else level.capitalize(), message=message)


def get_from_dict(data_dict, map_list):
  """Method to get value from dictionary hierarchy from list

  Args:
    data_dict: dictionary from which data to be read
    map_list: list of hierarchy of keys
      i.e. keys are read in increasing order of list index

  Returns: if map_list = [key1, key2, key3] then function returns
        value of data_dict[key1][key2][key3]

  """
  first, rest = map_list[0], map_list[1:]
  if rest:
    # if `rest` is not empty, run the function recursively
    return get_from_dict(data_dict[first], rest)
  else:
    return data_dict["knobs"][first]


def set_in_dict(data_dict, map_list, value):
  """Method to set value from dictionary hierarchy from list

  Args:
    data_dict: dictionary in which which data to be updated
    map_list: list of hierarchy of keys
      i.e. keys are read in increasing order of list index
    value: value/dictionary which is to be updated

  Returns: if map_list = [key1, key2, key3] then function
        sets/updates the value of data_dict[key1][key2][key3]
  """
  first, rest = map_list[0], map_list[1:]
  if rest:
    # data_dict.setdefault(first, {"knobs": []})
    data_dict.setdefault(first, {"knobs": {}})
    set_in_dict(data_dict[first], rest, value)
  else:
    data_dict.setdefault(first, {"knobs": {}})
    data_dict[first]["knobs"][value["@name"]] = value


def get_path_hierarchy(path):
  """Get parent hierarchy for the given path as a list

  Args:
    path: specify path which is to be represented as
          hierarchy list

  Returns: list of hierarchy of path

  """
  return path.split('/')[:-1]


def get_hierarchy(knob):
  """Get the hierarchy path for the knob

  Args:
    knob: knob dictionary to get SetupPgPtr

  Returns: SetupPgPtr of knob eliminating it's
  own prompt name from the end of string

  """
  path_hierarchy = knob['@SetupPgPtr']
  if knob['@prompt'].strip():
    # There is recent scenario discovered where setup knobs have empty prompt name
    prompt_len = len(knob['@prompt'])
    path_hierarchy = knob['@SetupPgPtr'][:-prompt_len]
  return path_hierarchy


def is_offline_xml(file_path):
  """Identify whether the given xml file is
  offline or not

  Args:
    file_path: xml file location

  Returns: boolean value
    True - if xml type is offline
  """
  if not os.path.exists(file_path):
    err_msg = "File not exist"
    return False
  tree = ET.parse(file_path)
  root = tree.getroot()
  gbt = root.find("GBT")
  xml_type = gbt.attrib.get("Type", "")
  return bool(xml_type.lower() == "offline")


# END:Generic Section ##################################################################################################


########################################################################################################################
# BEGIN:Main Section ###################################################################################################

CHANGE_LIST = {}


class DynamicPage(BasePage):
  """Pages for knob values which are generated dynamically
  on click event from Menubar
  """

  def __init__(self, page_title, knobs, parent, *args, **kwargs):
    """

    Args:
      *args:
      page_title: title of the Page to be displayed on top of frame
      knobs: list of knobs which are to be place in grid of the frame
      parent: parent page of all the knobs
      **kwargs:
    """
    self.args = args
    self.kwargs = kwargs
    self.page_title = page_title
    self.knobs = knobs
    self.parent = parent
    self.knob_tree = json.load(open(KNOB_JSON_PATH, "r", encoding="utf-8"))

    BasePage.__init__(self, *args, **kwargs)

    self.config(bg=GREY)  # configure background of the page

    label = tk.Label(self, text=self.page_title, font=('Helvetica', 12, 'bold'),
                     fg=WHITE,
                     bg=DARK_BLUE
                     )
    label.pack()
    help_frame = tk.Frame(self, bg=GREY)
    help_frame.pack()
    tk.Label(help_frame, text="Default Choice - {}".format(DEFAULT_CHOICE),
             font=('Helvetica', 10), relief=tk.RIDGE, bg=GREY).pack(side=tk.LEFT, padx=PAD_X)
    tk.Label(help_frame, text="Current Choice - {}".format(CURRENT_CHOICE),
             font=('Helvetica', 10), relief=tk.RIDGE, bg=GREY).pack(side=tk.LEFT, padx=PAD_X)
    tk.Label(help_frame, text="Default & Current Choice - {}".format(BOTH_CHOICE),
             font=('Helvetica', 10), relief=tk.RIDGE, bg=GREY).pack(side=tk.LEFT, padx=PAD_X)

    if self.knobs:
      # vertical scrollable frame with mouse wheel support
      self.win = VerticalScrolledFrame(self, width=300, relief=tk.SUNKEN, background=GREY)
      self.win.pack(fill=tk.BOTH, expand=True)
      self.make_form(self.win)  # create form with knob options

  def stored_current_value(self, hierarchy):
    """Get the current value for the path hierarchy

    Args:
      hierarchy: hierarchy for which current value to be fetched

    Returns:

    """
    # try to get current value from change list
    current_value = CHANGE_LIST.get(hierarchy[-1], {}).get("previous_value", None)
    if not current_value:  # value not exist in changelist
      # load current value from the refined knobs dictionary
      current_value = self.parent.get_current_value_of(self.knob_tree, hierarchy)
    return current_value

  def on_changed(self, entry, tkvar, txt_cur_val, field, choices, *args):
    """Handles the widget/entry value when changed

    Args:
      entry: entry for which function is working
      tkvar: tk variable to read the changed value
      txt_cur_val: current value as text
      field: knob dictionary
      choices: available choices (for dropdown)
      *args:

    Returns:

    """
    # print("CHANGES!!!", entry, tkvar, txt_cur_val, field, args, sep=" | ")
    hierarchy = get_path_hierarchy(get_hierarchy(field))
    knob_name = field["@name"]
    setup_type = field["@setupType"]
    hierarchy.append(knob_name)
    current_value_int = field["@CurrentVal"]
    default_value = field["@default"]  # load default value of the knob
    current_value = self.stored_current_value(hierarchy=hierarchy)
    new_value_int = ""
    previous_value_str = current_value
    if setup_type == "oneof":  # show dropdown
      value = tkvar.get().replace(BOTH_CHOICE, "").replace(DEFAULT_CHOICE, "").replace(CURRENT_CHOICE, "").strip()
      rev_choices = {v.replace(BOTH_CHOICE, "").replace(DEFAULT_CHOICE, "").replace(CURRENT_CHOICE, "").strip(): k for
                     k, v in choices.items()}
      new_value_int = rev_choices.get(value)
      previous_value_str = choices.get(utils.get_integer_value(current_value)).replace(BOTH_CHOICE, "").replace(DEFAULT_CHOICE, "").replace(CURRENT_CHOICE, "").strip()
    elif setup_type == "numeric":
      _val = tkvar.get()
      new_value_int = utils.get_integer_value(_val)
      if new_value_int:
        value = new_value_int
        _min, _max = utils.get_integer_value(field["@min"]), utils.get_integer_value(field["@max"])
        if value not in range(_min, _max + 1):
          tkvar.set(current_value)
          value = new_value_int = current_value_int
          err_msg = "Value must be in range {0}(0x{0:x}) to {1} (0x{1:x})".format(_min, _max)
          log(level="ERROR", title="Error!!!", message=err_msg, alert=True)
      else:
        tkvar.set(current_value)
        value = new_value_int = current_value_int
        err_msg = "Please enter valid integer/hex value"
        log(level="ERROR", title="Error!!!", message=err_msg, alert=True)
    elif setup_type == "checkbox":
      new_value_int = tkvar.get()
      value = new_value_int
    else:
      value = tkvar.get()
      # print("{} : {}".format(prompt, value))
      value = value.replace(DEFAULT_CHOICE, "").replace(CURRENT_CHOICE, "").strip()

    if not self.parent.publish_all:
      # update dictionary for evaluating knob status only if option is not set to publish all
      _value = new_value_int.strip() if not isinstance(new_value_int, int) else hex(new_value_int)
      self.parent.evaluated_depex[knob_name]["CurVal"] = _value

    if new_value_int != utils.get_integer_value(current_value):  # new value is different then the current value stored in xml
      _changes = {
        # "hierarchy": hierarchy,
        "new_value"         : value,  # store new value as is
        "new_value_int"     : new_value_int,  # stores new value in form of integer
        "previous_value_str": previous_value_str,  # stores previous value/ i.e. current value from xml file
        "previous_value"    : current_value,  # stores previous value/ i.e. current value from xml file
        "default"           : default_value,  # stores default value from xml
        "hierarchy"         : hierarchy  # stores hierarchy of knob option
      }
      CHANGE_LIST[knob_name] = _changes
    else:  # new value same is current value in xml
      if knob_name in CHANGE_LIST:
        # if knob value changed previously and set back to current value in xml then remove it from change list
        CHANGE_LIST.pop(knob_name)
    if not self.parent.publish_all:
      # for online mode after every change knobs' dependency to be evaluated and reload the page again
      self.reload()
    pop_lis = [i for i in CHANGE_LIST if self.status_of(i) != "active"]
    print("status of this item changed to grayed out/suppressed: {}".format(pop_lis))
    for item in pop_lis:
      CHANGE_LIST.pop(item)
    print(CHANGE_LIST)

  def reload(self):
    self.parent.evaluate_status()
    self.win.destroy()
    self.win = VerticalScrolledFrame(self, relief=tk.SUNKEN, background=GREY)
    self.win.pack(fill=tk.BOTH, expand=True)
    self.make_form(self.win)

  @staticmethod
  def parse_oneof_options(options, default_value, current_value):
    choices = {}
    if isinstance(options, list):
      options = options[0]
    for idx, opt in enumerate(options["option"]):
      _dict_to_process = opt if isinstance(opt, dict) else options["option"]
      val = utils.get_integer_value(_dict_to_process.get("@value"))
      pre_fix = ""
      if val == utils.get_integer_value(current_value, base=10) and val == utils.get_integer_value(default_value, base=10):
        pre_fix = BOTH_CHOICE
      elif val == utils.get_integer_value(default_value, base=10):
        pre_fix = DEFAULT_CHOICE
      elif val == utils.get_integer_value(current_value, base=10):
        pre_fix = CURRENT_CHOICE
      pre_fix += " " if pre_fix else ""
      choices[val] = pre_fix + _dict_to_process.get("@text")
    return choices

  def status_of(self, knob):
    """For the online mode get the status of knobs
    to decide whether to keep the menu item or suppress the menu item

    Args:
      knob: knob option to get the status of

    Returns: string status of the knob
      can be -  "active", "grayedout" "disabled", "suppressed", "unknown"
    """
    return self.parent.status_of(knob)

  @staticmethod
  def get_current_value(field):
    value = CHANGE_LIST.get(field["@name"], {}).get("new_value_int", None)
    if value is None:
      value = field["@CurrentVal"]
    else:
      value = hex(value) if isinstance(value, int) else value
    return value

  def make_form(self, root):
    print("Making form for {} at {}".format(self.page_title, root))
    count = 0
    for option, field in self.knobs.items():
      prompt, setup_type, description = field["@prompt"], field["@setupType"], field["@description"]
      status = self.status_of(field["@name"])
      if status.lower() in ["disabled", "suppressed", "unknown"]:
        continue
      elif status.lower() == "grayedout":
        state = "disable"
      else:
        state = "normal"
      current_value, default_value = self.get_current_value(field), field["@default"]
      txt_cur_val = current_value
      current_value_int = utils.get_integer_value(current_value)
      # add label
      row_label = tk.Label(root, width=MAX_COLUMN_SIZE, text=prompt.strip(), anchor='w', fg=BLUE, bg=GREY,
                           font=LABEL_FONT, padx=PAD_X)
      # add description
      row_description = tk.Label(root, text=field["@description"], anchor='w', fg=BLUE, bg=GREY, font=DESCRIPTION_FONT,
                                 padx=PAD_X)
      # Create a Tkinter variable
      tkvar = tk.StringVar(root)
      # configure selection
      choices = {}
      ent = tk.Entry(root, textvariable=tkvar)
      if setup_type == "oneof":  # dropdown list
        choices = self.parse_oneof_options(options=field["options"], default_value=default_value,
                                           current_value=current_value)
        choice_list = list(choices.values())
        txt_cur_val = choices.get(current_value_int)
        ent = tk.OptionMenu(root, tkvar, *choice_list)
        tkvar.set("{}".format(txt_cur_val))
      elif setup_type == "checkbox":
        tkvar = tk.IntVar(value=current_value_int)
        ent = tk.Checkbutton(root, variable=tkvar)
        ent.config(bg=GREY)
      elif setup_type == "numeric":
        ent = IntegerEntry(root, textvariable=tkvar, current_value=current_value_int)
        tkvar.set("{}".format(current_value))
      elif setup_type == "string":
        ent = tk.Entry(root, textvariable=tkvar)
        tkvar.set("{}".format(current_value))
      else:
        err_msg = "Encountered Invalid setup type `{}`".format(setup_type)
        log(level="ERROR", title="Invalid setup option", message=err_msg)
      ent.config(state=state)
      if setup_type in ["numeric", "string"]:
        ent.bind("<Return>",
                 lambda *args, ent=ent, tkvar=tkvar, txt_cur_val=txt_cur_val, field=field, choices=choices:
                 self.on_changed(ent, tkvar, txt_cur_val, field, choices, *args))
      else:
        tkvar.trace("w",
                    lambda *args, ent=ent, tkvar=tkvar, txt_cur_val=txt_cur_val, field=field, choices=choices:
                    self.on_changed(ent, tkvar, txt_cur_val, field, choices, *args))

      for i in [root, row_label]:
        i.config(bg=GREY)

      row_label.grid(row=count, column=0, pady=1)
      ent.grid(row=count, column=1, sticky="nsew", padx=10, pady=1)
      row_description.grid(row=count, column=2, sticky="w", padx=10, pady=1)

      count += 1

      # configure tooltip on hovering
      if len(prompt) > 50:
        create_tool_tip(row_label, field["@name"] + utils.string_splitter(prompt))
      else:
        create_tool_tip(row_label, field["@name"])
      if len(description) > 50:
        create_tool_tip(row_description, utils.string_splitter(description))
    return True


class MainView(tk.Frame):
  """Constructs Main Root window view
  """

  def __init__(self, bios_bin, publish_all=True, *args, **kwargs):
    """
    Accepts all the tk.Frame arguments and kwargs for
    detail of which arguments are accepted look for the
    base class

    Args:
        publish_all:
    Args:
      *args: as per base class
      bios_bin: absolute path to bios binary/rom, Platform Configuration
                xml or any valid access mode specified in global constant utils.VALID_ACCESS_METHODS
      publish_all:
      **kwargs: as per base class and additional arguments listed below
    """
    self.args, self.kwargs = args, kwargs
    self.offline_xml = None
    self.root = None
    self.bios_bin = bios_bin
    self.publish_all = publish_all

    self.configure_window()
    self.validate_arg()

    # initialize frame
    tk.Frame.__init__(self, *args, **kwargs)

    self.menubar = tk.Menu(self.root)  # create menu bar on root window
    # set publish_all flag (always true for offline xml, and can be set via commandline for online xml)
    self.publish_all = is_offline_xml(self.get_xml()) or self.publish_all
    print("-> Publish All Knobs: {}".format(self.publish_all))
    self.bios_version = utils.get_bios_version(self.get_xml(save_xml=False))  # fetch the bios version from xml
    self.knobs = utils.get_bios_knobs(self.get_xml(save_xml=False))  # get knobs from xml in form of dict
    self.evaluated_depex = {}  # empty dict to store the status of knobs
    self.evaluate_status()  # evaluate status of all the knobs in xml
    self.knob_tree = self.refine_knobs(self.knobs)  # refine the parsed knobs from xml with menu hierarchy
    self.verification_tree = json.load(open(KNOB_JSON_PATH, "r", encoding="utf-8"))
    self.container, self.bottom_buttons = None, None
    self.main_page_title = "BIOS Setup Option ({} : {})".format(self.mode.capitalize(), self.bios_version)
    title = tk.Label(self.root, text=self.main_page_title, font=('Helvetica', 18, 'bold'), bg=GREY, fg=BLUE)
    title.pack()

    self.create_containers()
    self.construct_main_view()
    self.pack_buttons()
    # pack the main view
    self.pack(side="top", fill="both", expand=True)

    # run the window
    self.root.mainloop()

  def configure_window(self):
    """Creates and configures root window
    """
    if self.root is not None:
      self.root.destroy()
    self.root = tix.Tk()  # make root window
    # rename the title of the window
    self.root.title(WINDOW_TITLE)
    # set window background
    self.root.config(bg=GREY)
    # set window size
    self.root.wm_geometry(WINDOW_SIZE)

  def validate_arg(self):
    """Validates the commandline arguments passed to the
    commandline and sets the work mode based on the argument
    Returns:
      True if valid offline xml or bios bin/rom file or valid access mode
    """
    print("Validating 1st argument: {}".format(self.bios_bin))
    # if argument is file then work on offline mode otherwise work in online mode
    if os.path.isfile(self.bios_bin):
      self.mode = "offline"
      if os.path.splitext(self.bios_bin)[-1].lower() not in VALID_OFFLINE_EXTENSIONS:
        err_msg = "Invalid Extension"
        log(level="ERROR", title="Invalid File Type", message=err_msg, alert=True)
        self.root.destroy()
        self.root.quit()
      if self.bios_bin.endswith(".xml"):
        # if argument is xml then define offline_xml for working of script
        self.offline_xml = self.bios_bin
        self.publish_all = is_offline_xml(self.get_xml()) or self.publish_all
    elif self.bios_bin.lower() in utils.VALID_ACCESS_METHODS:
      # work on online mode if valid access method
      self.mode = "online"
      cli.clb._setCliAccess(self.bios_bin)
      self.log_cli_err()
      status = cli.clb.ConfXmlCli()
      if status == 0:
        # XmlCli supported and enabled
        pass
      elif status == 1:
        err_msg = "XmlCLi is not supported on the current BIOS or System BIOS has not completed boot"
        log(level="ERROR", title="XmlCli not supported", message=err_msg, alert=True)
        self.restart()
      elif status == 2:
        err_msg = "XmlCLi is supported but is not enabled, the script has now enabled it and SUT needs reboot to make use of XmlCli"
        log(level="WARNING", title="XmlCli not supported", message=err_msg, alert=True)
        self.root.quit()
    else:
      raise Exception("Invalid argument passed. Please specify valid file or access mode")
    return True

  @staticmethod
  def log_cli_err(root_window=None, _quit=None):
    """Log and Alert for error in GUI thrown by xmlcli
    """
    status = cli.clb.LastErrorSig
    if status != 0:
      err_str = cli.clb.LastErrorSigDict.get(status)
      log(level="ERROR", title="Error 0x{:x}".format(status),
          message="Error 0x{:x}: {}".format(status, err_str), alert=True)
      if _quit:
        log(message="Quitting...", alert=False)
        root_window.quit()
        raise Exception(err_str)
    return True

  def evaluate_status(self):
    """Evaluate the depex for all the knobs
    and store it in dictionary self.evaluated_depex
    """
    if not self.publish_all:
      print("Evaluating Status of knobs...")
      if self.evaluated_depex:
        cli.prs.eval_knob_depex(0, self.evaluated_depex)
      # self.log_cli_err()
      else:
        cli.prs.eval_knob_depex(self.get_xml(save_xml=False), self.evaluated_depex)
        self.log_cli_err()
      return self.evaluated_depex

  def status_of(self, knob):
    """For the online mode get the status of knobs
    to decide whether to keep the menu item or suppress the menu item

    Args:
      knob: knob option to get the status of

    Returns: string status of the knob
      can be -  "active", "grayedout" "disabled", "suppressed", "unknown"
    """
    return self.evaluated_depex.get(knob, {}).get("SetupPgSts", "active").lower()

  def create_containers(self):
    """Create Frame for content and buttons at the bottom
    """
    self.bottom_buttons = tk.Frame(self, bg=GREY)
    self.container = tk.Frame(self, bg=GREY)

    self.bottom_buttons.pack(in_=self, fill="x", side=tk.BOTTOM, expand=False)
    self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

  def restart(self, save_xml=True):
    """Restart the GUI

    Args:
      save_xml: specify whether to call the cli.savexml()
                function or while restarting GUI

    Returns:

    """
    # self.pack_forget()
    self.container.destroy()  # destroy Frame of content
    self.bottom_buttons.destroy()  # destroy the Frame of bottom buttons
    self.bios_version = utils.get_bios_version(self.get_xml(save_xml=save_xml))
    self.knobs = utils.get_bios_knobs(self.get_xml(save_xml=False))
    self.knob_tree = self.refine_knobs(self.get_xml(save_xml=False))

    self.create_containers()
    self.pack_buttons()
    self.construct_main_view()
    self.pack(side="top", fill="both", expand=True)

  def hard_reset(self):
    """Equivalent to restart but also removes
    the content of CHANGE_LIST

    Returns:

    """
    global CHANGE_LIST
    if self.evaluated_depex:
      for knob_name in CHANGE_LIST:
        self.evaluated_depex[knob_name]["CurVal"] = self.get_current_value_of(self.verification_tree, CHANGE_LIST[knob_name]["hierarchy"])

      if not self.publish_all:
        # for online mode after discard change re-evaluates knobs' dependency and reload the page again
        self.evaluate_status()

    CHANGE_LIST = {}
    self.restart(save_xml=False)

  @staticmethod
  def get_current_value_of(knob_tree, hierarchy):
    knob_dict = get_from_dict(knob_tree, hierarchy)
    return knob_dict["@CurrentVal"]

  def discard_changes(self):
    """Discard the changes and restart the GUI
    """
    global CHANGE_LIST
    if CHANGE_LIST:
      self.hard_reset()
    else:
      err_msg = "No changes to be discard"
      log(level="WARNING", message=err_msg)

  def get_xml(self, save_xml=True):
    """Get the existing xml or new xml based on
    the working mode

    Args:
      save_xml: specify whether to re-read the xml or not

    Returns:

    """
    if self.mode == "online":
      if save_xml:
        cli.savexml()
        self.log_cli_err(root_window=self.root, _quit=True)
      return cli.clb.PlatformConfigXml
    else:  # offline mode
      if self.offline_xml:  # if xml is given by user
        return self.offline_xml
      else:
        if save_xml:  # if bios bin/rom file is given by user
          cli.savexml(cli.clb.PlatformConfigXml, self.bios_bin)
          self.log_cli_err(root_window=self.root, _quit=True)
        return cli.clb.PlatformConfigXml

  def construct_main_view(self):
    """Start constructing main view

    Returns:

    """
    self.menubar = tk.Menu(self.root, font="Verdana 12")
    self.root.config(menu=self.menubar)
    for page_name, value in self.knob_tree.items():
      if page_name == "???" and not self.publish_all:
        continue
      knobs = value.pop("knobs")
      menu_title = tk.Menu(self.menubar, tearoff=0, font="Verdana 12")
      menu_title.add_separator()
      self.menubar.add_cascade(label=page_name, menu=menu_title)
      self.page_maker(bg=DARK_BLUE, border=0, parent_menu=menu_title, page_name=page_name, knobs=knobs, child=value)

  def pack_buttons(self):
    """Create button at bottom of window
    """
    save_button = tk.Button(self.bottom_buttons, text="Push Changes", command=self.save_changes)
    save_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(save_button, "Apply changes to system if online mode else to `bin/rom` file, (N/A for offline xml)")

    change_list_button = tk.Button(self.bottom_buttons, text="View Changes", command=self.create_change_pane)
    change_list_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(change_list_button, "View saved changes in new window")

    exit_button = tk.Button(self.bottom_buttons, text='Exit',
                            command=lambda *args, window=self.root: self.close(window))
    exit_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(exit_button, "Exit the GUI")

    restart_button = tk.Button(self.bottom_buttons, text='Reload', command=self.restart)
    restart_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(restart_button, "Reload the GUI")

    discard_changes_button = tk.Button(self.bottom_buttons, text='Discard Changes', command=self.discard_changes)
    discard_changes_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(discard_changes_button, "Discard any change made, any value if modified are restored to current value (`CurrentVal`) of knob xml file")

    defaults_button = tk.Button(self.bottom_buttons, text='Load Defaults', command=self.load_defaults)
    defaults_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)
    create_tool_tip(defaults_button, "Restore to default values and revert any changes made")
    if self.mode == "offline":
      if self.bios_bin.endswith(".xml"):
        save_button.config(state="disable")
      defaults_button.config(state="disable")

  def load_defaults(self):
    """Load default values
    """
    if self.mode == "online":
      status = cli.CvLoadDefaults()
      self.log_cli_err()
      if status != 0:
        level = "ERROR"
        msg = "Unable to Load the default values"
      else:
        level = "INFO"
        msg = "Default Values are loaded"
      log(level=level, message=msg)
    return False

  def save_changes(self, output_location=OUTPUT_INI_LOCATION, output_ini_name="VirtualBiosSetup.ini"):
    """Save changes made to the output file
    Also write the changes to the hardware if working on online mode

    Args:
      output_location: absolute output folder path for ini location
      output_ini_name: Name of output ini file

    Returns:

    """
    content = "; This file was generated using Virtual Bios Setup Page app\n\n[BiosKnobs]\n"
    if self.offline_xml:
      log(level="WARNING", title="Warning!!", message="Push not applicable for XML file as an input", alert=True)
      return False

    if not CHANGE_LIST:
      log(level="WARNING", title="Warning!!", message="No changes to push", alert=True)
      return False

    for knob, value in CHANGE_LIST.items():
      val = value.get("new_value_int")
      val = hex(val) if isinstance(val, int) else val
      content += "{}={}\n".format(knob, val)

    os.makedirs(output_location, exist_ok=True)
    output_path = os.path.join(output_location, output_ini_name)
    with open(output_path, "w") as f:
      f.write(content)

    cli.clb.KnobsIniFile = output_path
    status = None
    out_bin_file = ""
    if self.mode == "online":
      status = cli.CvProgKnobs()
      self.log_cli_err()
      if status == 0:
        status = cli.CvReadKnobs()
        self.log_cli_err()
    elif self.mode == "offline":
      out_bin_file = filedialog.asksaveasfilename(initialdir=os.path.dirname(cli.clb.OutBinFile),
                                                  initialfile=os.path.basename(cli.clb.OutBinFile),
                                                  title="Select File location to store",
                                                  filetypes=(("Bios image", "*.rom"), ("Binary files", "*.bin"), ("All files", "*.*")))
      status = cli.CvProgKnobs(0, self.bios_bin, BiosOut=out_bin_file)
      self.log_cli_err()
      if status == 0:
        status = cli.CvReadKnobs(0, out_bin_file)
        self.log_cli_err()
    if status == 0:
      log(level="INFO", message="Knob updated", alert=False)
    elif status != 0:
      err_msg = "Error verifying the knob changes"
      log(level="ERROR", message=err_msg, alert=True)
    else:
      err_msg = "Error programming the knob changes"
      log(level="ERROR", message=err_msg, alert=True)

    # GUI dialog for success/failure
    if CHANGE_LIST:
      text = "Changes Applied."
      if self.mode != "online":
        text += "New binary generated at: {}".format(out_bin_file)
    else:
      text = "No Changes to be applied: status: {}".format(status)
    status = "INFO" if bool(CHANGE_LIST and status == 0) else "ERROR"
    log(level=status, title=status, message=text)
    self.hard_reset()

  @staticmethod
  def close(window):
    """Destroys/clears all the content of specified frame/window

    Args:
      window: window to be reset

    Returns:

    """
    window.destroy()

  def create_change_pane(self):
    """Create separate window to display change list

    Returns:

    """
    new_window = tk.Toplevel(self.root)  # root to the new window
    new_window.geometry("500x200")
    new_window.after(1, lambda: new_window.focus_force())  # add focus to new window
    new_window.bind('<Escape>', lambda *args, window=new_window: self.close(window))  # bind escape key with exit window
    new_window.title("Change List")

    win = VerticalScrolledFrame(new_window, relief=tk.SUNKEN, background=GREY)
    win.pack(fill=tk.BOTH, expand=True)  # fill window

    headers = ["Xml Knob Name", "New Value", "Previous Value"]  # headers for the grid/change table
    row_cnt = 0
    for idx, header in enumerate(headers):
      # write headers
      tk.Label(win, text=header, bg=GREY, font="Verdana 10 bold").grid(row=row_cnt, column=idx, sticky="nswe",
                                                                       padx=PAD_X, pady=PAD_Y)
    row_cnt += 1
    for knob, detail in CHANGE_LIST.items():
      # write changes one by one on the window
      values = [knob, "{} ({})".format(detail.get("new_value"), hex(detail.get("new_value_int"))),
                "{} ({})".format(detail.get("previous_value_str"), detail.get("previous_value"))]
      for idx, item in enumerate(values):
        item = tk.Label(win, text=item, bg=GREY, font="Verdana 8")
        item.grid(row=row_cnt, column=idx, padx=PAD_X, pady=PAD_Y, sticky="w")
      row_cnt += 1

  def add_knob_page(self, knobs, page_title):
    """Method to create knob page when requested

    Args:
      knobs: list of knobs
      page_title: title of the page/parent menu

    Returns:

    """
    p = DynamicPage(*self.args, highlightbackground=DARK_BLUE, borderwidth=1, page_title=page_title, knobs=knobs,
                    parent=self, **self.kwargs)
    p.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
    p.show()

  def page_maker(self, bg, border, parent_menu, page_name, knobs, child):
    """make a recursive hiearachial menus

    Args:
      bg: background color for the child page
      border: border size
      parent_menu: link the parent to the menu hierarchy
      page_name: name of the current page/menu option
      knobs: list of knobs under the current page
      child: list of child menu/pages

    Returns:

    """
    if knobs:
      parent_menu.add_command(label="knobs", command=lambda: self.add_knob_page(knobs=knobs, page_title=page_name))
    if knobs and child:
      parent_menu.add_separator()
    for label, value in child.items():
      child_knobs = value.pop("knobs")
      child_menu = tk.Menu(parent_menu, tearoff=False, font="Verdana 12")
      parent_menu.add_cascade(label=label, menu=child_menu)
      self.page_maker(bg=bg, border=border, parent_menu=child_menu, page_name=label, knobs=child_knobs, child=value)

  def refine_knobs(self, write_to_file=True):
    """Refine the knobs which are parsed from xml as dict
    as per the require hierarchy

    Args:
      write_to_file: boolean value to determine whether to write back changes or not.

    Returns: dictionary of pages and knobs hierarchy

    """
    pages = {}
    options_to_parse = ["oneof", "numeric", "checkbox", "string"]
    cnt = 0
    for knob in self.knobs:
      if knob.get("@setupType") not in options_to_parse or "@SetupPgPtr" not in knob:
        cnt += 1
        continue
      hierarchy_path = get_hierarchy(knob)
      hierarchy = get_path_hierarchy(hierarchy_path)
      set_in_dict(pages, hierarchy, knob)
    print("{} knobs skipped".format(cnt))
    if write_to_file:
      with open(KNOB_JSON_PATH, "w") as f:
        json.dump(pages, f, indent=4)
    return pages


class PromptGui(object):
  def __init__(self):
    self.col_size = 20
    self.options = ["online", "offline"]
    self.work_on = None
    self.publish_all = False
    self.root = tk.Tk()

    self.start()
    self.arg_window()

    self.root.mainloop()

  def create_containers(self):
    """Create Frame for content and buttons at the bottom
    """
    self.bottom_buttons = tk.Frame(self.root, bg=GREY)
    self.container = tk.Frame(self.root, bg=GREY)

    self.bottom_buttons.pack(in_=self.root, fill="x", side=tk.BOTTOM, expand=False)
    self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

  def start(self):
    self.root.title("Initial Configuration")
    self.root.eval('tk::PlaceWindow . center')
    self.create_containers()

  def restart(self):
    self.root.destroy()
    self.root = tk.Tk()

    self.start()
    self.arg_window()

    self.root.mainloop()

  def trace_option(self, ent, tkvar, offlines):
    value = tkvar.get()
    if value.lower() == "offline":
      self.work_on = filedialog.askopenfilename()
      if not self.work_on:
        # no file selected
        tkvar.set("---")
        log(level="WARNING", title="No File Selected!!", message="Please select valid bin/rom or xml file", alert=False)
      elif os.path.splitext(self.work_on)[-1].lower() not in VALID_OFFLINE_EXTENSIONS:
        # invalid file type selected
        tkvar.set("---")
        err_msg = "Invalid Extension"
        log(level="ERROR", title="Invalid File Type", message=err_msg, alert=True)
      else:
        # valid offline file type
        for entry in offlines:
          entry.config(state="disable")
        if self.work_on.endswith(".xml"):
          if is_offline_xml(self.work_on):
            self.publish_all = True
            self.publish_var.set(1)
            self.publish.config(state="disable")
        log(level="INFO", message="Loading File: {}".format(self.work_on), alert=False)
    elif value.lower() == "online":
      for entry in offlines:
        entry.config(state="normal")
    else:
      self.work_on = value
    return value

  def arg_window(self):
    self.mode_var = tk.StringVar(self.container)
    mode_label = tk.Label(self.container, width=self.col_size, text="Working mode")
    self.mode = tk.OptionMenu(self.container, self.mode_var, *self.options)
    self.mode_var.set("---")

    self.access_var = tk.StringVar(self.container)
    access_method_label = tk.Label(self.container, width=self.col_size, text="Access Method")
    self.access_method = tk.OptionMenu(self.container, self.access_var, *utils.VALID_ACCESS_METHODS)
    self.access_var.set("---")

    self.publish_var = tk.IntVar()
    publish_label = tk.Label(self.container, width=self.col_size, text="Publish All?")
    self.publish = tk.Checkbutton(self.container, variable=self.publish_var)

    form_options = [(mode_label, self.mode), (access_method_label, self.access_method),
                    (publish_label, self.publish)]
    for row, form_option in enumerate(form_options):
      for col, ent in enumerate(form_option):
        ent.grid(row=row, column=col, pady=PAD_Y, padx=1, sticky="nsew")

    create_tool_tip(self.mode, "Select Valid Working mode Online- for SUT and offline - to run bios binary or xml")
    create_tool_tip(self.access_method, "select valid access method for online mode from GUI dropdown menu")
    create_tool_tip(self.publish, "Publish All the knobs without evaluating dependency expression if selected")

    self.mode_var.trace("w", lambda *args, ent=self.mode, tkvar=self.mode_var,
                                    offlines=(self.access_method,): self.trace_option(ent, tkvar, offlines))

    self.access_var.trace("w", lambda *args, ent=self.access_method, tkvar=self.access_var,
                                      offlines=(self.access_method, self.publish, self.mode): self.trace_option(ent, tkvar, offlines))

    save_button = tk.Button(self.bottom_buttons, text="Run Virtual Setup Options with this settings", command=self.save_changes)
    save_button.pack(side=tk.LEFT, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)

  def save_changes(self):
    if self.work_on:
      self.root.destroy()
      self.root.quit()
      self.publish_all = bool(self.publish_var.get())
      print(self.work_on, self.publish_all)
      MainView(bg=GREY, bios_bin=self.work_on, publish_all=self.publish_all)
    else:
      log(level="ERROR", message="Please select valid settings first", alert=True)


def gen_gui():
  """Main function Entry point

  Creates GUI using commandline arguments

  Returns: None

  """
  if len(sys.argv) <= 1:
    prompt_gui = PromptGui()
  else:
    work_on = sys.argv[1]  # loads first argument from commandline
    publish_all = bool(sys.argv[2] == "pa") if len(sys.argv) > 2 else False  # loads second argument from commandline

    # call the class MainView with parsed commandline arguments
    self = MainView(bg=GREY, bios_bin=work_on, publish_all=publish_all)


if __name__ == "__main__":
  gen_gui()
