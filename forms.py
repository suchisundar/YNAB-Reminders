from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Email

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class BudgetForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Submit')

class TransactionForm(FlaskForm):
    payee_name = StringField('Payee Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', choices=[], validators=[DataRequired()])
    memo = StringField('Memo')
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Transaction')

    def populate_categories(self, categories):
        self.category_id.choices = [(cat['id'], cat['name']) for group in categories for cat in group['categories']]