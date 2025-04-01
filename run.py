#!/usr/bin/env python3
from app import create_app, db
from app.models import User, Report, Log
from flask_migrate import Migrate
import os
from werkzeug.security import generate_password_hash

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Report=Report, Log=Log)

def create_default_admin():
    """Crea el usuario admin predeterminado si no existe."""
    from app.models import User
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Administrator',
            is_admin=True,
            is_ldap=False,
            password_hash=generate_password_hash('SecretPassword')
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado con contraseña predeterminada: SecretPassword")

if __name__ == '__main__':
    os.makedirs(app.config['MEDIA_FOLDER'], exist_ok=True)
    with app.app_context():
        create_default_admin()
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        ssl_context='adhoc' if os.getenv('USE_SSL', 'false').lower() == 'true' else None
    )
