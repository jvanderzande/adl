import logging
from lxml import etree
from .xml_tools import ADEPT_NS, NSMAP, add_subelement
from .api_call import Activate
from .bom import Device
from . import data

logger = logging.getLogger(__name__)

###### Register devices
def device_register(mountpoint):
  logger.info("Looking for ADEPT support on {}".format(mountpoint))
  d = read_device_file(mountpoint)
  if d is None:
    logger.error("This device does not seem to support ADEPT DRM")
    return

  current_account = data.get_current_account()
  if current_account is None:
    logger.error("Please log in with a user and select it first")

  # Check it is not already in our db
  devices = current_account.devices
  for device in devices:
    if device.fingerprint == d.fingerprint:
      print("Device already exists in the DB")
      return

  # Check if it is not already activated
  username, plk, device_id = read_activation_file(mountpoint)

  if username is not None and plk is not None:
    # Already activated
    a = data.find_account_by_sign(username)
    if a is not None:
      if a.get_private_key() == plk:
        # Activated by a known user
        logger.info("Device is already activated for user {} but is not known by adl, registering it".format(username))
        d.device_id = device_id
        data.add_device(a.urn, d)
        return

    logger.error("Device is already activated for an unknown user. Doing nothing or all books on the device will become unreadable")
    return 

  # Activate device
  logger.info("Activating device ...")
  activation_token = activate(current_account, d)
  if activation_token is None:
    logger.error("Activation failed")
    return

  # Store file in the device
  activation_file_content = build_activation_file(current_account, activation_token, data.config)
  logger.debug(activation_file_content)

  if write_activation_file(mountpoint, activation_file_content):
    # Store info in db
    data.add_device(current_account.urn, d)
    print("Activation successful")
  else:
    print("Error while writing activation file")

  return

def activate(acc, d):
  act = Activate(acc, d)
  return act.call() 

def read_device_file(mountpoint):
  try:
    with open("{}/.adobe-digital-editions/device.xml".format(mountpoint), "r") as device_file:
      d = Device()
      tree_root = etree.fromstring(device_file.read())
      d.name = tree_root.find("{http://ns.adobe.com/adept}deviceName").text
      d.type = tree_root.find("{http://ns.adobe.com/adept}deviceType").text
      d.fingerprint = tree_root.find("{http://ns.adobe.com/adept}fingerprint").text

      print(("Found device: {}".format(d)))
      return d

  except Exception:
    print("Could not find device. Maybe it doesn't support ADEPT DRM ?")
    return None

def read_activation_file(mountpoint):
  try:
    with open("{}/.adobe-digital-editions/activation.xml".format(mountpoint), "r") as activation_file:
      tree_root = etree.fromstring(activation_file.read())
      creds = tree_root.find("{http://ns.adobe.com/adept}credentials")
      username = creds.find("{http://ns.adobe.com/adept}username").text
      plk = creds.find("{http://ns.adobe.com/adept}privateLicenseKey").text

      at = tree_root.find("{http://ns.adobe.com/adept}activationToken")
      device_id = at.find("{http://ns.adobe.com/adept}device").text

      logger.info("This device is already activated for user {}".format(username))
      return username, plk, device_id
  except Exception:
    logger.info("Activation data not found")

  return None, None, None

def write_activation_file(mountpoint, content):
  try:
    with open("{}/.adobe-digital-editions/activation.xml".format(mountpoint), "w") as activation_file:
      activation_file.write(content)
  except Exception:
    logging.exception("Error while updating device !")
    return False

  return True

def build_activation_file(acc, reply, config):
  xml = etree.Element("{%s}activationInfo" % ADEPT_NS, nsmap=NSMAP)

  service = etree.Element("{%s}activationServiceInfo" % ADEPT_NS, nsmap=NSMAP)
  xml.append(service)
  add_subelement(service, "authURL", config.auth_url)
  add_subelement(service, "userInfoURL", config.userinfo_url)
  add_subelement(service, "activationURL", config.auth_url)
  add_subelement(service, "certificate", config.activation_certificate)

  cred = etree.Element("{%s}credentials" % ADEPT_NS, nsmap=NSMAP)
  xml.append(cred)
  add_subelement(cred, "user", acc.urn)
  add_subelement(cred, "licenseCertificate", acc.licenseCertificate)
  add_subelement(cred, "privateLicenseKey", acc.get_private_key())
  add_subelement(cred, "authenticationCertificate", config.authentication_certificate)
  user = etree.Element("username", attrib = {"method": acc.sign_method})
  user.text = acc.sign_id
  cred.append(user)

  activationToken = etree.fromstring(reply)
  xml.append(activationToken)

  return etree.tostring(xml)
  
