from flask import Flask, render_template
from flask import abort
from flask import redirect
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import LoginManager, login_required, logout_user, login_user

from app.db_helper import raw_query
from app.db_logic import select_flights, select_ticket_list, buy_ticket, select_flight_back_office, save_flight, \
    select_airport_back_office, select_planes_back_office
from app.forms import RegistrationForm, LoginForm, SearchForm, BookTicketForm, FlightForm, BackOfficeLoginForm, \
    AirportForm, PlaneForm
from app.models import User, Flight, Airport, Plane

app = Flask(__name__)


@app.route('/')
@app.route('/home/')
def home():
    return render_template('customer_views/home.html')


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
        return redirect(url_for('home'))
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
        return render_template('back_office_views/base.html', current_user)
    return abort(403)


@app.route('/back_office/login/', methods=['GET', 'POST'])
def back_office_login():
    form = BackOfficeLoginForm(request.form)
    if request.method == 'POST' and form.validate():
        login_user(form.user)
        return redirect(url_for('back_office_home'))
    return render_template('back_office_views/login.html', form=form)


@app.route('/back_office/flights/', methods=['GET', 'POST'])
@app.route('/back_office/flights/<int:id_flight>/', methods=['GET', 'POST'])
@login_required
def flights(id_flight=None):
    if current_user.is_admin:
        all_flights = select_flight_back_office()
        form = FlightForm(request.form)

        if request.method == 'POST' and form.validate():
            flight = Flight()
            flight.id_flight = id_flight
            flight.flight_number = form.flight_number.data
            flight.id_airport_from = form.id_airport_from.data
            flight.id_airport_to = form.id_airport_to.data
            flight.date_from = form.date_from.data
            flight.date_to = form.date_from.data
            flight.id_plane = form.id_plane.data
            saved_flight = flight.save()
            if saved_flight is not None:
                return redirect(url_for('flights'))

        flight = None if id_flight is None else Flight.get(id_flight)
        if flight is not None:
            form.flight_number.data = flight.flight_number
            form.id_airport_from.data = flight.id_airport_from
            form.id_airport_to.data = flight.id_airport_to
            form.date_from.data = flight.date_from
            form.date_to.data = flight.date_to
            form.id_plane.data = flight.id_plane

        return render_template('back_office_views/flights.html', form=form, flights=all_flights, id_flight=id_flight)
    return abort(403)


@app.route('/back_office/airports/', methods=['GET', 'POST'])
@app.route('/back_office/airports/<int:id_airport>/', methods=['GET', 'POST'])
@login_required
def airports(id_airport=None):
    if current_user.is_admin:
        all_airports = select_airport_back_office()
        form = AirportForm(request.form)
        if request.method == 'POST' and form.validate():
            airport = Airport()
            airport.id_airport = id_airport
            airport.name = form.name.data
            # airport.id_address = form.id_airport_from.data
            saved_airport = airport.save()
            if saved_airport is not None:
                return redirect(url_for('airports'))

        airport = None if id_airport is None else Airport.get(id_airport)
        if airport is not None:
            form.name.data = airport.name
            # form.id_address.data = airport.id_address

        return render_template('back_office_views/airports.html', form=form, airports=all_airports, id_airport=id_airport)
    return abort(403)


@app.route('/back_office/planes/', methods=['GET', 'POST'])
@app.route('/back_office/planes/<int:id_plane>/', methods=['GET', 'POST'])
@login_required
def planes(id_plane=None):
    if current_user.is_admin:
        all_planes = select_planes_back_office()
        form = PlaneForm(request.form)
        if request.method == 'POST' and form.validate():
            plane = Plane()
            plane.id_plane = id_plane
            plane.producer = form.producer.data
            plane.model = form.model.data
            saved_plane = plane.save()
            if saved_plane is not None:
                return redirect(url_for('planes'))

        plane = None if id_plane is None else Plane.get(id_plane)
        if plane is not None:
            form.producer.data = plane.producer
            form.model.data = plane.model

        return render_template('back_office_views/planes.html', form=form, planes=all_planes, id_plane=id_plane)
    return abort(403)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/postgres'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://u4kuklewski:4kuklewski@localhost/u4kuklewski'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    app.run()

