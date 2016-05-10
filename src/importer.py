#!/usr/bin/env python2.6

import os
import csv
import logging
import optparse
import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, DataError

N_TYPE = 'N'
ECHO = False

USER = 'vasil'
PASS = 'vasil_pass'
HOST = '10.0.2.110'
PORT = '5432'
DB = 'andappstore'

URL = 'postgresql://%s:%s@%s:%s/%s' % (USER, PASS, HOST, PORT, DB)

meta = MetaData()
session = scoped_session(sessionmaker())


def _init_model(engine):
    global t_application
    global t_language
    global t_screenshot

    t_screenshot = sa.Table("screenshoturl", meta.metadata, autoload=True,
                            autoload_with=engine)
    t_application = sa.Table("application", meta.metadata, autoload=True,
                             autoload_with=engine)
    t_language = sa.Table("language", meta.metadata, autoload=True,
                          autoload_with=engine)
    orm.mapper(Book, t_application)
    orm.mapper(Language, t_language)
    orm.mapper(Screenshot, t_screenshot)
    session.configure(bind=engine)
    meta.engine = engine

t_screenshot = None
t_application = None
t_language = None


def _configure_logger():
    LOG_FILENAME = os.path.join('..', 'log', 'imps.log')
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=LOG_FILENAME)


class Language(object):

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.basic = False

    def __repr__(self):
        myclass = self.__class__.__name__
        return "<%s: %s : %s>" % (myclass, self.code, self.name)


class Screenshot(object):

    def __init__(self):
        pass


class Book(object):

    def __init__(self, name,
                 author,
                 language_code,
                 homeurl,
                 isbn,
                 released,
                 publisher_id=2785915):
        self.name = name
        self.author = author
        self.language_code = language_code
        self.homeurl = homeurl
        self.isbn = isbn
        try:
            released_date = datetime.date(
                *[int(x) for x in released.split('-')])
        except ValueError, e:
            logging.error('Error while parsing the released_date -- %s' % e)
            released_date = datetime.datetime.now()
        self.released = released_date

        self.publisher_id = publisher_id
        self.purchasingtype = N_TYPE
        self.disabled = False
        self.type = 2
        self.purchase_type = 0

    def __repr__(self):
        myclass = self.__class__.__name__
        return "<%s: %s -- %s>" % (myclass, self.name, self.author)


def main():
    _configure_logger()

    params = optparse.OptionParser(description='',
                                   prog='importer.py',
                                   version='0.1b',
                                   usage='%prog [metadata.csv]')
    params.add_option("-l", "--langs",
                      dest="langs",
                      default=None,
                      help="Import languages from the given lang file")
    options, arguments = params.parse_args()
    engine = create_engine(URL, echo=ECHO)
    _init_model(engine)

    if options.langs:

        lang_reader = csv.reader(open(options.langs, 'rb'),
                                 delimiter=',', quotechar='"')
        for (code, name) in lang_reader:
            lang = Language(code, name)
            session.add(lang)
            try:
                session.commit()
            except IntegrityError, e1:
                logging.error('Error while adding new language -- %s' % e1)
                session.rollback()
        return
    elif len(arguments) == 0:
        params.print_help()
        return

    md_reader = csv.reader(open(arguments[0], 'rb'),
                           delimiter=',', quotechar='"')
    for (author, name, language_code, homeurl, isbn, released) in md_reader:
        book = Book(name,
                    author,
                    language_code,
                    homeurl,
                    isbn.split('.')[0],
                    released)
        session.add(book)
        try:
            session.commit()
            logging.info('The book with ISBN:%s was inserted in the DB' % isbn)
        except IntegrityError, e1:
            logging.error('The book (%s) is already in the DB -- %s' % (isbn,
                                                                        e1))
            session.rollback()
        except DataError, e2:
            logging.error('The book (%s) has long name %s' % (isbn, e2))
            session.rollback()

if __name__ == "__main__":
    main()
