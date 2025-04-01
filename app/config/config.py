import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    MEDIA_FOLDER = os.path.join(basedir, 'media')
    ALLOWED_MEDIA_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'mp3', 'wav'}
    
    # LDAP Configuration
    LDAP_SERVER = os.environ.get('LDAP_SERVER', 'ldap://localhost')
    LDAP_USER_OU = os.environ.get('LDAP_USER_OU', 'ou=users,dc=example,dc=com')
    LDAP_GROUP_OU = os.environ.get('LDAP_GROUP_OU', 'ou=groups,dc=example,dc=com')
    LDAP_ADMIN_GROUP = os.environ.get('LDAP_ADMIN_GROUP', 'cn=admins,ou=groups,dc=example,dc=com')
    LDAP_USER_GROUP = os.environ.get('LDAP_USER_GROUP', 'cn=users,ou=groups,dc=example,dc=com')
    LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', 'cn=admin,dc=example,dc=com')
    LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', '')

    # Validación de configuraciones críticas
    if not SECRET_KEY or SECRET_KEY == 'default-secret-key':
        raise ValueError("SECRET_KEY no configurado correctamente")
    if not LDAP_BIND_PASSWORD:
        raise ValueError("LDAP_BIND_PASSWORD no configurado")
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
