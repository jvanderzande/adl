from .exceptions import DataDirectoryAccessError
from . import db

data = db.DBData()

if not data.check_or_create_dir():
  raise DataDirectoryAccessError()

data.load()
