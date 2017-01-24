# -*- coding: utf-8 -*-

"""
Formularze obsługi danych wprowadznych przez użytkowników (klientów i administratorów)
"""

from wtforms import Form, StringField, PasswordField, validators, DateField, IntegerField, SelectMultipleField, \
    BooleanField, DateTimeField
from wtforms.widgets import ListWidget, RadioInput
from src.db_helper import get_dictionary_item_id
from src.models import User, Airport, Plane


class RegistrationForm(Form):
    email = StringField('adres email', [
        validators.DataRequired(),
        validators.Length(min=6, max=256)
    ])
    password = PasswordField('hasło', [
        validators.DataRequired(),
        validators.Length(min=6, max=30),
        validators.EqualTo('confirm', message='hasła nie pasują do siebie')
    ])
    confirm = PasswordField('powtórz hasło')

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.get(email=self.email.data)
        if user is not None:
            self.email.errors.append('podany adres email jest już używany')
            return False

        return True


class LoginForm(Form):
    email = StringField('email', [validators.DataRequired()])
    password = PasswordField('hasło', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.get(email=self.email.data)
        if user is None:
            self.email.errors.append('podany email jest niepoprawny')
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append('podane hasło jest niepoprawne')
            return False

        self.user = user
        return True


class SearchForm(Form):
    airport_from = StringField('lotnisko wylotu')
    airport_to = StringField('lotnisko przylotu')
    departure_date = DateField('data wylotu', [validators.DataRequired()], format='%Y-%m-%d')

    def validate(self):
        if not Form.validate(self):
            return False
        if self.airport_from.data == '' and self.airport_to.data == '':
            self.airport_from.errors.append('podaj miejsce wylotu lub przylotu')
            self.airport_to.errors.append('podaj miejsce wylotu lub przylotu')
            return False
        if self.airport_from.data != '' and Airport.get(name=self.airport_from.data) is None:
            self.airport_from.errors.append('brak lotniska {}'.format(self.airport_from.data))
            return False
        if self.airport_to.data != '' and Airport.get(name=self.airport_to.data) is None:
            self.airport_to.errors.append('brak lotniska {}'.format(self.airport_to.data))
            return False
        return True


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


class MultiIntegerField(SelectMultipleField):
    widget = ListWidget()
    option_widget = IntegerField()


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
    date_from = DateTimeField('data wylotu', [validators.DataRequired()])
    date_to = DateTimeField('data przylotu', [validators.DataRequired()])
    id_plane = IntegerField('id samolotu', [validators.DataRequired()])

    def validate(self):
        if not Form.validate(self):
            return False
        flag = True
        if self.id_airport_from == self.id_airport_to:
            self.id_airport_from.errors.append('id musza byc inne')
            self.id_airport_to.errors.append('id musza byc inne')
            flag = False
        if Airport.get(id_airport=self.id_airport_from.data) is None:
            self.id_airport_from.errors.append('niepoprawny id lotniska wylotu')
            flag = False
        if Airport.get(id_airport=self.id_airport_to.data) is None:
            self.id_airport_to.errors.append('niepoprawny id lotniska przylotu')
            flag = False
        if self.date_from.data >= self.date_to.data:
            self.date_from.errors.append('data wylotu >= data przylotu')
            self.date_to.errors.append('data wylotu >= data przylotu')
            flag = False
        if Plane.get(self.id_plane.data) is None:
            self.id_plane.errors.append('niepoprawny id samolotu')
            flag = False
        return flag


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

    @classmethod
    def append_field(cls, name, field):
        setattr(cls, name, field)
        return cls


class PriceForm(Form):
    id_class = MultiRadioField('klasa', validators=[validators.DataRequired()], coerce=int)
    price = IntegerField('cena', [validators.DataRequired()])
    amount = IntegerField('ilosc', [validators.DataRequired()])
    date_from = DateField('data od', [validators.DataRequired()])
    date_to = DateField('data do', [validators.DataRequired()])
    available = BooleanField('dostepny', default=True)

    def validate(self):
        if not Form.validate(self):
            return False
        flag = True
        if self.date_from.data >= self.date_to.data:
            self.date_from.errors.append('data od >= data do')
            self.date_to.errors.append('data od >= data do')
            flag = False
        return flag
