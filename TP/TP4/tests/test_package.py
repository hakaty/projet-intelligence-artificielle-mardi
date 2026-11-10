"""Le package est installé : métadonnées et commande maintai-predict."""
import os
import shutil
import sysconfig
from importlib.metadata import PackageNotFoundError, version

import maintai


def test_package_is_installed():
    try:
        installed = version("maintai")
    except PackageNotFoundError:
        installed = None
    assert installed == maintai.__version__ == "0.2.0"


def test_command_is_installed():
    # .venv\Scripts (Windows) ou .venv/bin : là où pip crée le .exe de la commande
    scripts = sysconfig.get_path("scripts")
    path = os.pathsep.join([scripts, os.environ.get("PATH", "")])
    assert shutil.which("maintai-predict", path=path) is not None
