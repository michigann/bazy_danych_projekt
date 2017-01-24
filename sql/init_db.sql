drop TABLE bagaz_cennik cascade;
drop SEQUENCE samolot_id_samolot_seq cascade;
drop TABLE samolot cascade;
drop TABLE slownik cascade;
drop TABLE samolot_miejsca cascade;
drop SEQUENCE adres_id_adres_seq cascade;
drop TABLE adres cascade;
drop SEQUENCE lotnisko_id_lotnisko_seq cascade;
drop TABLE lotnisko cascade;
drop SEQUENCE lot_id_lot_seq cascade;
drop TABLE lot cascade;
drop TABLE bilet_cennik cascade;
drop SEQUENCE dane_osobowe_id_dane_osobowe_seq cascade;
drop TABLE dane_osobowe cascade;
drop TABLE pracownik cascade;
drop TABLE lot_pracownik cascade;
drop SEQUENCE uzytkownik_id_uzytkownik_seq cascade;
drop TABLE uzytkownik cascade;
drop TABLE bilet_osoba cascade;
drop TABLE lot_miejsca cascade;





CREATE TABLE public.bagaz_cennik (
                id_bagaz INTEGER NOT NULL,
                cena VARCHAR NOT NULL,
                od DATE NOT NULL,
                do_1 DATE NOT NULL,
                CONSTRAINT bagaz_cennik_pk PRIMARY KEY (id_bagaz)
);


CREATE SEQUENCE public.samolot_id_samolot_seq;

CREATE TABLE public.samolot (
                id_samolot INTEGER NOT NULL DEFAULT nextval('public.samolot_id_samolot_seq'),
                producent VARCHAR(30) NOT NULL,
                model VARCHAR(30) NOT NULL,
                CONSTRAINT samolot_pk PRIMARY KEY (id_samolot)
);


ALTER SEQUENCE public.samolot_id_samolot_seq OWNED BY public.samolot.id_samolot;

CREATE TABLE public.slownik (
                id_slownik INTEGER NOT NULL,
                zbior VARCHAR(30) NOT NULL,
                element VARCHAR(30) NOT NULL,
                CONSTRAINT slownik_pk PRIMARY KEY (id_slownik)
);


CREATE TABLE public.samolot_miejsca (
                id_slownik INTEGER NOT NULL,
                id_samolot INTEGER NOT NULL,
                ilosc INTEGER NOT NULL,
                CONSTRAINT samolot_miejsca_pk PRIMARY KEY (id_slownik, id_samolot)
);


CREATE SEQUENCE public.adres_id_adres_seq;

CREATE TABLE public.adres (
                id_adres INTEGER NOT NULL DEFAULT nextval('public.adres_id_adres_seq'),
                kraj VARCHAR(30) NOT NULL,
                miasto VARCHAR(30) NOT NULL,
                ulica VARCHAR(30) NOT NULL,
                nr VARCHAR(10) NOT NULL,
                nr_mieszkania VARCHAR(10),
                kod_pocztowy VARCHAR(10),
                CONSTRAINT adres_pk PRIMARY KEY (id_adres)
);


ALTER SEQUENCE public.adres_id_adres_seq OWNED BY public.adres.id_adres;

CREATE SEQUENCE public.lotnisko_id_lotnisko_seq;

CREATE TABLE public.lotnisko (
                id_lotnisko INTEGER NOT NULL DEFAULT nextval('public.lotnisko_id_lotnisko_seq'),
                nazwa VARCHAR(30) NOT NULL,
                id_adres INTEGER,
                CONSTRAINT lotnisko_pk PRIMARY KEY (id_lotnisko)
);


ALTER SEQUENCE public.lotnisko_id_lotnisko_seq OWNED BY public.lotnisko.id_lotnisko;

CREATE SEQUENCE public.lot_id_lot_seq;

CREATE TABLE public.lot (
                id_lot INTEGER NOT NULL DEFAULT nextval('public.lot_id_lot_seq'),
                nr_lot VARCHAR(30) NOT NULL,
                id_lotnisko_wylot INTEGER NOT NULL,
                id_lotnisko_przylot INTEGER NOT NULL,
                data_wylot TIMESTAMP NOT NULL,
                data_przylot TIMESTAMP NOT NULL,
                id_samolot INTEGER NOT NULL,
                CONSTRAINT lot_pk PRIMARY KEY (id_lot)
);


