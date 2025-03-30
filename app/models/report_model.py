from datetime import datetime
from .db import db

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255))
    system_date = db.Column(db.DateTime, default=datetime.utcnow)
    post_date = db.Column(db.DateTime)
    summary = db.Column(db.Text)
    url = db.Column(db.String(500))
    user_id = db.Column(db.String(100))
    image_path = db.Column(db.String(255))
    is_global = db.Column(db.Boolean, default=False)
    user_id_created = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_number': self.report_number,
            'source': self.source,
            'title': self.title,
            'system_date': self.system_date.isoformat(),
            'post_date': self.post_date.isoformat() if self.post_date else None,
            'summary': self.summary,
            'url': self.url,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'is_global': self.is_global,
            'date_created': self.date_created.isoformat(),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }
