import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://blackcat_user:SecurePassword123!@localhost/blackcat_osint'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # LDAP Configuration
    LDAP_SERVER = os.environ.get('LDAP_SERVER', 'ldap://your-ldap-server')
    LDAP_USER_OU = os.environ.get('LDAP_USER_OU', 'ou=users,dc=example,dc=com')
    LDAP_GROUP_OU = os.environ.get('LDAP_GROUP_OU', 'ou=groups,dc=example,dc=com')
    LDAP_ADMIN_GROUP = os.environ.get('LDAP_ADMIN_GROUP', 'cn=admins,ou=groups,dc=example,dc=com')
    LDAP_USER_GROUP = os.environ.get('LDAP_USER_GROUP', 'cn=users,ou=groups,dc=example,dc=com')
    LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', 'cn=admin,dc=example,dc=com')
    LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', 'password')
    
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
