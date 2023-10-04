from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
import json
from django.views.decorators.csrf import csrf_exempt
### Custom packages
from anime.utils import post_json 
from anime.utils import dictfetchall
from anime.utils import tuple_to_list
#Ovo ubacuje bitne module i funkcije za Django i custom packages.Naglaskom, render se koristi za renderovanje HTML template-a, 
#HttpResponse je koristen da vrati HTTP response , i razlicit DRM su ubaceni za DB operacije.

# Kada  user udje na home page, funkcija daje simple HTTP response sa datim tekstom "Home page placeholder."
def index(request):
    return HttpResponse('Home page placeholder')


@csrf_exempt #s ovim govorim stranici da mi ne treba token tj.da je izuzet(naziva se dekoratorom)
def login(request):
    #očekuje JSON podatke u zahtevu, izdvaja email i lozinku i ispituje bazu podataka da provjeri da li su ispravni.
    if request.method == 'POST':
        json_data = post_json(request)

        email = json_data['email']
        password = json_data['password']
        with connection.cursor() as cursor: #dozvoljava da se citaju podaci row by row
            cursor.execute(
                'SELECT Email FROM User WHERE Email = %s AND Password = %s',
                [email, password])
            row = cursor.fetchone()
            if row is None:
                return HttpResponse("Login failed")
            else:
                return HttpResponse(email)
        return HttpResponse(json_data['email'])
    else:
        return HttpResponse('Login placeholder')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        json_data = post_json(request)

        email = json_data['email']
        username = json_data['username']
        password = json_data['password']
        gender = json_data['gender']
        if gender == 'male':
            gender = 1
        elif gender == 'female':
            gender = 2
        else:
            gender = 3 #sta znam treba li se crnjaciti da 3 znaci "ostalo"
        with connection.cursor() as cursor:
            cursor.execute('SELECT Email FROM User WHERE Email = %s', [email])
            row = cursor.fetchone()
            if row is not None:
                return HttpResponse("Register failed")
            cursor.execute(
                'INSERT INTO User (Email, Username, Password, Gender) VALUES (%s, %s, %s, %s)',
                [email, username, password, gender])
        return HttpResponse(json_data['email'])
    else:
        return HttpResponse('Register page placeholder')

@csrf_exempt 
def anime_display(request): #funckija za popis anime-a i podataka 
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT animeID, name, imageLink FROM Anime')
            animes = tuple_to_list(cursor.fetchall())
            #atrributes = cursor.description
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall()) #sta je korisnik lajkovao 
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            watch = tuple_to_list(cursor.fetchall()) #sta je korisnik gledao
        for i in animes:
            i.append([i[0]] in likes)
            flag = True
            for j in watch:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
        # print(atrributes)
        # columns = [col[0] for col in atrributes].append('likestatus')
        # print(columns)
        # columns.append('watchstatus')
        columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
        query_dict = [dict(zip(columns, row)) for row in animes]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')
    
    return HttpResponse('Anime display placeholder')

