# -*- coding: utf-8 -*-

"""
Funkcje ułatwiające obsługę bazy danych
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask import current_app, g


def get_db():
    """
    Funkcja ułatwiająca pobranie handlera do bazy danych

    Returns:
        handler bazy danych
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = SQLAlchemy(current_app)
    return db


def get_db_engine():
    """
    Pobieranie silnika bazy danych - wykonującego zapytań do bazy

    Returns:
        silnik bazy danych
    """
    return get_db().engine


def get_dictionary_items(elements_set):
    """
    Funkcja pobierająca słownik elementów dla danego zbioru

    Args:
        elements_set: zbiór dla którego pobierane są elementy
    Returns:
        słownik elementów w postaci
        {
            ['nazwa elementu']: id_slownik,
        }
    """
    d = {'zbior': elements_set}
    query = "SELECT id_slownik, element FROM slownik WHERE zbior=:zbior"
    _user_types = raw_query(query, d).fetchall()
    d = dict()
    for i in _user_types:
        d[i[1]] = i[0]
    return d


def get_dictionary_item_id(elements_set, element):
    """
    Funkcja umożliwiająca pobranie id elementu danego zbioru słownika

    Args:
        elements_set: zbiór
        element: element dla którego id chcemy dostać
    Returns:
        id elementu / None
    """
    d = {
        'zbior': elements_set,
        'element': element
    }
    query = "SELECT id_slownik, element FROM slownik WHERE zbior=:zbior AND element=:element"
    element_id = raw_query(query, d).first()
    return element_id[0]


def raw_query(query, args=None):
    """
    Funkcja umożliwiająca wykonanie zapytania do bazy danych

    Args:
        query: polecenie sql
        args: słownik wartości elementów uwzględnionych w query
    Returns:
        odpowiedź z bazy danych (wybrane elementy przy pomocy select, id wstawionego / edytowanego elementu
    """
    e = get_db_engine()
    if args is None:
        return e.execute(query)
    return e.execute(text(query), **args)

