from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    picture = db.Column(db.String(100))
    session_token = db.Column(db.String(500), nullable=False)
    session_expiration = db.Column(db.DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<User {self.email}>"