@csrf_exempt
def detail_page(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        animeID = request.GET.get('animeID')
        #Unutar funkcije postavlja upit bazi podataka kako bi dohvatio detaljne informacije o animeu, 
        #uključujući datum izlaska, broj epizoda, studio,kreatora i oznake.
        #Takođe daje/hvata informacije o tome sviđa li se korisniku anime, status gledanja, ocjenu i prosječnu ocjenu anime-a
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT animeID, name, imageLink, releaseDate, releaseYear, episode, studio, director, tags 
            FROM Anime
            WHERE animeID = %s''', [animeID])
            animes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s AND animeID = %s', [email, animeID])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s AND animeID = %s', [email, animeID])
            watch = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID, rate FROM RateAnime WHERE email = %s AND animeID = %s', [email, animeID])
            userrate = tuple_to_list(cursor.fetchall())
            cursor.execute('''
            SELECT animeID, AVG(rate) 
            FROM RateAnime 
            GROUP BY animeID
            HAVING animeID = %s''', [animeID])
            rate = tuple_to_list(cursor.fetchall())
        for i in animes:
            i.append([i[0]] in likes)
            flag = True
            for j in watch:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
            flag = True
            for j in rate:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
            flag = True
            for j in userrate:
                if i[0] == j[0]:
                    i.append(int(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
        columns = ['animeID', 'name', 'imageLink', 'releaseDate', 'releaseYear', 'episode', 'studio', 'director', 'tags', 'likestatus', 'watchstatus', 'rate', 'userrate']
        query_dict = [dict(zip(columns, row)) for row in animes]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')
    
    return HttpResponse('Detail_page placeholder')

@csrf_exempt
def recommend(request): #funkcija pregleda koja preporučuje anime korisniku na temelju oznaka koje mu se sviđaju
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        #Unutar funkcije stvara privremene tablice za pronalaženje oznaka koje su se korisniku svidjele, 
        # a zatim koristi te oznake za preporuku animea koji se korisniku nisu svidjeli.
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TEMPORARY TABLE s AS
                (SELECT t.tag, COUNT(t.animeID) AS ct
                FROM LikeAnime l JOIN Anime_Tag t ON l.animeID = t.animeID
                WHERE l.email = %s 
                GROUP BY t.tag);
                ''', [email])
            cursor.execute('''
                CREATE TEMPORARY TABLE m AS 
                (SELECT t.animeID, SUM(s.ct) AS sum 
                FROM s JOIN Anime_Tag t ON s.tag = t.tag 
                GROUP BY t.animeID);
            ''')
            cursor.execute('''
                SELECT a.animeID, a.name, a.imageLink 
                FROM m JOIN Anime a ON m.animeID = a.animeID 
                WHERE a.animeID NOT IN 
                    (SELECT l.animeID FROM LikeAnime l WHERE l.email = %s) 
                    AND a.animeID NOT IN 
                    (SELECT w.animeID FROM WatchStatus w WHERE w.email = %s) 
                    AND a.animeID NOT IN 
                    (SELECT r.animeID FROM RateAnime r WHERE r.email = %s) 
                ORDER BY m.sum DESC;
            ''', [email, email, email])
            animes = tuple_to_list(cursor.fetchall())
            # cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            # likes = tuple_to_list(cursor.fetchall())
            # cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            # watch = tuple_to_list(cursor.fetchall())
            for i in animes:
                # i.append([i[0]] in likes)
                # flag = True
                # for j in watch:
                #     if i[0] == j[0]:
                #         i.append(str(j[1]))
                #         flag = False
                #         break
                #     if flag:
                #         i.append('0')
                i.append(0)
                i.append('0')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in animes]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Recommend tab placeholder')