ALTER SEQUENCE public.lot_id_lot_seq OWNED BY public.lot.id_lot;

CREATE TABLE public.lot_miejsca (
                id_lot INTEGER NOT NULL,
                id_klasa INTEGER NOT NULL,
                ilosc INTEGER NOT NULL,
                CONSTRAINT lot_miejsca_pk PRIMARY KEY (id_lot, id_klasa)
);


CREATE SEQUENCE public.bilet_cennik_id_bilet_cennik_seq;

CREATE TABLE public.bilet_cennik (
                id_bilet_cennik INTEGER NOT NULL DEFAULT nextval('public.bilet_cennik_id_bilet_cennik_seq'),
                id_lot INTEGER NOT NULL,
                id_klasa INTEGER NOT NULL,
                cena INTEGER NOT NULL,
                ilosc INTEGER NOT NULL,
                kupione INTEGER NOT NULL,
                data_od DATE NOT NULL,
                data_do DATE DEFAULT null NOT NULL,
                dostepny INTEGER DEFAULT 1 NOT NULL,
                CONSTRAINT bilet_cennik_pk PRIMARY KEY (id_bilet_cennik)
);


ALTER SEQUENCE public.bilet_cennik_id_bilet_cennik_seq OWNED BY public.bilet_cennik.id_bilet_cennik;

CREATE SEQUENCE public.dane_osobowe_id_dane_osobowe_seq;

CREATE TABLE public.dane_osobowe (
                id_dane_osobowe INTEGER NOT NULL DEFAULT nextval('public.dane_osobowe_id_dane_osobowe_seq'),
                nr_osoba VARCHAR(30) NOT NULL,
                imie VARCHAR(30) NOT NULL,
                nazwisko VARCHAR(30) NOT NULL,
                data_urodzenia DATE NOT NULL,
                narodowosc VARCHAR(30) NOT NULL,
                id_adres INTEGER NOT NULL,
                CONSTRAINT dane_osobowe_pk PRIMARY KEY (id_dane_osobowe)
);


ALTER SEQUENCE public.dane_osobowe_id_dane_osobowe_seq OWNED BY public.dane_osobowe.id_dane_osobowe;

CREATE TABLE public.pracownik (
                id_pracownik INTEGER NOT NULL,
                id_dane_osobowe INTEGER NOT NULL,
                id_ranga INTEGER NOT NULL,
                CONSTRAINT pracownik_pk PRIMARY KEY (id_pracownik)
);


CREATE TABLE public.lot_pracownik (
                id_lot INTEGER NOT NULL,
                id_pracownik INTEGER NOT NULL,
                CONSTRAINT lot_pracownik_pk PRIMARY KEY (id_lot, id_pracownik)
);


CREATE SEQUENCE public.uzytkownik_id_uzytkownik_seq;

CREATE TABLE public.uzytkownik (
                id_uzytkownik INTEGER NOT NULL DEFAULT nextval('public.uzytkownik_id_uzytkownik_seq'),
                id_ranga INTEGER NOT NULL,
                email VARCHAR(256) NOT NULL,
                haslo VARCHAR(30) NOT NULL,
                id_dane_osobowe INTEGER DEFAULT null,
                CONSTRAINT uzytkownik_pk PRIMARY KEY (id_uzytkownik)
);


ALTER SEQUENCE public.uzytkownik_id_uzytkownik_seq OWNED BY public.uzytkownik.id_uzytkownik;

CREATE TABLE public.bilet_osoba (
                id_dane_osobowe INTEGER NOT NULL,
                id_bilet_cennik INTEGER NOT NULL,
                id_uzytkownik INTEGER NOT NULL,
                nr_miejsce INTEGER NOT NULL,
                data_zakupu DATE NOT NULL,
                bagaz_ilosc INTEGER NOT NULL,
                id_bagaz INTEGER DEFAULT null,
                CONSTRAINT bilet_osoba_pk PRIMARY KEY (id_dane_osobowe, id_bilet_cennik)
);


