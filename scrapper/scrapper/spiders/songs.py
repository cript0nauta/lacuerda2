# -*- coding: utf-8 -*-

import re
import operator
import urlparse
import scrapy

from scrapper.spiders.artists import ArtistSpider, first_or_none
from scrapper.items import Song, Version

SONGS_XPATH = "id('b_main')/li/a/@href"
TITLE_XPATH = "id('r_head')/h1/text()[2]"
TRCAL_XPATH = "//script[contains(@src, 'cal.php')]/@src"

VERSION_XPATHS = {
    "album": "id('t_h3')[count(font)=0]/strong[2]/following::text()[1]",
    "autor": "id('t_h3')[count(font)=0]/strong[1]/following::text()[1]",
    "codigo": "id('t_h2')/div/text()",
    "transcriptor": "id('t_h4')/div/a/@href"
}
ACORDES_XPATH = "id('t_body')/pre/a/text()"

TRCAL_RE = (r"trcal\[(?P<version>\d+)\]=\['(?P<format>\w+)',"
            "'(?P<puntaje>[0-9\.]+)',(?P<votos>\d+)\]")
TRANSCRIPTOR_RE = r"\('A:([^']+)'\)"

class SongSpider(ArtistSpider):
    name = 'songs'

    def __init__(self, artist=None, *args, **kwargs):
        super(SongSpider, self).__init__(*args, **kwargs)
        self.artist = artist
        if artist:
            self.start_urls = ['http://acordes.lacuerda.net/%s/' % artist]

    def parse(self, response):
        if not self.artist:
            # Uso todos los artistas
            return super(SongSpider, self).parse(response)
        else:
            return self.parse_artist(response)

    def parse_artist(self, response):
        artist = next(super(SongSpider, self).parse_artist(response))
        for req in yield_links_requests(response,
                                        SONGS_XPATH,
                                        self.parse_song,
                                        artist=artist['slug']):
            yield req

    def parse_song(self, response):
        title = response.xpath(TITLE_XPATH).extract()[0]
        title = title.rsplit(' ', 1)[0]  # Quito el " Tab"
        slug = urlparse.urlparse(response.url).path.split('/')[2]

        cal_url = response.xpath(TRCAL_XPATH).extract()[0]
        song = Song(nombre=title, slug=slug, artista=response.meta['artist'])
        yield scrapy.Request(url=response.urljoin(cal_url),
                             callback=self.parse_cal,
                             meta=dict(response=response, song=song))

    def parse_cal(self, cal_response):
        groupdicts = map(operator.methodcaller('groupdict'),
                         re.finditer(TRCAL_RE, cal_response.body))
        trcal = {int(gd['version']): {"puntaje": float(gd['puntaje']),
                                      "votos": int(gd['votos']),
                                      "formato": gd['format']}
                 for gd in groupdicts}
        song = cal_response.meta['song']
        for version, version_info in trcal.items():
            yield scrapy.Request(self.version_url(song, version),
                                 callback=self.parse_version,
                                 meta=dict(song=song, version=version,
                                           version_info=version_info))

    def version_url(self, song, version, txt=False):
        return ('http://acordes.lacuerda.net{txt}/{artist}/'
                '{slug}{i}.{ext}'.format(
                    txt='/TXT' if txt else '',
                    artist=song['artista'],
                    slug=song['slug'],
                    i='-%s' % version if version > 1 else '',
                    ext='txt' if txt else 'shtml'
                ))

    def parse_version(self, response):
        v = Version()
        v['version_number'] = response.meta['version']
        v.update(response.meta['song'])
        v.update(response.meta['version_info'])
        for key, xpath in VERSION_XPATHS.items():
            v[key] = get_xpath(response, xpath)
        v['acordes'] = response.xpath(ACORDES_XPATH).extract()

        t = re.search(TRANSCRIPTOR_RE,
                       v['transcriptor'])
        if t:
            v['transcriptor'] = t.group(1)

        yield scrapy.Request(self.version_url(v, v['version_number'], True),
                             # encoding='iso-8859-2',
                             callback=self.parse_version_txt,
                             meta=dict(version=v))

    def parse_version_txt(self, response):
        version = response.meta['version']
        version['contenido'] = response.body_as_unicode()
        yield version


def yield_links_requests(response, xpath, callback, **kwargs):
    for link in response.xpath(xpath).extract():
        yield scrapy.Request(url=response.urljoin(link),
                             callback=callback,
                             meta=kwargs)


def get_xpath(response, xpath):
    return first_or_none(response.xpath(xpath).extract())