@csrf_exempt
def popular(request): #funkcija pregleda koja dohvaća popis popularnih animea na temelju:
    #sastava bodovanja koji uzima u obzir broj lajkova, prosječnu ocjenu i broj gledanja
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        #Unutar funkcije, stvara privremene tablice 
        #za izračun rezultata za svaki anime na temelju spomenutih faktora, a zatim odabire 50 najboljih anime-a s najvišim ocjenama.
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TEMPORARY TABLE k AS 
                (SELECT l.animeID, COUNT(l.email) AS ct 
                FROM LikeAnime l 
                GROUP BY l.animeID);
                ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE s AS 
                (SELECT r.animeID, AVG(r.rate) AS avg 
                FROM RateAnime r 
                GROUP BY r.animeID);
            ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE n AS 
                (SELECT w.animeID, COUNT(w.email) AS ct 
                FROM WatchStatus w 
                WHERE w.status >= 1 AND w.status <= 3 
                GROUP BY w.animeID);
            ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE m AS 
                (SELECT s.animeID, s.avg + 4 * EXP(-1/k.ct) + 2 * EXP(-1/n.ct) AS score 
                FROM s JOIN k ON s.animeID = k.animeID JOIN n ON k.animeID = n.animeID);
            ''')
            cursor.execute('''
            SELECT a.animeID, a.name, a.imageLink 
                FROM m JOIN Anime a ON m.animeID = a.animeID
                ORDER BY m.score DESC
                LIMIT 50;
            ''')
            animes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            watch = tuple_to_list(cursor.fetchall())
            #Takođe hvata informacije o tome je li se korisniku svidio neki anime i njihov status gledanja za svaki anime
            for i in animes:
                i.append([i[0]] in likes)
                flag = True
                for j in watch:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                    if flag:
                        i.append('0')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in animes]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Popular tab placeholder')

@csrf_exempt
def wishlist(request): #funkcija pregleda koja hvata popis animea koje korisnik ima na popisu želja (status 1)
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.animeID, a.name, a.imageLink 
                FROM Anime a JOIN WatchStatus w on a.animeID = w.animeID
                WHERE w.email = %s AND w.status = 1''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('1')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Wishlist tab placeholder')

@csrf_exempt
def watched(request): #funkcija pregleda koja hvata popis animea koje je korisnik gledao (status 3)
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.animeID, a.name, a.imageLink 
                FROM Anime a JOIN WatchStatus w on a.animeID = w.animeID
                WHERE w.email = %s AND w.status = 3''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('3')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Watched tab placeholder')

@csrf_exempt 
def watching(request): #funkcija pregleda koja hvata popis animea koje korisnik trenutno gleda (status 2)
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.animeID, a.name, a.imageLink 
                FROM Anime a JOIN WatchStatus w on a.animeID = w.animeID
                WHERE w.email = %s AND w.status = 2''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('2')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Watching tab placeholder')

@csrf_exempt
def search(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        keyword = request.GET.get('value')
        #Upit za bazu 
        #Dodaje informacije o tome je li se korisniku svidio svaki anime i njihov status gledanja za svaki anime.
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT animeID, name, imageLink 
                FROM Anime 
                WHERE name LIKE %s''', ['%'+keyword+'%'])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            watch = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                flag = True
                for j in watch:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Search tab placeholder')


