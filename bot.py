import requests
from discord.ext import commands
from data.auth_data import DC_TOKEN
import discord
import os
from bs4 import BeautifulSoup
import wikipedia
from data.users import User
from data.books import Books
from data.author import Author
from data.genres import Genre
from data import db_session
import random

TOKEN = DC_TOKEN
wikipedia.set_lang('ru')
db_session.global_init("db/book_shop.sqlite")
bot = commands.Bot(command_prefix='!!')


def get_ll(toponym):
    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    ll = ",".join([toponym_longitude, toponym_lattitude])

    return ll


def search_bookshop(toponym):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    address_ll = get_ll(toponym)

    search_params = {
        "apikey": api_key,
        "text": "Книжный магазин",
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)
    if response:
        json_response = response.json()
        org_point = ''  # переменная содержит координаты всех десяти аптек
        for i in range(4):
            organization = json_response["features"][i]
            point = organization["geometry"]["coordinates"]
            org_point += "{0},{1};".format(point[0], point[1])
        org_point = org_point.split(';')
        string = ''
        names, addresses = [], []
        for i in range(4):
            hours = json_response["features"][i]['properties']['CompanyMetaData']['Hours']['text']
            if not hours:
                string += '{0},pm2grl{1}~'.format(org_point[i], i + 1)
            elif 'круглосуточно' in hours:
                string += '{0},pm2gnl{1}~'.format(org_point[i], i + 1)
            else:
                string += '{0},pm2bll{1}~'.format(org_point[i], i + 1)
            names.append(json_response["features"][i]['properties']['name'])
            addresses.append(json_response["features"][i]['properties']['description'])
        string += '{0},flag'.format(address_ll)
        return string, names, addresses


class BookBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help_bot')
    async def help_bot(self, channel):

        embed = discord.Embed(
            colour=discord.Colour.blue()
        )
        embed.set_author(name='Что бот умеет?')
        embed.add_field(name='**!!find_shops**',
                        value='Введи свой адрес, а бот вышлет карту с координатами четырех ближайших книжных магазинов',
                        inline=False)
        embed.add_field(name='**!!15_best_fantasy**',
                        value='Бот вышлет 15 лучших книг и их авторов в жанре фэнтези',
                        inline=False)
        embed.add_field(name='**!!10_popular_authors**',
                        value='Бот вышлет 10 самых популярных писателей в мире и ссылки в Википедии на них',
                        inline=False)
        embed.add_field(name='**!!wiki_author**',
                        value='Введи автора, а бот вышлет короткую информацию о нем и ссылку в Википедии',
                        inline=False)
        embed.add_field(name='**!!wiki_book**',
                        value='Введи название книги, а бот вышлет короткую информацию о ней и ссылку в Википедии',
                        inline=False)
        embed.add_field(name='**!!add_book** (для админа)',
                        value='Админ может добавит книгу в наш магазин.'
                              '\n**Формат: фамилия автора, название, жанр,'
                              'год создания, стоимость, url — ссылка на обложку книги**',
                        inline=False)
        embed.add_field(name='**!!add_author** (для админа)',
                        value='Админ может добавить автора книг в наш магазин.'
                              '\n**Формат: имя, фамилия, '
                              'годы жизни (YEAR-YEAR), несколько его известных произведений через ;** ',
                        inline=False)
        embed.add_field(name='**!!random_db_book**',
                        value='Бот вышлет информацию о случайной книге из базы данных!',
                        inline=False)
        embed.add_field(name='**!!all_books**',
                        value='Бот вышлет информацию о всех книгах из базы данных!',
                        inline=False)
        embed.add_field(name='**!!all_authors**',
                        value='Бот вышлет информацию о всех авторах из базы данных!',
                        inline=False)
        embed.add_field(name='**!!review**',
                        value='Напиши название книги и узнай отзывы к ней! **Формат: с большой буквы без кавычек!**',
                        inline=False)
        embed.add_field(name='**!!all_reviews**',
                        value='Бот вышлет все отзывы к книгам!',
                        inline=False)

        await channel.send(embed=embed)

    @commands.command(name='find_shops')
    async def find_shops(self, channel, *place):
        place = ' '.join(place)
        req = "http://geocode-maps.yandex.ru/1.x/" \
              "?apikey=40d1649f-0493-4b70-98ba-98533de7710b" \
              "&geocode=Москва, {}&format=json".format(place)
        response = requests.get(req)
        # Определяю координаты введенного адреса
        if response:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            ll = get_ll(toponym)
        delta = "0.025"
        string, shops_names, shops_addresses = search_bookshop(toponym)
        map_api_server = "http://static-maps.yandex.ru/1.x/"
        map_params = {
            "ll": ll,
            "spn": ','.join([delta, delta]),
            'pt': string,
            "l": "map"
        }
        response = requests.get(map_api_server, params=map_params)
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        await channel.send(file=discord.File(map_file))
        await channel.send(
            '\n'.join([f'{i + 1} - "{shops_names[i]}" {shops_addresses[i]}' for i in range(len(shops_names))]))
        os.remove(map_file)

    @commands.command(name='15_best_fantasy')
    async def best_fantasy(self, channel):
        url = 'https://miridei.com/idei-dosuga/kakuyu-knigu-pochitat/top15_knig_v_zhanre_fentezi/'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        embed = discord.Embed(
            title='**15 лучших книг в жанре фэнтези**',
            url=url,
            colour=discord.Colour.blue()
        )
        for i in soup.find_all('h2'):
            index, book_and_author = i.get_text().split('.')
            embed.add_field(name=index,
                            value=book_and_author,
                            inline=True)
        await channel.send(embed=embed)

    @commands.command(name='10_popular_authors')
    async def popular_authors(self, channel):
        url = 'https://infox.tv/posts/general/348/napisano-perom-10-russkih-pisateley-izvestnyh-vo-vsem-mire/'
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        embed = discord.Embed(
            title='**10 популярных русских писаталей в мире**',
            url=url,
            colour=discord.Colour.blue()
        )
        for i in soup.find_all('strong'):
            index, book_author = i.get_text().split('.')
            name, surname = book_author.split()
            embed.add_field(name=f'**{index}. {book_author}**',
                            value=f'https://ru.wikipedia.org/wiki/{name}_{surname}',
                            inline=False)
        await channel.send(embed=embed)

    @commands.command(name='wiki_author')
    async def wiki_author(self, channel, *author):
        try:
            name, surname = author
            url = f'https://ru.wikipedia.org/wiki/{name}_{surname}'
            embed = discord.Embed(
                title=f'**Информация об авторе** (Википедия)',
                url=url,
                colour=discord.Colour.blue()
            )
            embed.add_field(name=f'**{name} {surname}**',
                            value=wikipedia.summary(f'{author}', sentences=2),
                            inline=True)
            await channel.send(embed=embed)
        except ValueError:
            await channel.send("Напиши только имя и фамилию автора, пожалуйста!")
        except wikipedia.exceptions.PageError:
            await channel.send("Ошибочка, такой страницы нет!")
        except wikipedia.exceptions.DisambiguationError:
            await channel.send("Не могу определить автора, попробуй еще раз")

    @commands.command(name='wiki_book')
    async def wiki_book(self, channel, *book):
        try:
            book = '_'.join(book)
            url = f'https://ru.wikipedia.org/wiki/{book}'
            embed = discord.Embed(
                title=f'**Информация об книге** (Википедия)',
                url=url,
                colour=discord.Colour.blue()
            )
            embed.add_field(name=f'**{book}**',
                            value=wikipedia.summary(f'{book}', sentences=2),
                            inline=True)
            await channel.send(embed=embed)
        except wikipedia.exceptions.PageError:
            await channel.send("Ошибочка, такой страницы нет!")
        except wikipedia.exceptions.DisambiguationError:
            await channel.send("Не могу определить автора, попробуй еще раз")

    @commands.command(name='random_db_book')
    async def random_db_book(self, channel):
        session = db_session.create_session()
        books = session.query(Books).all()
        book = books[random.randint(0, len(books) - 1)]
        embed = discord.Embed(
            title=f'**Информация о книге из базы данных!**',
            colour=discord.Colour.blue()
        )
        embed.add_field(name=f'**Название**',
                        value=book.title,
                        inline=False)
        author = session.query(Author).filter(Author.id == book.author_id).first()
        embed.add_field(name=f'**Автор**',
                        value=f"{author.name} {author.surname}",
                        inline=False)
        embed.add_field(name=f'**Год создания**',
                        value=book.date,
                        inline=False)
        embed.add_field(name=f'**Стоимость в нашем магазине**',
                        value=book.price,
                        inline=False)
        await channel.send(embed=embed, file=discord.File(f'static/img/book{book.id}.jpg'))

    @commands.command(name='add_book')
    @commands.has_role('admin')
    async def add_book(self, channel, *content):
        try:
            surname, title, date, genre, price, url = ' '.join(content).split(',')
            surname, title, date, genre, price, url = surname.strip(), title.strip(), \
                                                      genre.strip(), date.strip(), price.strip(), url.strip()
            session = db_session.create_session()
            if session.query(Books).filter(Books.title == title).first():
                await channel.send("Такая книга уже есть в БД")
                return
            if not session.query(Genre).filter(Genre.genre == genre).first():
                await channel.send('Такого жанра нет в БД')
                return
            book = Books(
                author_id=session.query(Author).filter(Author.surname == surname).first().id,
                title=title,
                date=date,
                price=price,
                genre_id=session.query(Genre).filter(Genre.genre == genre).first().id
            )
            response = requests.get(url)
            len_books = len(session.query(Books).all())
            photo = f'static/img/book{len_books + 1}.jpg'
            with open(photo, 'wb') as imgfile:
                imgfile.write(response.content)
            book.cover = f'book{len_books + 1}.jpg'
            session.add(book)
            session.commit()
            await channel.send('Ваша книга успешно добавлена')
        except AttributeError:
            await channel.send('Увы, но автора вашей книги не оказалось у нас в базе данных...'
                               '\nДобавьте автора, а потом книгу!')

    @commands.command(name='add_author')
    @commands.has_role('admin')
    async def add_author(self, channel, *content):
        name, surname, years, books = ' '.join(content).split(',')
        name, surname, years, books = name.strip(), surname.strip(), years.strip(), books.strip()
        books = books.replace(';', ',').strip()
        session = db_session.create_session()
        if session.query(Author).filter(Author.surname == surname).first():
            await channel.send('Автор с такой фамилией уже есть в БД')
            return
        author = Author(
            name=name,
            surname=surname,
            years=years,
            list_of_books=books
        )
        session.add(author)
        session.commit()
        await channel.send('Ваш автор успешно добавлен')

    @commands.command(name='all_books')
    async def all_books(self, channel):
        session = db_session.create_session()
        books = session.query(Books).all()
        for book in books:
            embed = discord.Embed(
                title=f'**Информация о книге {book.id} из базы данных!**',
                colour=discord.Colour.blue()
            )
            embed.add_field(name=f'**Название**',
                            value=book.title,
                            inline=False)
            author = session.query(Author).filter(Author.id == book.author_id).first()
            embed.add_field(name=f'**Автор**',
                            value=f"{author.name} {author.surname}",
                            inline=False)
            embed.add_field(name=f'**Год создания**',
                            value=book.date,
                            inline=False)
            embed.add_field(name=f'**Стоимость в нашем магазине**',
                            value=book.price,
                            inline=False)
            await channel.send(embed=embed, file=discord.File(f'static/img/book{book.id}.jpg'))

    @commands.command(name='all_authors')
    async def all_authors(self, channel):
        session = db_session.create_session()
        authors = session.query(Author).all()
        for author in authors:
            embed = discord.Embed(
                title=f'**Информация об авторе {author.id} из базы данных!**',
                colour=discord.Colour.blue()
            )
            embed.add_field(name=f'**Имя, фамилия**',
                            value=f'{author.name} {author.surname}',
                            inline=False)
            embed.add_field(name=f'**Годы жизни**',
                            value=f"{author.years}",
                            inline=False)
            embed.add_field(name=f'**Популярные книги автора**',
                            value=author.list_of_books,
                            inline=False)
            await channel.send(embed=embed)

    @commands.command(name='review')
    async def review(self, channel, *book):
        book = ' '.join(book)
        session = db_session.create_session()
        book = session.query(Books).filter(Books.title == book).first()

        if not book:
            await channel.send('Такой книги у нас нет')
            return
        if not book.review:
            await channel.send('Отзывов к данной книге у нас еще нет...')
            return
        reviews = book.review.strip('+').split('+')
        embed = discord.Embed(
            title=f"**Отзывы о книге '{book.title}'**",
            colour=discord.Colour.blue()
        )
        count = 0
        for r in reviews:
            count += 1
            embed.add_field(name=f'**Отзыв №{count}**',
                            value=r,
                            inline=False)
        await channel.send(embed=embed)

    @commands.command(name='all_reviews')
    async def review(self, channel):
        session = db_session.create_session()
        books = session.query(Books).all()
        for book in books:
            if not book.review:
                embed = discord.Embed(
                    title=f"**Отзывы о книге '{book.title}' у нас еще нет...**",
                    colour=discord.Colour.blue()
                )
                await channel.send(embed=embed)
                return
            reviews = book.review.strip('+').split('+')
            embed = discord.Embed(
                title=f"**Отзывы о книге '{book.title}'**",
                colour=discord.Colour.blue()
            )
            count = 0
            for r in reviews:
                count += 1
                embed.add_field(name=f'**Отзыв №{count}**',
                                value=r,
                                inline=False)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, channel, error):
        if isinstance(error, commands.errors.MissingRole):
            await channel.send('У вас нет прав доступа к данной команде.')


bot.add_cog(BookBot(bot))
print('Bot started')
bot.run(TOKEN)
