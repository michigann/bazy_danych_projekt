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

from app.db_helper import raw_query, get_dictionary_items
from app.db_logic import select_flights, select_ticket_list, buy_ticket, select_flight_back_office, \
    select_airport_back_office, select_planes_back_office, select_cheapest_flights, select_price_list, \
    select_user_tickets, generate_report
from app.forms import RegistrationForm, LoginForm, SearchForm, BookTicketForm, FlightForm, BackOfficeLoginForm, \
    AirportForm, PlaneForm, PriceForm
from app.models import User, Flight, Airport, Plane, Price

app = Flask(__name__)


@app.route('/')
@app.route('/home/')
def home():
    args = {
        'flights': select_cheapest_flights()
    }
    return render_template('customer_views/home.html', **args)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        User.new(form.email.data, form.password.data)
        return redirect(url_for('login'))
    return render_template('customer_views/register.html', form=form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_user(form.user)
        return redirect(request.args.get('next') or url_for('home'))
    return render_template('customer_views/login.html', form=form)


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/search_flight/', methods=['GET', 'POST'])
def search_flight():
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


@app.route('/book_ticket/<int:id_flight>/', methods=['GET', 'POST'])
@login_required
def book_ticket(id_flight):
    form = BookTicketForm(request.form)
    form.choose_ticket.choices = select_ticket_list(id_flight)
    if request.method == 'POST' and form.validate():
        info_id = 2 if buy_ticket(form) else 1
        return redirect(url_for('info', info_id=info_id))
    return render_template('customer_views/book_ticket.html', form=form)


@app.route('/my_tickets/<int:id_personal_data>/<int:id_price>', methods=['GET', 'POST'])
@app.route('/my_tickets/', methods=['GET', 'POST'])
@login_required
def my_tickets(id_personal_data=None, id_price=None):
    future_tickets, past_tickets = select_user_tickets(int(session['user_id']))
    return render_template('customer_views/my_tickets.html', future_tickets=future_tickets, past_tickets=past_tickets)


@app.route('/info/<int:info_id>/')
def info(info_id):
    if info_id == 1:
        msg = 'Przepraszamy! Wystapil problem z zakupem biletu... Sprobuj ponownie pozniej.'
    elif info_id == 2:
        msg = 'Dziekujemy za zakup biletu!'
    else:
        msg = 'Przepraszamy! Wystapil nieznany nam problem...'
    return render_template('customer_views/info.html', msg=msg)


@app.route('/search_airport/<search_string>/', methods=['GET', 'POST'])
def search_airport(search_string):
    args = {'search_string': '%{}%'.format(search_string)}
    query = 'SELECT id_lotnisko, nazwa FROM lotnisko WHERE nazwa LIKE :search_string '
    airports = raw_query(query, args)
    return render_template('customer_views/search_airport.html', airports=airports)


@app.route('/back_office/')
@app.route('/back_office/home/')
@login_required
def back_office_home():
    if current_user.is_admin:
        return render_template('back_office_views/base.html')
    return abort(403)


@app.route('/back_office/login/', methods=['GET', 'POST'])
def back_office_login():
    form = BackOfficeLoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_user(form.user)
        return redirect(url_for('back_office_home'))
    return render_template('back_office_views/login.html', form=form)


@app.route('/back_office/airports/', methods=['GET', 'POST'])
@app.route('/back_office/airports/<int:id_airport>/', methods=['GET', 'POST'])
@login_required
def airports(id_airport=None):
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


@app.route('/back_office/planes/', methods=['GET', 'POST'])
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


@app.route('/back_office/flights/', methods=['GET', 'POST'])
@app.route('/back_office/flights/<int:id_flight>/', methods=['GET', 'POST'])
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


@app.route('/back_office/price_list/flights/<int:id_flight>/', methods=['GET', 'POST'])
@app.route('/back_office/price_list/', methods=['GET', 'POST'])
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


@app.route('/back_office/price_list/set_available/<int:id_flight>/<int:id_price>/', methods=['GET', 'POST'])
@login_required
def set_price_available(id_flight, id_price):
    if not current_user.is_admin:
        return abort(403)
    price = Price.get(id_price)
    price.available = 1 if price.available == 0 else 0
    price.save()
    return redirect(url_for('price_list', id_flight=id_flight))


@app.route('/back_office/reports/<string:report>/', methods=['GET', 'POST'])
@app.route('/back_office/reports/', methods=['GET', 'POST'])
@login_required
def reports(report=None):
    if not current_user.is_admin:
        return abort(403)
    report_list = generate_report(report)
    return render_template('back_office_views/reports.html', report_list=report_list)


if __name__ == '__main__' or __name__ == 'main':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    if __name__ == '__main__':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://u4kuklewski:4kuklewski@localhost/u4kuklewski'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.run()

