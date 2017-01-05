from flask_login import UserMixin
from sqlalchemy import text

from db_helper import get_dictionary_items, get_db, get_dictionary_item_id, raw_query, get_db_engine


class User(UserMixin):

    def __init__(self, id_user, email, id_rank, id_personal_data=None):
        self.id_user = id_user
        self.email = email
        self.id_rank = id_rank
        self.id_personal_data = id_personal_data
        self.is_customer = False
        self.is_admin = False
        self.is_employee = False

    @staticmethod
    def get(id_user=None, email=None):
        if id_user is None and email is None:
            return None

        query = 'SELECT id_uzytkownik, email, id_ranga, id_dane_osobowe FROM uzytkownik WHERE '
        query += ' id_uzytkownik=:id_user ' if id_user is not None else ' email=:email '
        args = {
            'id_user': id_user,
            'email': email
        }
        user_data = get_db_engine().execute(text(query), **args).fetchone()
        if user_data is None:
            return None

        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        __user_types = get_dictionary_items('user')
        user.is_customer = user.id_rank == __user_types['klient']
        user.is_admin = user.id_rank == __user_types['admin']
        user.is_employee = user.id_rank == __user_types['pracownik']
        return user

    @staticmethod
    def new(email, password):
        if email is None or password is None:
            return None

        query = ' INSERT INTO uzytkownik (email, haslo, id_ranga, id_dane_osobowe) ' \
                ' VALUES (:email, :password, :id_rank, :id_personal_data) '
        args = {
            'email': email,
            'password': password,
            'id_rank': get_dictionary_item_id('user', 'klient'),
            'id_personal_data': None
        }
        get_db_engine().execute(text(query), **args)
        return User.get(email=email)

    def get_id(self):
        return str(self.id_user)

    def check_password(self, password):
        query = 'SELECT haslo FROM uzytkownik WHERE id_uzytkownik=:id_user'
        args = {
            'id_user': self.get_id()
        }
        correct_password = str(get_db_engine().execute(text(query), **args).first()[0])
        return correct_password == password


class PersonalData(object):

    def __init__(self):
        self.id_personal_data = None
        self.personal_number = None
        self.fname= None
        self.lname = None
        self.birth = None
        self.nationality = None
        self.id_address = None

    @staticmethod
    def get(id_personal_data):
        query = ' SELECT id_dane_osobowe, nr_osoba, imie, nazwisko, data_urodzenia, narodowosc, id_adres ' \
                ' FROM dane_osobowe WHERE id_dane_osobowe=:id_dane_osobowe '
        args = {
            'id_dane_osobowe': id_personal_data
        }
        data = get_db_engine().execute(text(query), **args).first()
        if data is None:
            return None

        p_data = PersonalData()
        p_data.id_personal_data = data[0]
        p_data.personal_number = data[1]
        p_data.fname = data[2]
        p_data.lname = data[3]
        p_data.birth = data[4]
        p_data.nationality = data[5]
        p_data.id_address = data[6]
        return p_data

    @staticmethod
    def new(personal_data):
        if personal_data is None or not isinstance(personal_data, PersonalData):
            return None
        query = ' INSERT INTO dane_osobowe (nr_osoba, imie, nazwisko, data_urodzenia, narodowosc, id_adres) ' \
                ' VALUES (:personal_number, :fname, :lname, :birth, :nationality, :id_address) ' \
                ' RETURNING id_dane_osobowe'
        args = personal_data.__dict__
        id_personal_data = get_db_engine().execute(text(query), **args).fetchone()[0]
        return PersonalData.get(id_personal_data)


class Address(object):

    def __init__(self):
        self.id_address = None
        self.country = None
        self.city = None
        self.street = None
        self.street_number = None
        self.flat_number = None
        self.postal_code = None

    @staticmethod
    def get(id_address):
        query = ' SELECT id_adres, kraj, miasto, ulica, nr, nr_mieszkania, kod_pocztowy ' \
                ' FROM adres WHERE id_adres=:id_adres '
        args = {
            'id_adres': id_address
        }
        data = get_db_engine().execute(text(query), **args).first()
        if data is None:
            return None

        a_data = Address()
        a_data.id_address = data[0]
        a_data.country = data[1]
        a_data.city = data[2]
        a_data.street = data[3]
        a_data.street_number = data[4]
        a_data.flat_number = data[5]
        a_data.postal_code = data[6]
        return a_data

    @staticmethod
    def new(address):
        if address is None or not isinstance(address, Address):
            return None
        query = ' INSERT INTO adres (kraj, miasto, ulica, nr, nr_mieszkania, kod_pocztowy) ' \
                ' VALUES (:country, :city, :street, :street_number, :flat_number, :postal_code) ' \
                ' RETURNING id_adres '
        args = address.__dict__
        id_address = get_db_engine().execute(text(query), **args).fetchone()[0]
        return Address.get(id_address)


