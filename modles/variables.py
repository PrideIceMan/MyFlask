from app import db


class Variables(db.Model):

    __tablename__ = 'variables'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(11), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    description= db.Column(db.String(50))