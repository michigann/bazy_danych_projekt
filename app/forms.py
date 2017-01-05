from wtforms import Form, StringField, PasswordField, validators, DateField, IntegerField, SelectMultipleField
from wtforms.widgets import ListWidget, RadioInput

from app.db_helper import get_dictionary_item_id
from app.models import User, Airport, Plane


class RegistrationForm(Form):
    email = StringField('email', [
        validators.DataRequired(),
        validators.Length(min=6, max=256)
    ])
    password = PasswordField('new password', [
        validators.DataRequired(),
        validators.Length(min=6, max=30),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('repeat password')

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.get(email=self.email.data)
        if user is not None:
            self.email.errors.append('email address in usage')
            return False

        return True


class LoginForm(Form):
    email = StringField('email', [validators.DataRequired()])
    password = PasswordField('password', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.get(email=self.email.data)
        if user is None:
            self.email.errors.append('wrong email address')
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append('invalid password')
            return False

        self.user = user
        return True


class SearchForm(Form):
    airport_from = StringField('from')
    airport_to = StringField('to')
    departure_date = DateField('departure', format='%Y-%m-%d')


class AddressForm(Form):
    country = StringField('kraj', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    city = StringField('miasto', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    street = StringField('ulica', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    street_number = StringField('numer domu', [
        validators.DataRequired(),
        validators.Length(max=10)
    ])
    flat_number = StringField('numer mieszkania', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    postal_code = StringField('kod pocztowy', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])


class PersonalDataForm(AddressForm):
    personal_number = StringField('pesel', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    fname = StringField('imie', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    lname = StringField('nazwisko', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    birth = DateField('data urodzenia', [validators.DataRequired()], format='%Y-%m-%d')
    nationality = StringField('narodowosc', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])


class MultiRadioField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = RadioInput()


class BookTicketForm(PersonalDataForm):
    choose_ticket = MultiRadioField('wybierz bilet', validators=[validators.DataRequired()], coerce=int)


class BackOfficeLoginForm(LoginForm):
    def validate(self):
        if not LoginForm.validate(self):
            return False
        if self.user.id_rank != get_dictionary_item_id('user', 'admin'):
            self.email.errors.append('brak dostepu')
            self.password.errors.append('brak dostepu')
            return False
        return True


class FlightForm(Form):
    flight_number = StringField('numer lotu', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    id_airport_from = IntegerField('id lotniska wylotu', [validators.DataRequired()])
    id_airport_to = StringField('id lotniska przylotu', [validators.DataRequired()])
    date_from = DateField('data wylotu', [validators.DataRequired()], format='%Y-%m-%d %H:%M:%S')
    date_to = DateField('data przylotu', [validators.DataRequired()], format='%Y-%m-%d %H:%M:%S')
    id_plane = IntegerField('id samolotu', [validators.DataRequired()])

    def validate(self):
        if not Form.validate(self):
            return False
        if self.id_airport_from == self.id_airport_to:
            self.id_airport_from.errors.append('id musza byc inne')
            self.id_airport_to.errors.append('id musza byc inne')
            return False
        if Airport.get(id_airport=self.id_airport_from.data) is None:
            self.id_airport_from.errors.append('niepoprawny id lotniska wylotu')
            return False
        if Airport.get(id_airport=self.id_airport_to.data) is None:
            self.id_airport_to.errors.append('niepoprawny id lotniska przylotu')
            return False
        if self.date_from.data >= self.date_to.data:
            self.date_from.errors.append('data wylotu >= data przylotu')
            self.date_to.errors.append('data wylotu >= data przylotu')
        if Plane.get(self.id_plane.data) is None:
            self.id_plane.errors.append('niepoprawny id samolotu')
            return False
        return True


class AirportForm(Form):
    name = StringField('nazwa', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])

    def validate(self):
        if not Form.validate(self):
            return False
        if Airport.get(name=self.name.data) is not None:
            self.name.errors.append('lotnisko o takiej nazwie juz istnieje')
            return False
        return True


class PlaneForm(Form):
    producer = StringField('producent', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])
    model = StringField('model', [
        validators.DataRequired(),
        validators.Length(max=30)
    ])

