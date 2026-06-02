from sqlmodel import create_engine

from app.core.config import settings
from app.models import User, SpeedTest

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