@csrf_exempt
def search_fav(request): #Funkcija za trazenje anime-a preko imena ali za dodatno filtriranje je kljucno da li ga je korisnik mark-ao
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        keyword = request.GET.get('name')
        #Upit u bazi za hvatanje popisa svidjenih(mark-anih) sa trazenim imenom
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.animeID, a.name, a.imageLink 
                FROM Anime a JOIN LikeAnime l on a.animeID = l.animeID
                WHERE a.email=%s AND a.name LIKE %s''', [email, '%'+keyword+'%'])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            watch = tuple_to_list(cursor.fetchall())
            #Dodaje informacije o korisnikovom statusu sviđanja (uvijek 1 budući da su to svidjeli anime) i status gledanja za svaki anime.
            for i in results:
                i.append(1)
                flag = True
                for j in watch:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Search_fav tab placeholder')


@csrf_exempt
def fav(request): #Funkcija prikaza koja upravlja i dobivanjem popisa omiljenih anime korisnika i dodavanjem/uklanjanjem animea s popisa omiljenih.
    if request.method == 'GET':
        #Za GET se uzimaju podaci o tome da li je korisnik barem jedan anime ubacio u favorite i sta je gledao
        email = request.GET.get('UserEmail')
        with connection.cursor() as cursor:
            # Return full fav list
            cursor.execute(
                'SELECT DISTINCT a.animeID AS animeID, a.name AS name, a.imageLink AS imageLink FROM Anime AS a, LikeAnime AS l WHERE l.email = %s AND l.animeID = a.animeID',
                [email])
            fav = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
            watch = tuple_to_list(cursor.fetchall())
            for i in fav:
                i.append(1)
                flag = True
                for j in watch:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
            query_dict = [dict(zip(columns, row)) for row in fav]
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
            
#U POST gleda radnju (action), gdje 1 predstavlja dodavanje u favorite, 
# a 0 predstavlja uklanjanje iz favorita. 
# U skladu s tim ažurira anime koji se sviđaju korisniku i vraća ažurirani popis animea koji se sviđaju.
    elif request.method == 'POST':
        json_data = post_json(request)
        email = json_data['email']
        animeID = json_data['animeID']
        isLike = json_data['action']
        with connection.cursor() as cursor:
            if isLike == 1:
                cursor.execute('SELECT email, animeID FROM LikeAnime WHERE email = %s AND animeID = %s', [email, animeID])
                if cursor.fetchone() is None:
                    cursor.execute('INSERT INTO LikeAnime (email, animeID) VALUES (%s, %s)', [email, animeID])
            else:
                cursor.execute('DELETE FROM LikeAnime WHERE email = %s AND animeID = %s', [email, animeID])
            # Return full fav list
            cursor.execute(
                'SELECT DISTINCT a.animeID AS animeID, a.name AS name FROM Anime AS a, LikeAnime AS l WHERE l.email = %s AND l.animeID = a.animeID',
                [email])
            query_dict = dictfetchall(cursor)
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
        
    return HttpResponse('Fav anime placeholder')



@csrf_exempt
def change_watch_status(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        # keyword = request.GET.get('name')
        animeID = request.GET.get('animeID')
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT a.animeID AS animeID, a.name AS name, w.status AS watchstatus FROM Anime AS a, WatchStatus AS w WHERE w.email = %s AND w.animeID = %s AND w.animeID = a.animeID',
                [email, animeID])
            query_dict = dictfetchall(cursor)
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
    #Dodajemo za POST metod watchstatus
    elif request.method == 'POST':
        json_data = post_json(request)
        email = json_data['email']
        animeID = json_data['animeID']
        status = json_data['watchstatus']
        with connection.cursor() as cursor:
            cursor.execute('SELECT status FROM WatchStatus WHERE email = %s AND animeID = %s', [email, animeID])
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO WatchStatus (email, animeID, status) VALUES (%s, %s, %s)', [email, animeID, int(status)])
            else:
                cursor.execute('UPDATE WatchStatus SET status = %s WHERE email = %s AND animeID = %s',[int(status), email, animeID])
            # Return full watchstatus lista
            cursor.execute(
                'SELECT DISTINCT a.animeID AS animeID, a.name AS name FROM Anime AS a, WatchStatus AS w WHERE w.email = %s AND w.animeID = a.animeID',
                [email])
            query_dict = dictfetchall(cursor)
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
    
    return HttpResponse('Change anime watching status')

# Za debug
@csrf_exempt
def debug_json(request):
    if request.method == 'POST':
        a = [{'parent_id': None, 'id': 54360982}, {'parent_id': None, 'id': 54360880}]
        return HttpResponse(json.dumps(a))
    else:
        return HttpResponse('Placeholder')

@csrf_exempt
def rate(request): #Korisnicka ocjena anime-a
    if request.method == 'POST':
        #Za POST zahtjev očekuje JSON podatke koji sadrže korisničku e-poštu (email), ID animea (animeID) i ocjenu korisnika (userrate).
        json_data = post_json(request)
        email = json_data['email']
        animeID = json_data['animeID']
        rate = json_data['userrate']
        with connection.cursor() as cursor:
            cursor.execute('SELECT rate FROM RateAnime WHERE email = %s AND animeID = %s', [email, animeID])
            # Ažurira ocjenu korisnika za anime u bazi podataka.
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO RateAnime (email, animeID, rate) VALUES (%s, %s, %s)', [email, animeID, rate])
            else:
                cursor.execute('UPDATE RateAnime SET rate = %s WHERE email = %s AND animeID = %s',[rate, email, animeID])
            return HttpResponse('OK')



@csrf_exempt
def date(request):
    #Očekuje UserEmail, godinu i mjesec kao parametre u GET zahtjevu.
    email = request.GET.get('UserEmail')
    # year is a string
    year = request.GET.get('year')
    # month is a string
    month = request.GET.get('month')
    year = int(year)
    month = int(month)
    monthMapList = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = monthMapList[month - 1]

    query_dict = None
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT animeID, name, imageLink 
            FROM Anime 
            WHERE releaseDate LIKE %s AND releaseYear = %s''', ['%'+month, year])
        results = tuple_to_list(cursor.fetchall())
        # atrributes = cursor.description
        # Konstruira upit za dohvaćanje animea koji je objavljen u navedenoj godini i mjesecu i odgovara korisnikovom statusu sviđanja i gledanja.
        cursor.execute('SELECT animeID FROM LikeAnime WHERE email = %s', [email])
        likes = tuple_to_list(cursor.fetchall())
        cursor.execute('SELECT animeID, status FROM WatchStatus WHERE email = %s', [email])
        watch = tuple_to_list(cursor.fetchall())
        # Zatim konstruira JSON odgovor s tim informacijama i vraća ih ili vraća "prazan" ako nema podataka.
        for i in results:
            i.append([i[0]] in likes)
            flag = True
            for j in watch:
                if i[0] == j[0]:
                    i.append(j[1])
                    flag = False
                    break
            if flag:
                i.append(0)
        columns = ['animeID', 'name', 'imageLink', 'likestatus', 'watchstatus']
        query_dict = [dict(zip(columns, row)) for row in results]
        # query_dict = dictfetchall(cursor)
    if query_dict is not None:
        return HttpResponse(json.dumps(query_dict))
    else:
        return HttpResponse('empty')

