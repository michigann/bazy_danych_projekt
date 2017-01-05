from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy

from app.db_helper import raw_query, get_dictionary_items, get_dictionary_item_id, get_db, get_db_engine
from app.forms import BookTicketForm, FlightForm
from app.models import Airport, Address, PersonalData, Flight


def select_flights(search_form):
    where_airports, where_date = '', ''
    args = dict()
    if search_form.airport_from.data != '':
        args['id_lotnisko_wylot'] = Airport.get(name=search_form.airport_from.data).id_airport
        where_airports += ' id_lotnisko_wylot=:id_lotnisko_wylot '
    if search_form.airport_to.data != '':
        args['id_lotnisko_przylot'] = Airport.get(name=search_form.airport_to.data).id_airport
        if where_airports != '':
            where_airports += ' AND '
        where_airports += ' id_lotnisko_przylot=:id_lotnisko_przylot '
    if search_form.departure_date.data != '':
        args['data_wylot'] = search_form.departure_date.data

    flight_date, search_date = "to_char(data_wylot, 'YYYY-MM-DD')", "to_char(:data_wylot, 'YYYY-MM-DD')"

    id_class = get_dictionary_item_id('klasa', 'economy')

    query = 'SELECT id_lot, nr_lot, lw.nazwa, lp.nazwa, data_wylot, data_przylot, (SELECT _cena FROM obecna_cena(id_lot, {})) FROM lot ' \
            'INNER JOIN lotnisko AS lw ON id_lotnisko_wylot=lw.id_lotnisko ' \
            'INNER JOIN lotnisko AS lp ON id_lotnisko_przylot=lp.id_lotnisko WHERE data_wylot>=CURRENT_TIMESTAMP AND ' \
            ''.format(id_class)
    order_by = ' ORDER BY data_wylot '

    where_date = " {}={} ".format(flight_date, search_date)
    current_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    where_date = " :data_wylot-data_wylot <= '7 day' AND {} < {} ".format(flight_date, search_date)
    prev_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    where_date = " :data_wylot-data_wylot <= '7 day' AND {} > {} ".format(flight_date, search_date)
    next_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    return current_flights, prev_flights, next_flights


def select_ticket_list(id_flight):
    out = list()
    for name_item, id_item in get_dictionary_items('klasa').iteritems():
        price = raw_query("SELECT _id_bilet_cennik, _cena FROM obecna_cena({}, {})".format(id_flight, id_item)).first()
        out.append((int(price[0]), 'klasa {} {} zl'.format(name_item, price[1])))
    return out


def select_flight_back_office():
    query = 'SELECT id_lot, nr_lot, lw.nazwa, lp.nazwa, data_wylot, data_przylot, id_samolot FROM lot ' \
            'INNER JOIN lotnisko AS lw ON id_lotnisko_wylot=lw.id_lotnisko ' \
            'INNER JOIN lotnisko AS lp ON id_lotnisko_przylot=lp.id_lotnisko ORDER BY data_wylot '
    return raw_query(query).fetchall()


def select_airport_back_office():
    query = ' SELECT id_lotnisko, nazwa, id_adres FROM lotnisko ORDER BY nazwa '
    return raw_query(query).fetchall()


def select_planes_back_office():
    query = ' SELECT id_samolot, producent, model FROM samolot ORDER BY producent, samolot '
    return raw_query(query).fetchall()


def buy_ticket(book_ticket_form):
    if not isinstance(book_ticket_form, BookTicketForm):
        return None

    address = Address()
    address.country = book_ticket_form.country.data
    address.city = book_ticket_form.city.data
    address.street = book_ticket_form.street.data
    address.street_number = book_ticket_form.street_number.data
    address.flat_number = book_ticket_form.flat_number.data
    address.postal_code = book_ticket_form.postal_code.data
    id_address = Address.new(address).id_address

    personal_data = PersonalData()
    personal_data.personal_number = book_ticket_form.personal_number.data
    personal_data.fname = book_ticket_form.fname.data
    personal_data.lname = book_ticket_form.lname.data
    personal_data.birth = book_ticket_form.birth.data
    personal_data.nationality = book_ticket_form.nationality.data
    personal_data.id_address = id_address
    id_personal_data = PersonalData.new(personal_data).id_personal_data
    print "ssssss", list(book_ticket_form.choose_ticket.data)

    id_ticket_price = int(book_ticket_form.choose_ticket.data[0])
    id_user = int(current_user.get_id())

    try:
        engine = get_db_engine()
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.callproc("kup_bilet", [id_personal_data, id_ticket_price, id_user])
        cursor.close()
        connection.commit()
    except Exception:
        return False
    return True


def save_flight(flight_form, id_flight=None):
    if not isinstance(flight_form, FlightForm):
        return None
    flight = Flight()
    flight.id_flight = id_flight
    flight.flight_number = flight_form.flight_number.data
    flight.id_airport_from = flight_form.id_airport_from.data
    flight.id_airport_to = flight_form.id_airport_to.data
    flight.date_from = flight_form.date_from.data
    flight.date_to = flight_form.date_from.data
    flight.id_plane = flight_form.id_plane.data
    return flight.save()
