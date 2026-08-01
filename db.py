from mealplanner import db, create_app
from mealplanner.models import User
app = create_app()
with app.app_context():
    user = User.query.filter_by(username='Dantes').first()
    user.admin = True
    db.session.commit()