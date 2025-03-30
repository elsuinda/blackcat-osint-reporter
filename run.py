#!/usr/bin/env python3
from app import create_app, db
from app.models import User, Report, Log
from flask_migrate import Migrate
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Report=Report, Log=Log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
