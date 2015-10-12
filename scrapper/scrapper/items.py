# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class Artist(scrapy.Item):
    slug = scrapy.Field()
    nombre = scrapy.Field()
    genero = scrapy.Field()
    pais = scrapy.Field()


class Song(scrapy.Item):
    artista = scrapy.Field()
    slug = scrapy.Field()
    nombre = scrapy.Field()

class Version(Song):
    version_number = scrapy.Field()
    formato = scrapy.Field()
    votos = scrapy.Field()
    puntaje = scrapy.Field()
    autor = scrapy.Field()
    album = scrapy.Field()
    codigo = scrapy.Field()
    transcriptor = scrapy.Field()
    contenido = scrapy.Field()
    acordes = scrapy.Field()
