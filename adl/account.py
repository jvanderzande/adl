import logging

from . import data

logger = logging.getLogger(__name__)

def set_default_account(urn):
  data.set_current_account(urn)

def account_delete(urn):
  a = data.find_account_by_urn(urn)

  if a is None:
    logger.error("Account does not exist")
    return False
  else:
    data.delete_account(a)
    logger.info("Account deleted")

  return True
