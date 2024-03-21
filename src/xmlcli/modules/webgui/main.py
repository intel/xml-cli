# -*- coding: utf-8 -*-

# Built-in imports
import os
import sys
import json
import html
import threading
import functools
import webbrowser

# Python Modules
import flask
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from werkzeug.middleware.shared_data import SharedDataMiddleware


# Custom imports
from xmlcli.common import utils
from . import db
from . import forms
from . import flask_toastr

from xmlcli import XmlCli as cli
from xmlcli.common import logger

# Flask settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_HTML = os.path.join(BASE_DIR, "index.html")
DEBUG = False
app = flask.Flask(__name__)
toastr = flask_toastr.Toastr(app)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = os.urandom(30)

# CSRF Protection
csrf = SeaSurf(app)

# Content Security Policy
csp = {
    'default-src': [
        '\'self\'',
        '*.cdnjs.cloudflare.com',
        '*.code.jquery.com',
        ],
    'img-src': [ '*', 'data:' ],
    'script-src': [
      '\'self\'',
      '\'unsafe-inline\'',
    ]
}

talisman = Talisman(app, content_security_policy=csp)

# Upload configurations
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"xml"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.add_url_rule('/uploads/<filename>', 'uploaded_file', build_only=True)

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
  '/uploads':  app.config['UPLOAD_FOLDER']
})


sys.path.append(BASE_DIR)

nvar_db = db.NvarDb()
# settings = utils.Setup(log_level="DEBUG", sub_module="webgui", log_file_name="webgui.log", print_on_console=True)
settings = logger.settings
log = settings.logger


######################################################################################################################################################
# Custom Wrappers
######################################################################################################################################################
def xmlcli_enabled_required(f):
  @functools.wraps(f)
  def decorated_function(*args, **kwargs):
    status = 0 if nvar_db.interface == "stub" else cli.clb.ConfXmlCli()
    if status != 0:  # XmlCli is not enabled...
      return flask.redirect(flask.url_for('select_interface', next=flask.request.url))
    return f(*args, **kwargs)
  return decorated_function


######################################################################################################################################################
# Filters
######################################################################################################################################################
@app.template_filter('int_hex')
def int_hex(value):
  result = value
  val = db.get_integer_value(value)
  if val is not False:
    result = "{0} (0x{0:x})".format(val)
  return result


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


######################################################################################################################################################
# View
######################################################################################################################################################
@csrf.include
@app.route('/', methods=['GET'])
@xmlcli_enabled_required
def index():
  """Home Page to the url"""
  return flask.redirect(flask.url_for('display_created_knobs'))

@csrf.include
@app.route('/display_created_knobs', methods=['GET'])
@xmlcli_enabled_required
def display_created_knobs():
  """Displays created Nvar and knobs"""
  show_all = html.escape(flask.request.args.get("show_all", "false")).lower() in ["true", "1", "yes", "y"]
  resp = flask.make_response(flask.render_template('display_created_knobs.html', title="User Created Knobs", created_knobs=nvar_db.all_data, show_all=show_all))
  return resp


@csrf.include
@app.route('/create_nvar', methods=['GET', 'POST'])
def create_nvar():
  """Construct form to create new Nvar"""
  form = forms.CreateNvarForm(flask.request.form)
  if flask.request.method == 'POST':
    validated_data = form.fetch_values()
    if form.validate():
      flask.session["current_nvar"] = validated_data
      validated_data.setdefault("knobs", {})
      nvar_db.create_nvar(data_dict=validated_data)
      flask.flash('NVAR Created', category="success")
      return flask.redirect(flask.url_for('display_created_knobs', show_all=True))
  resp = flask.make_response(flask.render_template('create_nvar.html', title="Create NVAR", form=form, unique_id=utils.generate_unique_id()))
  return resp


@csrf.include
@app.route('/create_knob', methods=['GET', 'POST'])
def create_knob():
  """Construct form to create knobs under the selected Nvar"""
  nvar_key = html.escape(flask.request.args.get("nvar_key", None))
  nvar_data = nvar_db.search_nvar(nvar_key).get("extra_details")
  form = forms.CreateKnobForm(flask.request.form)
  form.offset.render_kw.update({"value": db.get_integer_value(nvar_data["next_offset"])})  # set default offset
  if nvar_db.get_free_space(nvar_key):
    form.size.render_kw.update({"min": 1, "max": min(nvar_db.get_free_space(nvar_key), 8)})
  resp = flask.make_response(flask.render_template('create_knob.html', title="Create Knob", form=form, nvar_data=nvar_data, key=nvar_key))
  return resp

@csrf.include
@app.route('/edit_knob/<nvar_key>/<unique_id>', methods=['GET', 'POST'])
def edit_knob(nvar_key, unique_id):
  """Construct form to edit knob's current value"""
  safe_nvar_key = html.escape(nvar_key)
  safe_unique_id = html.escape(unique_id)
  nvar_data = nvar_db.search_nvar(safe_nvar_key).get("extra_details")
  knob_data = nvar_data["knobs"][safe_unique_id]
  knob_options = json.dumps(knob_data.get("options", {}))
  resp = flask.make_response(flask.render_template('edit_knob.html', title="Edit Knob",
                               knob_data=knob_data, nvar_data=nvar_data, key=safe_nvar_key, unique_id=safe_unique_id, knob_options=knob_options))
  return resp

