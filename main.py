# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask import abort
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask_login import current_user
from flask_login import LoginManager, login_required, logout_user, login_user
from wtforms import IntegerField
from wtforms import validators

from src.db_helper import get_dictionary_items
from src.db_logic import select_flights, select_ticket_list, buy_ticket, select_flight_back_office, \
    select_airport_back_office, select_planes_back_office, select_cheapest_flights, select_price_list, \
    select_user_tickets, generate_report, select_airports
from src.forms import RegistrationForm, LoginForm, SearchForm, BookTicketForm, FlightForm, BackOfficeLoginForm, \
    AirportForm, PlaneForm, PriceForm
from src.models import User, Flight, Airport, Plane, Price

my_app = Flask(__name__)


@my_app.route('/')
@my_app.route('/home/')
def home():
    """Strona główna - widok

    Przygotowanie widoków dla strony głównej, wyświetlenie najtańszych lotów

    Returns:
        wygenerowany szablon html
    """
    args = {
        'flights': select_cheapest_flights()
    }
    return render_template('customer_views/home.html', **args)


@my_app.route('/register/', methods=['GET', 'POST'])
def register():
    """Rejestracja - widok

    Przygotowanie formularza rejestracyjnego, walidacja i dodawanie nowego użytkownika

    Returns:
        wygenerowany szablon html do rejestracji / przekierowanie do formularza logowania jeśli rejestracja
        przeszła pomyślnie
    """
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        User.new(form.email.data, form.password.data)
        return redirect(url_for('login'))
    return render_template('customer_views/register.html', form=form)


@my_app.route('/login/', methods=['GET', 'POST'])
def login():
    """Logowanie - widok

    Formularz logowania, jeśli dane logowania są poprawne logowanie użytkonika przy pomocy sesji

    Returns:
        wygenerowany szaplon logowania / przekierowanie do strony głównej lub strony z dostępem jedynie dla
        zalogowanych użytkowników
    """
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_user(form.user)
        return redirect(request.args.get('next') or url_for('home'))
    return render_template('customer_views/login.html', form=form)


@my_app.route("/logout/")
@login_required
def logout():
    """Wylogowanie - widok

    Wylogowywanie obecnie zalogowanego użytkownika

    Returns:
        przekierowanie do strony głównej
    """
    logout_user()
    return redirect(url_for('home'))


@my_app.route('/search_flight/', methods=['GET', 'POST'])
def search_flight():
    """Wyszukiwanie lotów - widok

    Przygotowanie formularza do wyszukania lotu

    Returns:
        szablon z formularzem / i lista wyszukanych lotów pasujących do kryterium +-7 dni
    """
    form = SearchForm(request.form)
    args = {
        'current_user': current_user,
        'form': form,
        'flights': None,
        'prev_flights': None,
        'next_flights': None
    }
    if request.method == 'POST' and form.validate():
        args['flights'], args['prev_flights'], args['next_flights'] = select_flights(form)
    return render_template('customer_views/search.html', **args)


@my_app.route('/book_ticket/<int:id_flight>/', methods=['GET', 'POST'])
@login_required
def book_ticket(id_flight):
    """Kupowanie biletu - widok

    Przygotowanie formularza kupowania biletu na konkretny lot dla osoby, jeśli formularz jest poprawny oraz
    miejsca na lot nadal są dostępne następuje kupienie biletu przez zalogowanego użytkownika

    Args:
        id_flight: numer identyfikacyjny lotu, na który kupowany jest bilet
    Returns:
        wygenerowany formularz danych osobowych potrzebnych do zakupu biletu / przekierowanie po zakupie
    """
    form = BookTicketForm(request.form)
    form.choose_ticket.choices = select_ticket_list(id_flight)
    if request.method == 'POST' and form.validate():
        info_id = 2 if buy_ticket(form) else 1
        return redirect(url_for('info', info_id=info_id))
    return render_template('customer_views/book_ticket.html', form=form)