@csrf_exempt
def anime_like(request):
    # Očekuje UserEmail i animeID kao parametre u GET zahtjevu.
    email = request.GET.get('UserEmail')
    animeID = request.GET.get('animeID')
    #Upit za bazu
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM LikeAnime WHERE email = %s AND animeID = %s
        ''', [email, animeID])
        if cursor.fetchone() is None:
            return HttpResponse(json.dumps({'likestatus': 0}))
        else:
            return HttpResponse(json.dumps({'likestatus': 1}))

# Manga display
@csrf_exempt
def manga_display(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('SELECT mangaID, name, imageLink FROM Manga')
            mangas = tuple_to_list(cursor.fetchall())
            #atrributes = cursor.description
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall()) #sta je korisnik lajkovao 
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            read = tuple_to_list(cursor.fetchall()) #sta je korisnik citao
        for i in mangas:
            i.append([i[0]] in likes)
            flag = True
            for j in read:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
        # print(atrributes)
        # columns = [col[0] for col in atrributes].append('likestatus')
        # print(columns)
        # columns.append('readstatus')
        columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
        query_dict = [dict(zip(columns, row)) for row in mangas]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')
    
    return HttpResponse('Manga display placeholder')


def detail_page_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        mangaID = request.GET.get('mangaID')
        #Unutar funkcije postavlja upit bazi podataka kako bi dohvatio detaljne informacije o mangi, 
        #uključujući datum izlaska, broj chaptera, studio,kreatora i oznake.
        #Takođe daje/hvata informacije o tome sviđa li se korisnik umanga, status citanja, ocjenu i prosječnu ocjenu mange
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT mangaID, name, imageLink, releaseDate, releaseYear, chapter, studio, director, tags 
            FROM Manga
            WHERE mangaID = %s''', [mangaID])
            mangas = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s AND mangaID = %s', [email, mangaID])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s AND mangaID = %s', [email, mangaID])
            read = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID, rate FROM RateManga WHERE email = %s AND mangaID = %s', [email, mangaID])
            userrate = tuple_to_list(cursor.fetchall())
            cursor.execute('''
            SELECT mangaID, AVG(rate) 
            FROM RateManga 
            GROUP BY mangaID
            HAVING mangaID = %s''', [mangaID])
            rate = tuple_to_list(cursor.fetchall())
        for i in mangas:
            i.append([i[0]] in likes)
            flag = True
            for j in read:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
            flag = True
            for j in rate:
                if i[0] == j[0]:
                    i.append(str(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
            flag = True
            for j in userrate:
                if i[0] == j[0]:
                    i.append(int(j[1]))
                    flag = False
                    break
            if flag:
                i.append('0')
        columns = ['mangaID', 'name', 'imageLink', 'releaseDate', 'releaseYear', 'chapter', 'studio', 'director', 'tags', 'likestatus', 'readstatus', 'rate', 'userrate']
        query_dict = [dict(zip(columns, row)) for row in mangas]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')
    
    return HttpResponse('Detail_page_manga placeholder')

# Recommend manga for manga lovers
@csrf_exempt
def recommend_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        #Unutar funkcije stvara privremene tablice za pronalaženje oznaka koje su se korisniku svidjele, 
        # a zatim koristi te oznake za preporuku mange koji se korisniku nisu svidjeli.
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TEMPORARY TABLE s AS
                (SELECT t.tag, COUNT(t.mangaID) AS ct
                FROM LikeManga l JOIN Manga_Tag t ON l.mangaID = t.mangaID
                WHERE l.email = %s 
                GROUP BY t.tag);
                ''', [email])
            cursor.execute('''
                CREATE TEMPORARY TABLE m AS 
                (SELECT t.mangaID, SUM(s.ct) AS sum 
                FROM s JOIN Manga_Tag t ON s.tag = t.tag 
                GROUP BY t.mangaID);
            ''')
            cursor.execute('''
                SELECT a.mangaID, a.name, a.imageLink 
                FROM m JOIN Manga a ON m.mangaID = a.mangaID 
                WHERE a.mangaID NOT IN 
                    (SELECT l.mangaID FROM LikeManga l WHERE l.email = %s) 
                    AND a.mangaID NOT IN 
                    (SELECT w.mangaID FROM ReadStatus w WHERE w.email = %s) 
                    AND a.mangaID NOT IN 
                    (SELECT r.mangaID FROM RateManga r WHERE r.email = %s) 
                ORDER BY m.sum DESC;
            ''', [email, email, email])
            mangas = tuple_to_list(cursor.fetchall())
            # cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            # likes = tuple_to_list(cursor.fetchall())
            # cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            # read = tuple_to_list(cursor.fetchall())
            for i in mangas:
                # i.append([i[0]] in likes)
                # flag = True
                # for j in read:
                #     if i[0] == j[0]:
                #         i.append(str(j[1]))
                #         flag = False
                #         break
                #     if flag:
                #         i.append('0')
                i.append(0)
                i.append('0')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in mangas]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Recommend tab placeholder')

# Display popular manga
@csrf_exempt
def popular_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        #Unutar funkcije, stvara privremene tablice 
        #za izračun rezultata za svaki manga na temelju spomenutih faktora, a zatim odabire 50 najboljih manga-a s najvišim ocjenama.
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TEMPORARY TABLE k AS 
                (SELECT l.mangaID, COUNT(l.email) AS ct 
                FROM LikeManga l 
                GROUP BY l.mangaID);
                ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE s AS 
                (SELECT r.mangaID, AVG(r.rate) AS avg 
                FROM RateManga r 
                GROUP BY r.mangaID);
            ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE n AS 
                (SELECT w.mangaID, COUNT(w.email) AS ct 
                FROM ReadStatus w 
                WHERE w.status >= 1 AND w.status <= 3 
                GROUP BY w.mangaID);
            ''')
            cursor.execute('''
            CREATE TEMPORARY TABLE m AS 
                (SELECT s.mangaID, s.avg + 4 * EXP(-1/k.ct) + 2 * EXP(-1/n.ct) AS score 
                FROM s JOIN k ON s.mangaID = k.mangaID JOIN n ON k.mangaID = n.mangaID);
            ''')
            cursor.execute('''
            SELECT a.mangaID, a.name, a.imageLink 
                FROM m JOIN Manga a ON m.mangaID = a.mangaID
                ORDER BY m.score DESC
                LIMIT 50;
            ''')
            mangas = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            read = tuple_to_list(cursor.fetchall())
            #Takođe hvata informacije o tome je li se korisniku svidio neki manga i njihov status gledanja za svaki manga
            for i in mangas:
                i.append([i[0]] in likes)
                flag = True
                for j in read:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                    if flag:
                        i.append('0')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in mangas]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Popular tab placeholder')