class Flight(object):

    def __init__(self):
        self.id_flight = None
        self.flight_number = None
        self.id_airport_from = None
        self.id_airport_to = None
        self.date_from = None
        self.date_to = None
        self.id_plane = None

    @staticmethod
    def get(id_flight=None):
        query = ' SELECT id_lot, nr_lot, id_lotnisko_wylot, id_lotnisko_przylot, data_wylot, data_przylot, id_samolot' \
                ' FROM lot WHERE id_lot=:id_lot '
        args = {
            'id_lot': id_flight
        }
        data = get_db_engine().execute(text(query), **args).first()
        if data is None:
            return None
        f_data = Flight()
        f_data.id_flight = data[0]
        f_data.flight_number = data[1]
        f_data.id_airport_from = data[2]
        f_data.id_airport_to = data[3]
        f_data.date_from = data[4]
        f_data.date_to = data[5]
        f_data.id_plane = data[6]
        return f_data

    def save(self):
        if self.id_flight is None:
            query = ' INSERT INTO lot (nr_lot, id_lotnisko_wylot, id_lotnisko_przylot, data_wylot, data_przylot, id_samolot) ' \
                    ' VALUES (:flight_number, :id_airport_from, :id_airport_to, :date_from, :date_to, :id_plane) ' \
                    ' RETURNING id_lot '
        else:
            query = ' UPDATE lot SET nr_lot=:flight_number, id_lotnisko_wylot=:id_airport_from, ' \
                    ' id_lotnisko_przylot=:id_airport_to, data_wylot=:date_from, data_przylot=:date_to, id_samolot=:id_plane' \
                    ' WHERE id_lot=:id_flight RETURNING id_lot '
        args = self.__dict__
        print args
        id_flight = get_db_engine().execute(text(query), **args).fetchone()[0]
        return Flight.get(id_flight)


class Airport(object):

    def __init__(self):
        self.id_airport = None
        self.name = None
        self.id_address = None

    @staticmethod
    def get(id_airport=None, name=None):
        if id_airport is None and name is None:
            return None

        query = ' SELECT id_lotnisko, nazwa, id_adres FROM lotnisko WHERE '
        query += ' id_lotnisko=:id_lotnisko ' if id_airport is not None else ' nazwa=:nazwa '
        args = {
            'id_lotnisko': id_airport,
            'nazwa': name
        }

        data = get_db_engine().execute(text(query), **args).first()
        if data is None:
            return None
        a_data = Airport()
        a_data.id_airport = data[0]
        a_data.name = data[1]
        a_data.id_address = data[2]
        return a_data

    def save(self):
        if self.id_airport is None:
            query = ' INSERT INTO lotnisko (nazwa, id_adres) VALUES (:name, :id_address) ' \
                    ' RETURNING id_lotnisko '
        else:
            query = ' UPDATE lotnisko SET nazwa=:name, id_adres=:id_address WHERE id_lotnisko=:id_airport ' \
                    ' RETURNING id_lotnisko '
        args = self.__dict__
        id_airport = get_db_engine().execute(text(query), **args).fetchone()[0]
        return Airport.get(id_airport)


class Plane(object):
    def __init__(self):
        self.id_plane = None
        self.producer = None
        self.model = None
        self.seats = list()

    @staticmethod
    def get(id_plane=None):
        query = ' SELECT producent, model, s.id_slownik, element, ilosc FROM samolot ' \
                ' INNER JOIN samolot_miejsca AS sm ON sm.id_samolot=samolot.id_samolot ' \
                ' INNER JOIN slownik AS s ON s.id_slownik=sm.id_slownik '
        if id_plane is not None:
            query += ' WHERE samolot.id_samolot=:id_samolot '
        args = {
            'id_samolot': id_plane
        }
        data = get_db_engine().execute(text(query), **args).fetchall()
        if data is None:
            return None

        p_data = Plane()
        p_data.id_plane = id_plane
        for row in data:
            p_data.producer = row[0]
            p_data.model = row[1]
            p_data.seats.append({
                'id_slownik': row[2],
                'element': row[3],
                'ilosc': row[4]
            })
        return p_data

    def save(self):
        if self.id_plane is None:
            query = ' INSERT INTO samolot (producent, model) VALUES (:producer, :model) ' \
                    ' RETURNING id_samolot '
        else:
            query = ' UPDATE samolot SET producent=:producer, model=:model WHERE id_samolot=:id_plane ' \
                    ' RETURNING id_samolot '
        args = self.__dict__
        id_airport = get_db_engine().execute(text(query), **args).fetchone()[0]
        return Airport.get(id_airport)


class Price(object):
    pass


class PersonTicket(object):
    pass

