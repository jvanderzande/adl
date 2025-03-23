import logging
import sys

from . import db

logger = logging.getLogger(__name__)
data = db.DBData()

if not data.check_or_create_dir():
  logger.error("Error accessing data directory !")
  sys.exit(1)

data.load()
