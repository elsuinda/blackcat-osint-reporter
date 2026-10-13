"""Instancia unica de SQLAlchemy, compartida por los modelos y la app."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
