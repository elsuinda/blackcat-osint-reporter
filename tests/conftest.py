"""Configuracion de pruebas: aisla el estado en un directorio temporal
ANTES de importar el paquete (config.py resuelve rutas en import-time)."""
import os
import tempfile

os.environ["BLACKCAT_HOME"] = tempfile.mkdtemp(prefix="blackcat_test_")

import pytest  # noqa: E402

from blackcat.core import models  # noqa: E402
from blackcat.core.db import db  # noqa: E402
from blackcat.web.app import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    app = create_app(compartido=False)
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    yield app


@pytest.fixture(scope="session")
def app_compartido():
    app = create_app(compartido=True, token="CLAVE-TEST-123")
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    yield app


@pytest.fixture(autouse=True)
def _limpiar(app):
    """Deja la base limpia antes de cada test (salvo perfiles base)."""
    with app.app_context():
        for modelo in (models.Adjunto, models.Hallazgo, models.Caso, models.RegistroActividad):
            modelo.query.delete()
        db.session.commit()
    yield


@pytest.fixture
def cliente(app):
    return app.test_client()
