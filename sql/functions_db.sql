DROP FUNCTION najnizsza_cena(integer);
DROP FUNCTION obecna_cena(integer, integer);
DROP FUNCTION kup_bilet(integer, integer, integer);
DROP TRIGGER lot_trigger ON lot;
DROP FUNCTION walidacja_lotu();
DROP TRIGGER bilet_cennik_trigger ON bilet_cennik;
DROP FUNCTION walidacja_bilet_cennik();
DROP TRIGGER lot_miejsca_trigger ON lot;
DROP FUNCTION lot_miejsca_dodaj();




-- funkcja pozwalająca na wyszukanie najniższej ceny dla danego lotu
CREATE OR REPLACE FUNCTION najnizsza_cena(_id_lot integer) RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT cena
    FROM bilet_cennik AS b_c
    JOIN lot_miejsca AS l_m ON l_m.id_lot = b_c.id_lot
    WHERE
      b_c.id_lot = _id_lot AND
	    CURRENT_DATE >= b_c.data_od AND
	    CURRENT_DATE <= b_c.data_do AND
	    b_c.dostepny = 1 AND
	    b_c.kupione < b_c.ilosc
    ORDER BY b_c.cena LIMIT 1);
END;

$$ LANGUAGE plpgsql;



-- funkcja zwracająca informacje o obecnej cenie dla danego lotu w danej klasie
-- informacjami tymi są (id_bilet_cennik, cena, ilość dostępnych biletów w tej cenie)
CREATE OR REPLACE FUNCTION obecna_cena(_id_lot integer, _id_klasa integer)
RETURNS TABLE (
    _id_bilet_cennik integer,
    _cena            integer,
    _ilosc           integer ) AS $$
BEGIN
    RETURN QUERY
    SELECT
	    id_bilet_cennik, cena,
	    CASE 
		    WHEN b_c.ilosc - b_c.kupione <= l_m.ilosc 
		    THEN b_c.ilosc - b_c.kupione
		    ELSE l_m.ilosc
	    END AS ilosc
    FROM bilet_cennik AS b_c
    JOIN lot_miejsca AS l_m ON l_m.id_lot = b_c.id_lot AND l_m.id_klasa = b_c.id_klasa
    WHERE 
        b_c.id_lot = _id_lot AND
        b_c.id_klasa = _id_klasa AND
	    CURRENT_DATE >= b_c.data_od AND 
	    CURRENT_DATE <= b_c.data_do AND
	    b_c.dostepny = 1 AND
	    b_c.kupione < b_c.ilosc
    ORDER BY b_c.cena LIMIT 1;
END;
$$ LANGUAGE plpgsql;



-- funckcja obsługująca zakup biletu
-- jeśli w trakcie zakupu ktoś inny kupił bilet (o danej cenie) lub bilet został oznaczony jako niedostępny
-- tranzakcja nie zostanie zakończona pomyślnie
-- w takim wypadku funkcja rzuca wyjątek jeśli będy nie wystąpiły zwracane jest 1 a bilet zostaje kupiony
CREATE OR REPLACE FUNCTION kup_bilet(_id_dane_osobowe integer, _id_bilet_cennik integer, _id_uzytkownik integer) 
RETURNS integer as $$
DECLARE
    _id_lot     integer;
    _id_klasa   integer;   
    x           integer;
    y           integer; 
    z           integer;
BEGIN
    _id_lot = ( SELECT id_lot FROM bilet_cennik WHERE id_bilet_cennik=_id_bilet_cennik LIMIT 1);
    _id_klasa = ( SELECT id_klasa FROM bilet_cennik WHERE id_bilet_cennik=_id_bilet_cennik LIMIT 1);    
    
    UPDATE bilet_cennik SET kupione = kupione+1 WHERE id_bilet_cennik=_id_bilet_cennik;
    UPDATE lot_miejsca SET ilosc = ilosc-1 WHERE id_lot=_id_lot AND id_klasa=_id_klasa;
    
    x = ( SELECT ilosc FROM lot_miejsca WHERE id_lot=_id_lot AND id_klasa=_id_klasa LIMIT 1 );
    y = ( SELECT ilosc-kupione FROM bilet_cennik WHERE id_bilet_cennik=_id_bilet_cennik LIMIT 1 );   
    z = ( SELECT dostepny FROM bilet_cennik WHERE id_bilet_cennik=_id_bilet_cennik LIMIT 1);  
    
    IF ( x<0 ) THEN
        RAISE EXCEPTION 'brak biletow na lot';
    END IF;
    IF ( y<0 ) THEN
        RAISE EXCEPTION 'brak biletow w tej cenie';
    END IF;
    IF ( z != 1 ) THEN
        RAISE EXCEPTION 'bilet w tej cenie jest niedostpeny';
    END IF; 
    
    y = ( SELECT ilosc FROM lot INNER JOIN samolot_miejsca ON samolot_miejsca.id_samolot=lot.id_samolot AND id_slownik=_id_klasa WHERE id_lot=_id_lot ); 
    
   
    
    INSERT INTO bilet_osoba (id_dane_osobowe, id_bilet_cennik, id_uzytkownik, nr_miejsce, data_zakupu, bagaz_ilosc, id_bagaz) 
    VALUES (_id_dane_osobowe, _id_bilet_cennik, _id_uzytkownik, y-x+1, CURRENT_DATE, 0, null);
    
    RETURN 1;
END;
$$ LANGUAGE plpgsql;



-- funkcja dodająca dostępne miejsca dla lotu na podstawie zdefiniowanego dla niego samolotu
-- po dodaniu lotu do tabeli lot wyzwalana jest ta funkcja w celu ustawienia ilości miejsc w danych klasach
CREATE OR REPLACE FUNCTION lot_miejsca_dodaj() RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO lot_miejsca (id_lot, id_klasa, ilosc)
        SELECT NEW.id_lot, id_slownik, ilosc FROM samolot_miejsca WHERE id_samolot=NEW.id_samolot;
        RETURN NULL;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER lot_miejsca_trigger
  AFTER INSERT
    ON lot
  FOR EACH ROW
EXECUTE PROCEDURE lot_miejsca_dodaj();



-- wyzwalacz walidacyjny dla lotu (data wylotu, przylotu oraz lotnisko wylotu, przylotu)
CREATE OR REPLACE FUNCTION walidacja_lotu() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.data_wylot >= NEW.data_przylot THEN
            RAISE 'data_wylot >= data_przylot';
        END IF;

        IF NEW.id_lotnisko_wylot = NEW.id_lotnisko_przylot THEN
            RAISE 'id_lotnisko_wylot = id_lotnisko_przylot';
        END IF;

        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER lot_trigger
  BEFORE UPDATE OR INSERT
    ON lot
  FOR EACH ROW
EXECUTE PROCEDURE walidacja_lotu();



-- wyzwalacz walidacyjny dla tabeli bilet_cennik (data od, data do)
CREATE OR REPLACE FUNCTION walidacja_bilet_cennik() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.data_od > NEW.data_do THEN
            RAISE 'data_od > data_do';
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER bilet_cennik_trigger
  BEFORE UPDATE OR INSERT
    ON bilet_cennik
  FOR EACH ROW
EXECUTE PROCEDURE walidacja_bilet_cennik();
