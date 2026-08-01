from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
    name = StringField('Meal name', validators=[DataRequired()])
    time = StringField('ETA', validators=[DataRequired()])
    recipe = TextAreaField('Recipe', validators=[DataRequired()])
    picture = FileField('Meal Picture', validators=[FileAllowed(['jpg', 'png', 'webp', 'heic'])])
    visibility = SelectField(
        'Visibility',
        choices=[
            ('private', 'Private'),
            ('followers', 'Followers Only'),
            ('public', 'Public')
        ],
        default='private',
        validators=[DataRequired()]
    )
    submit = SubmitField('Create meal')

