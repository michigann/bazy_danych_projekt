from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy

from app.db_helper import raw_query, get_dictionary_items, get_dictionary_item_id, get_db, get_db_engine
from app.forms import BookTicketForm, FlightForm
from app.models import Airport, Address, PersonalData, Flight, Plane


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

    query = ' SELECT * FROM loty_klient WHERE '
    order_by = ' ORDER BY data_wylot '

    where_date = " {}={} ".format(flight_date, search_date)
    current_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    where_date = " :data_wylot-data_wylot <= '7 day' AND {} < {} ".format(flight_date, search_date)
    prev_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    where_date = " :data_wylot-data_wylot <= '7 day' AND {} > {} ".format(flight_date, search_date)
    next_flights = raw_query(query + ' {} AND {} {}'.format(where_airports, where_date, order_by), args)

    return current_flights, prev_flights, next_flights


def select_cheapest_flights(limit=10):
    return raw_query(' SELECT * FROM loty_klient ORDER BY cena LIMIT {} '.format(limit))


def select_ticket_list(id_flight):
    out = list()
    for name_item, id_item in get_dictionary_items('klasa').iteritems():
        try:
            price = raw_query("SELECT _id_bilet_cennik, _cena FROM obecna_cena({}, {})".format(id_flight, id_item)).first()
            out.append((int(price[0]), 'klasa {} {} zl'.format(name_item, price[1])))
        except TypeError:
            pass
    return out


def select_user_tickets(id_user):
    args = {
        'id_uzytkownik': id_user
    }
    query = ' SELECT * FROM kupione_bilety WHERE id_uzytkownik=:id_uzytkownik ' \
            ' AND data_wylot {} CURRENT_TIMESTAMP ORDER BY data_wylot '
    future_flights = raw_query(query.format('>'), args).fetchall()
    past_flights = raw_query(query.format('<='), args).fetchall()
    return future_flights, past_flights


def select_flight_back_office():
    query = ' SELECT id_lot, nr_lot, lotnisko_wylot, lotnisko_przylot, data_wylot, data_przylot, id_samolot, ' \
            ' miejsca_wolne, miejsca_wszystkie FROM loty_backoffice '
    return raw_query(query).fetchall()


def select_airport_back_office():
    query = ' SELECT id_lotnisko, nazwa, id_adres FROM lotnisko ORDER BY nazwa '
    return raw_query(query).fetchall()


def select_planes_back_office():
    query = ' SELECT id_samolot FROM samolot ORDER BY producent, samolot '
    select = raw_query(query).fetchall()
    planes = list()
    for row in select:
        planes.append(Plane.get(row[0]))
    return planes


def select_price_list(flight_id, class_id):
    query = ' SELECT id_bilet_cennik, id_lot, id_klasa, cena, ilosc, kupione, data_od, data_do, dostepny FROM bilet_cennik ' \
            ' WHERE id_lot=:id_lot AND id_klasa=:id_klasa ORDER BY data_od, data_do '
    args = {
        'id_lot': flight_id,
        'id_klasa': class_id
    }
    return raw_query(query, args)


def generate_report(report):
    if report != 'day' and report != 'week' and report != 'month' and report != 'year':
        return None
    query = " SELECT to_char(date_trunc('{}', data_zakupu)), 'YYYY-MM-DD', COUNT(*) AS ilosc, SUM(bc.cena) AS dochod, AVG(bc.cena) AS srednia_cena " \
            " FROM bilet_cennik AS bc INNER JOIN bilet_osoba AS bo ON bo.id_bilet_cennik=bc.id_bilet_cennik " \
            " GROUP BY CUBE (date_trunc('{}', data_zakupu)) ORDER BY date_trunc('{}', data_zakupu) ".format(report)
    return raw_query(query)


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

