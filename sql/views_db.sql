DROP VIEW loty_backoffice;
DROP VIEW loty_klient;
DROP VIEW kupione_bilety;



CREATE VIEW loty_backoffice AS
SELECT id_lot, nr_lot, lw.nazwa AS lotnisko_wylot, lp.nazwa AS lotnisko_przylot, data_wylot, data_przylot, id_samolot,
        (SELECT SUM(ilosc) FROM lot_miejsca AS lm WHERE lm.id_lot=lot.id_lot) AS miejsca_wolne,
        (SELECT SUM(ilosc) FROM samolot_miejsca AS sm WHERE sm.id_samolot=lot.id_samolot) AS miejsca_wszystkie
FROM lot
INNER JOIN lotnisko AS lw ON id_lotnisko_wylot=lw.id_lotnisko
INNER JOIN lotnisko AS lp ON id_lotnisko_przylot=lp.id_lotnisko ORDER BY data_wylot;


CREATE VIEW loty_klient AS
SELECT id_lot, nr_lot, lw.nazwa AS lotnisko_wylot, lp.nazwa AS lotnisko_przylot, data_wylot, data_przylot,
      (SELECT * FROM najnizsza_cena(id_lot)) AS cena, id_lotnisko_wylot, id_lotnisko_przylot
FROM lot
INNER JOIN lotnisko AS lw ON id_lotnisko_wylot=lw.id_lotnisko
INNER JOIN lotnisko AS lp ON id_lotnisko_przylot=lp.id_lotnisko
WHERE data_wylot>=CURRENT_TIMESTAMP AND (SELECT * FROM najnizsza_cena(id_lot)) IS NOT null;


CREATE VIEW kupione_bilety AS
SELECT bo.id_dane_osobowe, bo.id_bilet_cennik, bo.id_uzytkownik, imie, nazwisko,
        lw.nazwa AS lwylot, lp.nazwa AS lprzylot, lot.data_wylot, lot.data_przylot
FROM bilet_osoba AS bo
INNER JOIN dane_osobowe AS da ON da.id_dane_osobowe=bo.id_dane_osobowe
INNER JOIN bilet_cennik AS bc ON bc.id_bilet_cennik=bo.id_bilet_cennik
INNER JOIN lot ON lot.id_lot=bc.id_lot
INNER JOIN lotnisko AS lw ON lot.id_lotnisko_wylot=lw.id_lotnisko
INNER JOIN lotnisko AS lp ON lot.id_lotnisko_przylot=lp.id_lotnisko
INNER JOIN slownik AS s ON s.id_slownik=bc.id_klasa;
