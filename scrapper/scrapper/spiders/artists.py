# -*- coding: utf-8 -*-

import urlparse
import string
import scrapy

from scrapper.items import Artist, Version

PAGES_XPATH = "id('a_cont')/table//td/a/@href"

def first_or_none(l):
    if l:
        return l[0]


class ArtistSpider(scrapy.Spider):
    name = 'artists'
    allowed_domains = ['lacuerda.net', 'acordes.lacuerda.net',
                       'www.lacuerda.net']
    start_urls = ['http://acordes.lacuerda.net/tabs/%s/index0.html' % letter
                  for letter in list(string.ascii_lowercase) + ['_num']]
                  # for letter in 'ab']

    def parse(self, response):
        for link in response.xpath("id('i_main')/li/a/@href").extract():
            yield scrapy.Request(url=response.urljoin(link),
                                 callback=self.parse_artist)
        for link in response.xpath(PAGES_XPATH).extract():
            yield scrapy.Request(url=response.urljoin(link),
                                 callback=self.parse)

    def parse_artist(self, response):
        nombre = response.xpath("id('f_mid')//td[@class='mid']/"
                                "div[@class='f_rslt']/text()").extract()[0]
        genero = first_or_none(response.xpath("id('f_mid')//td[@class='sub']"
                                "/text()").extract())
        pais = first_or_none(response.xpath("id('f_mid')//td[2]/img"
                                            "/@src").re('/IMG/Bndr/(\w+)\.gif'))
        slug = urlparse.urlparse(response.url).path.split('/')[1]
        yield Artist(nombre=nombre, genero=genero, pais=pais, slug=slug)


