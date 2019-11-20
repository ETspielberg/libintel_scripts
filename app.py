import os

from app import create_app

os.environ.setdefault("LIBINTEL_SETTINGS", "~/.libintel/config/libintel-scripts.cfg")

app = create_app()
