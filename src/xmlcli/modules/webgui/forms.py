# -*- coding: utf-8 -*-

# Built-in imports
import sys

# Python Modules
import wtforms

# Custom imports
from xmlcli.common import utils
from xmlcli.common import uefi_nvar

__author__ = "Gahan Saraiya"


KNOB_TYPES = [(None, 'Please select an option'),
              ('oneof', 'oneof'), ('string', 'string'), ('numeric', 'numeric'), ('checkbox', 'checkbox'), ('reserved', 'reserved')]

NvarDetails = uefi_nvar.create_nvar_structure


######################################################################################################################################################
# Forms
######################################################################################################################################################
class FormHelper(wtforms.Form):
  """Helper Class to create wtforms"""
  def fetch_values(self):
    result = {k: v.data for k, v in self._fields.items() if k != "submit"}
    return result


class CreateNvarForm(FormHelper):
  """Form to get input to create Nvar"""
  name = wtforms.StringField('NVAR name', validators=[wtforms.validators.DataRequired()],
                             render_kw={'class': 'form-control',
                                        'data-toggle'   : 'tooltip',
                                        'data-placement': 'right',
                                        'placeholder': 'Enter NVAR Name (only alphabets and numbers allowed)',
                                        'type': 'text',
                                        'pattern': '[a-zA-Z0-9]+'
                                        })
  guid = wtforms.StringField('GUID', validators=[wtforms.validators.DataRequired()],
                             render_kw={'class': 'form-control',
                                        'data-toggle'   : 'tooltip',
                                        'data-placement': 'right',
                                        'placeholder': '0x12345678-0x1234-0x1234-0x12-0x22-0x32-0x42-0x52-0x62-0x72-0x82',
                                        'type': 'text',
                                        'pattern': '[a-zA-Z0-9-]+'
                                        })
  # size = wtforms.StringField('Size',
  #                            # validators=[wtforms.validators.DataRequired("Please Enter Valid decimal Number")],
  #                            render_kw={'class': 'form-control',
  #                                       'ng-chang': 'IntToHex',
  #                                       'placeholder': 'Enter Size in decimal (hex representation will be displayed when you enter the number)',
  #                                       'pattern': '[0-9]+'
  #                                       })
  attributes = wtforms.StringField("Attributes",
                                   default="0x7",
                                   render_kw={'class': 'form-control',
                                              'data-toggle'   : 'tooltip',
                                              'data-placement': 'right',
                                              'disabled': 'true'})
  submit = wtforms.SubmitField('Submit',
                               render_kw={'class': 'btn btn-primary'})


class CreateKnobForm(FormHelper):
  """Form to create Knob under selected Nvar"""
  knob_type = wtforms.SelectField('Knob Type', validators=[wtforms.validators.InputRequired()],
                                  coerce=str,
                                  choices=KNOB_TYPES,
                                  render_kw={'class': 'custom-select',
                                             'data-toggle'   : 'tooltip',
                                             'data-placement': 'right',
                                             'placeholder': 'Enter Type of the Knob'})
  name = wtforms.StringField('Name', validators=[wtforms.validators.DataRequired()],
                             render_kw={'class': 'form-control',
                                        'data-toggle': 'tooltip',
                                        'data-placement': 'right',
                                        'placeholder': 'Enter Name of the Knob',
                                        'pattern': '[a-zA-Z0-9]+'})
  description = wtforms.TextAreaField('Description', validators=[wtforms.validators.DataRequired()],
                                      render_kw={'class': 'form-control',
                                                 'data-toggle': 'tooltip',
                                                 'data-placement': 'right',
                                                 'placeholder': 'Enter Description for the knob'})
  size = wtforms.IntegerField('Size', validators=[wtforms.validators.DataRequired("Please Enter Valid Number")],
                              default=1,
                              render_kw={'class': 'custom-range',
                                         'data-toggle'   : 'tooltip',
                                         'data-placement': 'right',
                                         'type': 'range',
                                         'value': 1,
                                         'placeholder': 'Enter Size',
                                         'min': 1,
                                         'max': 8
                                         })
  offset = wtforms.IntegerField('Offset', validators=[wtforms.validators.InputRequired()],
                                render_kw={'class': 'form-control',
                                           'data-toggle'   : 'tooltip',
                                           'data-placement': 'right',
                                           'type': 'number',
                                           'value': 1,
                                           'disabled': 'true',
                                           'placeholder': 'Enter Offset at which to add the knob'})


class SelectInterfaceForm(FormHelper):
  interface = wtforms.SelectField('Access Mode', validators=[wtforms.validators.InputRequired()],
                                  coerce=str,
                                  choices=[(None, 'Please select an option')] + [(i, i) for i in utils.VALID_ACCESS_METHODS + ["stub"]],
                                  default="linux" if sys.platform == "linux" else "winrwe",
                                  render_kw={'class': 'custom-select',
                                             'data-toggle'   : 'tooltip',
                                             'data-placement': 'right',
                                             'placeholder': 'Enter Interface to be used to access xmlcli on SUT'})
  xml_location = wtforms.StringField('XML Location',
                                     render_kw={'class': 'form-control',
                                                'data-toggle': 'tooltip',
                                                'data-placement': 'right',
                                                'title': 'Enter the xml file location to be operate this gui on',
                                                'placeholder': 'Enter the xml file location to be operate this gui on'})
  submit = wtforms.SubmitField('Submit',
                               render_kw={'class': 'btn btn-primary'})


if __name__ == "__main__":
  pass
