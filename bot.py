import requests
from discord.ext import commands
from data.auth_data import DC_TOKEN
import discord
import os


TOKEN = DC_TOKEN

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
        print(json_response)
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
        embed.add_field(name='!!find_shops',
                        value='Введи свой адрес и бот вышлет карту с координатами четырех ближайших книжных магазинов',
                        inline=True)

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
        await channel.send('\n'.join([f'{i + 1} - "{shops_names[i]}" {shops_addresses[i]}' for i in range(len(shops_names))]))
        os.remove(map_file)


bot = commands.Bot(command_prefix='!!')
bot.add_cog(BookBot(bot))
bot.run(TOKEN)
