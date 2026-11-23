"""Paste into the PythonAnywhere WSGI configuration after setting the project path."""
import json
import os
import sys
from pathlib import Path

home = Path.home()
project = home / "apps" / "pc-build-planner"
private = home / ".pcbuild-pw2"

os.environ.update(json.loads((private / "runtime.json").read_text(encoding="utf-8")))
sys.path.insert(0, str(project))

from deploy_wsgi import application

