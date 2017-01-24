# -*- coding: utf-8 -*-

"""
Moduł obsługujący i składający zapytania do bazy danych
"""

from flask_login import current_user
from src.db_helper import raw_query, get_dictionary_items, get_db_engine
from src.forms import BookTicketForm
from src.models import Airport, Address, PersonalData, Plane


def select_airports(search_string):
    """
    Wyszukiwanie lotnisk, których nazwa pasuje do danego wzorce

    Args:
        search_string: wzorzec wyszukiwania
    Returns:
        znalezione rekordy
    """
    args = {'search_string': '%{}%'.format(search_string)}
    query = 'SELECT id_lotnisko, nazwa FROM lotnisko WHERE nazwa LIKE :search_string '
    return raw_query(query, args)


def select_flights(search_form):
    """
    Obsługa formularza wyszukiwania lotów - składanie zapytania na podstawie wprowadzonych danych przez użytkownika
    Wymagane dane: lotnisko wylotu lub przylotu, data w każdym przypadku

    Args:
        search_form: formularz wyszukiwania lotów instancja SearchForm
    Returns:
        znalezione rekordy
    """
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
    """
    Wyszukiwarka najtańszych lotów

    Args:
        limit: ilość wyszukiwanych lotów
    Returns:
        znalezione rekordy
    """
    return raw_query(' SELECT * FROM loty_klient ORDER BY cena LIMIT {} '.format(limit))


def select_ticket_list(id_flight):
    """
    Wyszukiwanie listy biletów dla wszystkich klas zdefiniowanych dla lotu

    Args:
        id_flight: numer identyfikacyjny lotu
    Returns:
        znalezione rekordy / pusta lista
    """
    out = list()
    for name_item, id_item in get_dictionary_items('klasa').iteritems():
        try:
            price = raw_query("SELECT _id_bilet_cennik, _cena FROM obecna_cena({}, {})".format(id_flight, id_item)).first()
            out.append((int(price[0]), 'klasa {} {} zl'.format(name_item, price[1])))
        except TypeError:
            pass
    return out


def select_user_tickets(id_user):
    """
    Wyszukiwanie listy biletów kupionych przez użytkownika, lista przyszłych lotów oraz już odbytych

    Args:
        id_user: numer identyfikacyjny użytkownika dla ktróergo są wyszukiwane bilety
    Returns:
        znalezione rekordy w postaci krotki dwóch list (przyszłe loty, przeszłe loty)
    """
    args = {
        'id_uzytkownik': id_user
    }
    query = ' SELECT * FROM kupione_bilety WHERE id_uzytkownik=:id_uzytkownik ' \
            ' AND data_wylot {} CURRENT_TIMESTAMP ORDER BY data_wylot DESC '
    future_flights = raw_query(query.format('>'), args).fetchall()
    past_flights = raw_query(query.format('<='), args).fetchall()
    return future_flights, past_flights


def select_flight_back_office():
    """
    Wyszukiwanie listy lotów dla administratora - szczegółowa lista

    Returns:
        wszystkie loty ze szczegółowymi informacjami
    """
    query = ' SELECT id_lot, nr_lot, lotnisko_wylot, lotnisko_przylot, data_wylot, data_przylot, id_samolot, ' \
            ' miejsca_wolne, miejsca_wszystkie FROM loty_backoffice '
    return raw_query(query).fetchall()


def select_airport_back_office():
    """
    Wyszukiwanie listy lotnisk dla administratora - szczegółowa lista

    Returns:
        wszystkie lotniska ze szczegółowymi informacjami
    """
    query = ' SELECT id_lotnisko, nazwa, id_adres FROM lotnisko ORDER BY nazwa '
    return raw_query(query).fetchall()


def select_planes_back_office():
    """
    Wyszukiwanie listy samolotów dla administratora - szczegółowa lista

    Returns:
        wszystkie samoloty ze szczegółowymi informacjami
    """
    query = ' SELECT id_samolot FROM samolot ORDER BY producent, samolot '
    select = raw_query(query).fetchall()
    planes = list()
    for row in select:
        planes.append(Plane.get(row[0]))
    return planes


def select_price_list(flight_id, class_id):
    """
    Wyszukiwanie cenników dla administratora dla zdefiniowanego lotu i klasy (id_slownik)

    Args:
        flight_id: id lotu (dla którego szukamy cen)
        class_id: id klasy (dla której szukamy cen)
    Returns:
        zbiór
    """
    query = ' SELECT id_bilet_cennik, id_lot, id_klasa, cena, ilosc, kupione, data_od, data_do, dostepny FROM bilet_cennik ' \
            ' WHERE id_lot=:id_lot AND id_klasa=:id_klasa ORDER BY data_od, data_do '
    args = {
        'id_lot': flight_id,
        'id_klasa': class_id
    }
    return raw_query(query, args)


def generate_report(report):
    """
    Funkcje generująca raporty sprzedażowe dzienne, tygodniowe, miesięczne, roczne przy pomocy kostki
    w postaci (data, ilość sprzedanych, dochów, śerdnia cena)

    Args:
        report: string definiujący rodzaj raportu ('day', 'week', 'month', 'year')
    Returns:
        wygenerowane raporty sprzedażowe
    """
    if report != 'day' and report != 'week' and report != 'month' and report != 'year':
        return None
    query = " SELECT date_trunc('{}', data_zakupu), COUNT(*) AS ilosc, SUM(bc.cena) AS dochod, AVG(bc.cena) AS srednia_cena " \
            " FROM bilet_cennik AS bc INNER JOIN bilet_osoba AS bo ON bo.id_bilet_cennik=bc.id_bilet_cennik " \
            " GROUP BY CUBE (1) ORDER BY 1 ".format(report)
    return raw_query(query)


def buy_ticket(book_ticket_form):
    """
    Zakup biletu na podstawie danych wprowadzonych w formularzu (dane osobowe, rodzaj biletu) zakupu
    w tym celu wywoływana jest funkcja zdefiniowana w bazie danych

    Args:
        book_ticket_form: wypełniony formularz zakupu
    Returns:
        rezultat zakupu True / False
    """
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

