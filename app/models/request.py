from app import db
from datetime import datetime, timezone
import uuid

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_query = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='requests')

    def __repr__(self):
        return f"<Request {self.id}>"