ALTER TABLE public.bilet_osoba ADD CONSTRAINT bagaz_cennik_bilet_osoba_fk
FOREIGN KEY (id_bagaz)
REFERENCES public.bagaz_cennik (id_bagaz)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot ADD CONSTRAINT samolot_lot_fk
FOREIGN KEY (id_samolot)
REFERENCES public.samolot (id_samolot)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.samolot_miejsca ADD CONSTRAINT samolot_samolot_miejsca_fk
FOREIGN KEY (id_samolot)
REFERENCES public.samolot (id_samolot)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.bilet_cennik ADD CONSTRAINT slownik_bilet_fk
FOREIGN KEY (id_klasa)
REFERENCES public.slownik (id_slownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.pracownik ADD CONSTRAINT slownik_pracownik_fk
FOREIGN KEY (id_ranga)
REFERENCES public.slownik (id_slownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.uzytkownik ADD CONSTRAINT slownik_user_fk
FOREIGN KEY (id_ranga)
REFERENCES public.slownik (id_slownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.samolot_miejsca ADD CONSTRAINT slownik_samolot_miejsca_fk
FOREIGN KEY (id_slownik)
REFERENCES public.slownik (id_slownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot_miejsca ADD CONSTRAINT slownik_lot_miejsca_fk
FOREIGN KEY (id_klasa)
REFERENCES public.slownik (id_slownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.dane_osobowe ADD CONSTRAINT adres_osoba_fk
FOREIGN KEY (id_adres)
REFERENCES public.adres (id_adres)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lotnisko ADD CONSTRAINT adres_lotnisko_fk
FOREIGN KEY (id_adres)
REFERENCES public.adres (id_adres)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot ADD CONSTRAINT lotnisko_lot_fk
FOREIGN KEY (id_lotnisko_wylot)
REFERENCES public.lotnisko (id_lotnisko)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot ADD CONSTRAINT lotnisko_lot_fk1
FOREIGN KEY (id_lotnisko_przylot)
REFERENCES public.lotnisko (id_lotnisko)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot_pracownik ADD CONSTRAINT lot_lot_pracownik_fk
FOREIGN KEY (id_lot)
REFERENCES public.lot (id_lot)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.bilet_cennik ADD CONSTRAINT lot_bilet_fk
FOREIGN KEY (id_lot)
REFERENCES public.lot (id_lot)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot_miejsca ADD CONSTRAINT lot_lot_miejsca_fk
FOREIGN KEY (id_lot)
REFERENCES public.lot (id_lot)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.bilet_osoba ADD CONSTRAINT bilet_bilet_osoba_fk
FOREIGN KEY (id_bilet_cennik)
REFERENCES public.bilet_cennik (id_bilet_cennik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.uzytkownik ADD CONSTRAINT osoba_user_fk
FOREIGN KEY (id_dane_osobowe)
REFERENCES public.dane_osobowe (id_dane_osobowe)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.bilet_osoba ADD CONSTRAINT osoba_bilet_osoba_fk
FOREIGN KEY (id_dane_osobowe)
REFERENCES public.dane_osobowe (id_dane_osobowe)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.pracownik ADD CONSTRAINT dane_osobowe_pracownik_fk
FOREIGN KEY (id_dane_osobowe)
REFERENCES public.dane_osobowe (id_dane_osobowe)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.lot_pracownik ADD CONSTRAINT pracownik_lot_pracownik_fk
FOREIGN KEY (id_pracownik)
REFERENCES public.pracownik (id_pracownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE public.bilet_osoba ADD CONSTRAINT user_bilet_fk
FOREIGN KEY (id_uzytkownik)
REFERENCES public.uzytkownik (id_uzytkownik)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;






INSERT INTO slownik (id_slownik, zbior, element) VALUES
    (1, 'user', 'klient'), (2, 'user', 'pracownik'), (3, 'user', 'admin'),
    (4, 'klasa', 'economy'), (5, 'klasa', 'business'),
    (6, 'pracownik', 'pilot'), (7, 'pracownik', 'stewardessa');

INSERT INTO uzytkownik (id_uzytkownik, id_ranga, email, haslo, id_dane_osobowe) VALUES 
    (1, 1, 'user@user.pl', 'password', null),
    (2, 3, 'admin@admin.pl', 'password', null);