# Display manga in the user's wishlist
@csrf_exempt
def wishlist_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.mangaID, a.name, a.imageLink 
                FROM Manga a JOIN ReadStatus w on a.mangaID = w.mangaID
                WHERE w.email = %s AND w.status = 1''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('1')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Wishlist tab placeholder')

# Display manga marked as "read" by the user
@csrf_exempt
def read_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.mangaID, a.name, a.imageLink 
                FROM Manga a JOIN ReadStatus w on a.mangaID = w.mangaID
                WHERE w.email = %s AND w.status = 3''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('3')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Read tab placeholder')

# Display manga marked as "reading" by the user
@csrf_exempt
def reading_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')

        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.mangaID, a.name, a.imageLink 
                FROM Manga a JOIN ReadStatus w on a.mangaID = w.mangaID
                WHERE w.email = %s AND w.status = 2''', [email])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                i.append('2')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Reading tab placeholder')

# Search for manga
@csrf_exempt
def search_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        keyword = request.GET.get('value')
        #Upit za bazu 
        #Dodaje informacije o tome je li se korisniku svidjela svaka manga i njihov status gledanja za svaka manga.
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT mangaID, name, imageLink 
                FROM Manga 
                WHERE name LIKE %s''', ['%'+keyword+'%'])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
            likes = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            read = tuple_to_list(cursor.fetchall())
            for i in results:
                i.append([i[0]] in likes)
                flag = True
                for j in read:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'mangastatus']
            query_dict = [dict(zip(columns, row)) for row in results]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Search_manga tab placeholder')