@csrf.include
@app.route('/access_db/<action_on>/<action>', methods=['GET', 'POST'])
def access_db(action_on="knob", action="create"):
  """Api to create, delete, view the session database of Nvars

  :param action_on: knob|nvar
  :param action: create|delete|view
  :return: nvar structure
  """
  if flask.request.method == "POST":
    data = json.loads(flask.request.get_data())
    key = data.pop("key", None)
    unique_id = data.pop("unique_id", None)
    new_value = data.pop("new_value", None)
    log.info(f"{action_on}\t {action}\t {data}")
    log.info(f"key: {key}")
    log.info(f"unique_id: {unique_id}")
    log.info(f"new_value: {new_value}")
    if action_on == "knob":
      if key:
        if unique_id and action == "view":
          return nvar_db.search_knob(key, unique_id)
        if unique_id and action == "edit":
          print("---------> ", new_value)
          return nvar_db.edit_knob(key, unique_id, new_value)
        if unique_id and action == "delete":
          return nvar_db.delete_knob(key, unique_id)
        elif action == "create":
          unique_id = data["name"]
          return nvar_db.create_knob(key, unique_id, data)
    elif action_on == "nvar":
      if key and action == "view":
        return nvar_db.search_nvar(key)
      elif key and action == "delete":
        return nvar_db.delete_nvar(key)
      elif action == "create":
        return nvar_db.create_nvar(data)
  result = flask.jsonify(nvar_db.all_data)
  return result

@csrf.include
@app.route('/generate_xml', methods=['GET', 'POST'])
def generate_xml():
  nvar_xml_root = nvar_db.construct_xml(get_operation=False)
  nvar_xml = nvar_db.xml_string(nvar_xml_root)
  return flask.Response(nvar_xml, mimetype='text/xml')

@csrf.include
@app.route('/save_xml', methods=['GET', 'POST'])
@xmlcli_enabled_required
def save_xml():
  nvar_xml_root = nvar_db.construct_xml(get_operation=False)
  xml_path = nvar_db.store_xml(nvar_xml_root)
  nvar_xml = nvar_db.xml_string(nvar_xml_root)
  return flask.Response(nvar_xml, mimetype='text/xml')


@csrf.include
@app.route('/save_nvar', methods=['GET', 'POST'])
@xmlcli_enabled_required
def save_nvar():
  form = forms.SelectInterfaceForm(flask.request.form)
  if flask.request.method == 'POST':
    validated_data = form.fetch_values()
    if form.validate():
      nvar_xml_root = nvar_db.construct_xml(get_operation=False)
      xml_path = nvar_db.store_xml(nvar_xml_root)
      status = nvar_db.get_response_buffer(operation="set", xml_file=xml_path, interface=validated_data.get("interface"))
      print("Status of nvar save: {}".format(status))
      if status:
        flask.flash('Nvarupdated to SUT successfully', category="success")
        nvar_db.make_xml_backup()
        nvar_db.database = nvar_db.load_verified_xml(nvar_db.xml_location, interface=nvar_db.interface)
        nvar_xml_root = nvar_db.construct_xml(get_operation=False)
        xml_path = nvar_db.store_xml(nvar_xml_root)
        print("Nvar xml at: {}".format(xml_path))
      else:
        flask.flash('Error in saving knobs to SUT (status: {})'.format(status), category="error")
    return flask.redirect(flask.url_for('display_created_knobs'))
  resp = flask.make_response(flask.render_template('store_nvar_to_sut.html', title="Save Nvar", form=form))
  return resp


@csrf.include
@app.route('/select_interface', methods=['GET', 'POST'])
def select_interface():
  form = forms.SelectInterfaceForm(flask.request.form)
  form.xml_location.render_kw.update({"value": nvar_db.xml_location})
  if flask.request.method == 'POST':
    validated_data = form.fetch_values()
    log.debug(validated_data)
    if form.validate():
      interface = validated_data.get("interface")
      xml_location = validated_data.get("xml_location")
      status = 0
      if interface != "stub":
        cli.clb._setCliAccess(interface)
        status = cli.clb.ConfXmlCli()
      if status == 0:
        flask.flash('Interface selected successfully', category="success")
        if os.path.exists(xml_location) and os.path.isfile(xml_location):
          nvar_db.xml_location = xml_location
          nvar_db.interface = interface
          nvar_db.database = nvar_db.load_verified_xml(nvar_db.xml_location, interface=interface)
          log.debug(nvar_db.database)
          return flask.redirect(flask.url_for('display_created_knobs'))
        else:
          error_message = f"Invalid XML location: {xml_location}"
          log.error(error_message)
          return flask.render_template('error.html', title="Error Loading given XML", error_code=status, error_message=error_message)
      else:
        flask.flash('Error in saving knobs to SUT (status: {})'.format(status), category="error")
        error_message = "XmlCli enabled and system REBOOT is required!" if status == 2 else "XmlCli not supported or enabled!"
        log.error(error_message)
        return flask.render_template('error.html', title="Error Enabling XmlCli", error_code=status, error_message=error_message)
  return flask.render_template('store_nvar_to_sut.html', title="Select Interface", form=form)


def run_gui(port=4000):
  url = "https://127.0.0.1:{0}".format(port)
  threading.Timer(1.25, lambda: webbrowser.open(url)).start()
  app.run(host='0.0.0.0', port=port, ssl_context='adhoc')


if __name__ == "__main__":
  run_gui()
