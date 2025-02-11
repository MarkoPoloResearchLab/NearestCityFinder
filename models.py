from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    anchor_city = db.Column(db.String(100), nullable=False)
    closest_city = db.Column(db.String(100), nullable=False)
    driving_distance = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)
    searched_cities = db.Column(db.Text, nullable=False)  # Stored as comma-separated string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'anchor_city': self.anchor_city,
            'closest_city': self.closest_city,
            'driving_distance': self.driving_distance,
            'radius': self.radius,
            'searched_cities': self.searched_cities.split(','),
            'created_at': self.created_at.isoformat()
        }