@my_app.route('/my_tickets/<int:id_price>', methods=['GET', 'POST'])
@my_app.route('/my_tickets/', methods=['GET', 'POST'])
@login_required
def my_tickets(id_price=None):
    """Kupione bilety - widok

    Wyświetla listę lotów, na które kupiliśmy bilety

    Args:
        id_price: jeśli None wyświetla listę, jeśli wybrany bilet (id) dodatkowo szczegóły
    Returns:
        wygenerowany szablon z listą lotów
    """
    future_tickets, past_tickets = select_user_tickets(int(session['user_id']))
    return render_template('customer_views/my_tickets.html', future_tickets=future_tickets, past_tickets=past_tickets)


@my_app.route('/info/<int:info_id>/')
def info(info_id):
    """Kody informacji - widok

    Widok informacyjny zawierający kody informacji, błędów

    Args:
        info_id: kod informacji
    Returns:
        szablon z komunikatem
    """
    if info_id == 1:
        msg = 'Przepraszamy! Wystąpił problem z zakupem biletu... Spróbuj ponownie później.'
    elif info_id == 2:
        msg = 'Dziękujemy za zakup biletu!'
    else:
        msg = 'Przepraszamy! Wystąpił nieznany nam problem...'
    return render_template('customer_views/info.html', msg=msg)


@my_app.route('/search_airport/<search_string>/', methods=['GET', 'POST'])
def search_airport(search_string):
    """
    Wyświetlenie listy pasujących nazw lotnisk do wprowadzonego ciągu znaków
    :param search_string: ciąg znaków dla szukanego lotniska
    :return: wygenerowana lista hmtml dla podanego ciągu
    """
    selected_airports = select_airports(search_string)
    return render_template('customer_views/search_airport.html', airports=selected_airports)


@my_app.route('/back_office/')
@my_app.route('/back_office/home/')
@login_required
def back_office_home():
    """
    Strona główa dla panelu administratora, możliwe wyświetlenie dla użytkowników o randze admin
    :return: wygenerowany szablon strony głównej panelu admina / jeżeli brak uprawnień 403
    """
    if current_user.is_admin:
        return render_template('back_office_views/base.html')
    return abort(403)


@my_app.route('/back_office/login/', methods=['GET', 'POST'])
def back_office_login():
    """
    Panel logowania dla administratorów
    :return: generowanie formularza logowania lub przekierowanie jeśli dane są poprawne do strony głównej panelu
    """
    form = BackOfficeLoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_user(form.user)
        return redirect(url_for('back_office_home'))
    return render_template('back_office_views/login.html', form=form)


@my_app.route('/back_office/airports/', methods=['GET', 'POST'])
@my_app.route('/back_office/airports/<int:id_airport>/', methods=['GET', 'POST'])
@login_required
def airports(id_airport=None):
    """
    Widok do wyświetlania listy lotnisk w panelu administracyjnym, pozwalający również na edycję nazwy lotniska
    :param id_airport: opcjonalny argument (jeśli not None to tryb edycji lotniska)
    :return: wygenerowany szablon listy lotnisk + formularz dodawania / formularz edycji
    """
    if not current_user.is_admin:
        return abort(403)
    all_airports = select_airport_back_office()
    form = AirportForm(request.form)
    if request.method == 'POST' and form.validate():
        airport = Airport.new_airport(form)
        airport.id_airport = id_airport
        # airport.id_address = form.id_airport_from.data
        saved_airport = airport.save()
        if saved_airport is not None:
            return redirect(url_for('airports'))
    airport = None if id_airport is None else Airport.get(id_airport)
    if airport is not None:
        form.name.data = airport.name
        # form.id_address.data = airport.id_address
    return render_template('back_office_views/airports.html', form=form, airports=all_airports, id_airport=id_airport)


