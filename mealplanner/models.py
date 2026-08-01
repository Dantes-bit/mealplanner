from itsdangerous import URLSafeTimedSerializer as Serializer
from mealplanner import db, login_manager
from flask_login import UserMixin
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)
follow_requests = db.Table('follow_requests',
    db.Column('requester_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('requested_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    private = db.Column(db.Boolean, nullable=False, default=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    bio = db.Column(db.Text, default='My bio.')
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(255), nullable=False, default='https://res.cloudinary.com/xx1thsdq/image/upload/v1785588165/e130a2fd081397a9_dn5fr8.png')
    password = db.Column(db.String(60), nullable=False)
    meals = db.relationship('Meal', backref='author', lazy=True)
    monday = db.Column(db.Integer, default=0)
    tuesday = db.Column(db.Integer, default=0)
    wednesday = db.Column(db.Integer, default=0)
    thursday = db.Column(db.Integer, default=0)
    friday = db.Column(db.Integer, default=0)
    saturday = db.Column(db.Integer, default=0)
    sunday = db.Column(db.Integer, default=0)
    monday2 = db.Column(db.Integer, default=0)
    tuesday2 = db.Column(db.Integer, default=0)
    wednesday2 = db.Column(db.Integer, default=0)
    thursday2 = db.Column(db.Integer, default=0)
    friday2 = db.Column(db.Integer, default=0)
    saturday2 = db.Column(db.Integer, default=0)
    sunday2 = db.Column(db.Integer, default=0)
    shopping_list = db.Column(db.Text, nullable=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    pending_requests_sent = db.relationship(
        'User', secondary=follow_requests,
        primaryjoin=(follow_requests.c.requester_id == id),
        secondaryjoin=(follow_requests.c.requested_id == id),
        backref=db.backref('pending_requests_received', lazy='dynamic'),
        lazy='dynamic'
    )

    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def send_follow_request(self, user):
        if not self.has_requested(user):
            self.pending_requests_sent.append(user)

    def cancel_follow_request(self, user):
        if self.has_requested(user):
            self.pending_requests_sent.remove(user)

    def has_requested(self, user):
        return self.pending_requests_sent.filter(follow_requests.c.requested_id == user.id).count() > 0
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    essential = db.Column(db.Boolean, nullable=False, default=True)
    substitute = db.Column(db.String(100), nullable=True)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visibility = db.Column(db.String(20), nullable=False, default='private')
    name = db.Column(db.String(100), nullable=False)
    recipe = db.Column(db.Text, nullable=False)
    time = db.Column(db.String(15), nullable=False)
    image_file = db.Column(db.String(255), nullable=False, default='https://res.cloudinary.com/xx1thsdq/image/upload/v1785588251/default_meal_phepg2.png')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ingredient_list = db.relationship('Ingredient', backref='meal', lazy=True, cascade='all, delete-orphan')

class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)