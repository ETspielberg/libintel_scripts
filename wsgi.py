import os

from app import app

os.environ.setdefault("LIBINTEL_SETTINGS", "~/.libintel/config/libintel-scripts.cfg")

if __name__ == "__main__":
    app.run()