@my_app.route('/back_office/planes/', methods=['GET', 'POST'])
@login_required
def planes():
    if not current_user.is_admin:
        return abort(403)
    all_planes = select_planes_back_office()
    for name_item, id_item in get_dictionary_items('klasa').iteritems():
        PlaneForm.append_field(name_item, IntegerField(name_item, validators=[validators.DataRequired()]))
    form = PlaneForm(request.form)
    if request.method == 'POST' and form.validate():
        plane = Plane.new_plane(form)
        for name_item, id_item in get_dictionary_items('klasa').iteritems():
            plane.seats.append({
                'ilosc': getattr(form, name_item).data,
                'element': name_item,
                'id_slownik': id_item
            })
        saved_plane = plane.save()
        if saved_plane is not None:
            return redirect(url_for('planes'))

    return render_template('back_office_views/planes.html', form=form, planes=all_planes)


@my_app.route('/back_office/flights/', methods=['GET', 'POST'])
@my_app.route('/back_office/flights/<int:id_flight>/', methods=['GET', 'POST'])
@login_required
def flights(id_flight=None):
    if not current_user.is_admin:
        return abort(403)
    all_flights = select_flight_back_office()
    form = FlightForm(request.form)
    if request.method == 'POST' and form.validate():
        flight = Flight.new_flight(form)
        flight.id_flight = id_flight
        saved_flight = flight.save()
        if saved_flight is not None:
            return redirect(url_for('price_list', id_flight=saved_flight.id_flight))

    flight = None if id_flight is None else Flight.get(id_flight)
    if flight is not None:
        form.flight_number.data = flight.flight_number
        form.id_airport_from.data = flight.id_airport_from
        form.id_airport_to.data = flight.id_airport_to
        form.date_from.data = flight.date_from
        form.date_to.data = flight.date_to
        form.id_plane.data = flight.id_plane

    return render_template('back_office_views/flights.html', form=form, flights=all_flights, id_flight=id_flight)


@my_app.route('/back_office/price_list/flights/<int:id_flight>/', methods=['GET', 'POST'])
@my_app.route('/back_office/price_list/', methods=['GET', 'POST'])
@login_required
def price_list(id_flight=None):
    if not current_user.is_admin:
        return abort(403)

    form = PriceForm(request.form)
    form.id_class.choices = list()
    for name_item, id_item in get_dictionary_items('klasa').iteritems():
        form.id_class.choices.append((id_item, name_item))

    if request.method == 'POST' and form.validate():
        price = Price.new_price(form)
        price.id_flight = id_flight
        saved_price = price.save()
        if saved_price is not None:
            return redirect(url_for('price_list', id_flight=id_flight))

    flight = Flight.get(id_flight)

    # form.id_class.data = [4]
    all_flights = None
    all_prices = list()
    if flight is None:
        all_flights = select_flight_back_office()
    else:
        for class_name, class_id in get_dictionary_items('klasa').iteritems():
            all_prices.append((class_name, select_price_list(id_flight, class_id)))
    args = {
        'form': form,
        'flight': flight,
        'all_prices': all_prices,
        'all_flights': all_flights
    }
    return render_template('back_office_views/price_list.html', **args)


@my_app.route('/back_office/price_list/set_available/<int:id_flight>/<int:id_price>/', methods=['GET', 'POST'])
@login_required
def set_price_available(id_flight, id_price):
    if not current_user.is_admin:
        return abort(403)
    price = Price.get(id_price)
    price.available = 1 if price.available == 0 else 0
    price.save()
    return redirect(url_for('price_list', id_flight=id_flight))


@my_app.route('/back_office/reports/<string:report>/', methods=['GET', 'POST'])
@my_app.route('/back_office/reports/', methods=['GET', 'POST'])
@login_required
def reports(report=None):
    if not current_user.is_admin:
        return abort(403)
    report_list = generate_report(report)
    return render_template('back_office_views/reports.html', report_list=report_list)


if __name__ == '__main__' or __name__ == 'main':
    my_app.secret_key = 'super secret key'
    my_app.config['SESSION_TYPE'] = 'filesystem'
    if __name__ == '__main__':
        my_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
    else:
        my_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://u4kuklewski:4kuklewski@localhost/u4kuklewski'
    my_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    login_manager = LoginManager()
    login_manager.init_app(my_app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    my_app.run()

