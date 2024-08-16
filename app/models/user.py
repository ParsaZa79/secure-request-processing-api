from app import db
import uuid


class User(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = db.Column(db.Integer, unique=True, nullable=True)
    google_id = db.Column(db.String(50), unique=True, nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    picture = db.Column(db.String(100))
    session_token = db.Column(db.String(500), nullable=True)
    session_expiration = db.Column(db.DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<User {self.email}>"