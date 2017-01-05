from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask import current_app, g


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = SQLAlchemy(current_app)
    return db


def get_dictionary_items(elements_set):
    d = {'zbior': elements_set}
    query = "SELECT id_slownik, element FROM slownik WHERE zbior=:zbior"
    _user_types = raw_query(query, d).fetchall()
    d = dict()
    for i in _user_types:
        d[i[1]] = i[0]
    return d


def get_dictionary_item_id(elements_set, element):
    d = {
        'zbior': elements_set,
        'element': element
    }
    query = "SELECT id_slownik, element FROM slownik WHERE zbior=:zbior AND element=:element"
    element_id = raw_query(query, d).first()
    return element_id[0]


def raw_query(query, args=None):
    e = get_db().engine
    if args is None:
        return e.execute(query)
    return e.execute(text(query), **args)