# Search for favorite manga
@csrf_exempt
def search_fav_manga(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        keyword = request.GET.get('name')
        #Upit u bazi za hvatanje popisa svidjenih(mark-anih) sa trazenim imenom
        query_dict = None
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT a.mangaID, a.name, a.imageLink 
                FROM Manga a JOIN LikeManga l on a.mangaID = l.mangaID
                WHERE a.email=%s AND a.name LIKE %s''', [email, '%'+keyword+'%'])
            results = tuple_to_list(cursor.fetchall())
            # atrributes = cursor.description
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            read = tuple_to_list(cursor.fetchall())
            #Dodaje informacije o korisnikovom statusu sviđanja (uvijek 1 budući da su to mange) i status gledanja za svaku mangu.
            for i in results:
                i.append(1)
                flag = True
                for j in read:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in results]
            # query_dict = dictfetchall(cursor)
        if query_dict is not None:
            return HttpResponse(json.dumps(query_dict))
        else:
            return HttpResponse('empty')

    return HttpResponse('Search_fav_manga tab placeholder')

# Manage favorite manga
@csrf_exempt
def favorite_manga(request):
    if request.method == 'GET':
        #Za GET se uzimaju podaci o tome da li je korisnik barem jednu manga ubacio u favorite i sta je citao
        email = request.GET.get('UserEmail')
        with connection.cursor() as cursor:
            # Return full fav list
            cursor.execute(
                'SELECT DISTINCT a.mangaID AS mangaID, a.name AS name, a.imageLink AS imageLink FROM Manga AS a, LikeAnime AS l WHERE l.email = %s AND l.mangaID = a.mangaID',
                [email])
            fav = tuple_to_list(cursor.fetchall())
            cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
            read = tuple_to_list(cursor.fetchall())
            for i in fav:
                i.append(1)
                flag = True
                for j in read:
                    if i[0] == j[0]:
                        i.append(str(j[1]))
                        flag = False
                        break
                if flag:
                    i.append('0')
            columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
            query_dict = [dict(zip(columns, row)) for row in fav]
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')

# Change the read status of manga
@csrf_exempt
def change_read_status(request):
    if request.method == 'GET':
        email = request.GET.get('UserEmail')
        # keyword = request.GET.get('name')
        mangaID = request.GET.get('mangaID')
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT a.mangaID AS mangaID, a.name AS name, w.status AS readstatus FROM Manga AS a, ReadStatus AS w WHERE w.email = %s AND w.mangaID = %s AND w.mangaID = a.mangaID',
                [email, mangaID])
            query_dict = dictfetchall(cursor)
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
    #Dodajemo za POST metod readstatus
    elif request.method == 'POST':
        json_data = post_json(request)
        email = json_data['email']
        mangaID = json_data['mangaID']
        status = json_data['readstatus']
        with connection.cursor() as cursor:
            cursor.execute('SELECT status FROM ReadStatus WHERE email = %s AND mangaID = %s', [email, mangaID])
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO ReadStatus (email, mangaID, status) VALUES (%s, %s, %s)', [email, mangaID, int(status)])
            else:
                cursor.execute('UPDATE ReadStatus SET status = %s WHERE email = %s AND mangaID = %s',[int(status), email, mangaID])
            # Return full readstatus lista
            cursor.execute(
                'SELECT DISTINCT a.mangaID AS mangaID, a.name AS name FROM Manga AS a, ReadStatus AS w WHERE w.email = %s AND w.mangaID = a.mangaID',
                [email])
            query_dict = dictfetchall(cursor)
            if query_dict is not None:
                return HttpResponse(json.dumps(query_dict))
            else:
                return HttpResponse('empty')
    
    return HttpResponse('Change manga reading status')

# Allow users to rate manga
@csrf_exempt
def rate_manga(request):
    if request.method == 'POST':
        #Za POST zahtjev očekuje JSON podatke koji sadrže korisničku e-poštu (email), ID mange (mangaID) i ocjenu korisnika (userrate).
        json_data = post_json(request)
        email = json_data['email']
        mangaID = json_data['mangaID']
        rate = json_data['userrate']
        with connection.cursor() as cursor:
            cursor.execute('SELECT rate FROM RateManga WHERE email = %s AND mangaID = %s', [email, mangaID])
            # Ažurira ocjenu korisnika za mangu u bazi podataka.
            if cursor.fetchone() is None:
                cursor.execute('INSERT INTO RateManga (email, mangaID, rate) VALUES (%s, %s, %s)', [email, mangaID, rate])
            else:
                cursor.execute('UPDATE RateManga SET rate = %s WHERE email = %s AND mangaID = %s',[rate, email, mangaID])
            return HttpResponse('OK')

# Display manga by release date
@csrf_exempt
def date_manga(request):
    #Očekuje UserEmail, godinu i mjesec kao parametre u GET zahtjevu.
    email = request.GET.get('UserEmail')
    # year is a string
    year = request.GET.get('year')
    # month is a string
    month = request.GET.get('month')
    year = int(year)
    month = int(month)
    monthMapList = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = monthMapList[month - 1]

    query_dict = None
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT mangaID, name, imageLink 
            FROM Manga 
            WHERE releaseDate LIKE %s AND releaseYear = %s''', ['%'+month, year])
        results = tuple_to_list(cursor.fetchall())
        # atrributes = cursor.description
        # Konstruira upit za dohvaćanje mangi koji je objavljen u navedenoj godini i mjesecu i odgovara korisnikovom statusu sviđanja i citanja.
        cursor.execute('SELECT mangaID FROM LikeManga WHERE email = %s', [email])
        likes = tuple_to_list(cursor.fetchall())
        cursor.execute('SELECT mangaID, status FROM ReadStatus WHERE email = %s', [email])
        read = tuple_to_list(cursor.fetchall())
        # Zatim konstruira JSON odgovor s tim informacijama i vraća ih ili vraća "prazan" ako nema podataka.
        for i in results:
            i.append([i[0]] in likes)
            flag = True
            for j in read:
                if i[0] == j[0]:
                    i.append(j[1])
                    flag = False
                    break
            if flag:
                i.append(0)
        columns = ['mangaID', 'name', 'imageLink', 'likestatus', 'readstatus']
        query_dict = [dict(zip(columns, row)) for row in results]
        # query_dict = dictfetchall(cursor)
    if query_dict is not None:
        return HttpResponse(json.dumps(query_dict))
    else:
        return HttpResponse('empty')

# Check if a manga is liked by a user
@csrf_exempt
def manga_like(request):
    # Očekuje UserEmail i mangaID kao parametre u GET zahtjevu.
    email = request.GET.get('UserEmail')
    mangaID = request.GET.get('mangaID')
    #Upit za bazu
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM LikeManga WHERE email = %s AND mangaID = %s
        ''', [email, mangaID])
        if cursor.fetchone() is None:
            return HttpResponse(json.dumps({'likestatus': 0}))
        else:
            return HttpResponse(json.dumps({'likestatus': 1}))

            




