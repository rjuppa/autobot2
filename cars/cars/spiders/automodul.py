import json
import sys
from scrapy.exceptions import DropItem
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse

from cars.items import Car


def get_domain(url):
    parsed = urlparse(url)
    return u'{uri.netloc}'.format(uri=parsed)


class AutoModulSpider(CrawlSpider):
        """
        Scrapes products from site: mobile.de

        """
        name = 'automodul'
        domain = "automodul.cz"
        allowed_domains = [domain]
        start_urls = ['https://www.automodul.cz/osobni-vyber?p=1&d=1&cenaod=10%20000', ]
        year = ""

        rules = ()

        def get_name(self, res):
            # name (string)
            # Car headline containing the brand and product name
            names = res.xpath('//div[@id="main"]/p[@id="popis"]/text()').extract()

            if not names:
                return ''

            if isinstance(names, list):
                name = " ".join(names)
            else:
                name = names

            name = name.replace(u'Třída', u'')
            name = name.replace(u'  ', u' ')
            name = name.replace(u'\xa0', u' ')
            name = name.replace(u',', u' ')
            return name

        def get_brand(self, res):
            # brand: (string)
            # Product Brand Name
            text = res.xpath('//title/meta[@property="og:title"]/@content').extract()
            if not text:
                self.logger.error('Missing brand: %s', res.url)
                return ''
            return text

        def get_price(self, res):
            # unit_price: (float)
            # price = res.xpath('//div[@id="priceTable"]/@data-price').extract_first()
            # price = price.replace(',', '')  # remove thousands separator
            return float(0)

        def get_year(self, res):
            return ""

        def get_file_urls(self, res):
            # file_urls: (string list)
            # String array of "Technical Docs" URLs
            li = res.xpath('//section[@id="techDocsHook"]'
                           '//ul[@id="technicalData"]//a/@href').extract()
            arr = []
            for href in li:
                if not href.startswith("http"):
                    href = "https:{}".format(href)
                arr.append(href)

            return arr if arr else []

        def get_image_urls(self, res):
            # image_urls: (string list)
            # String Array of additional image urls
            li = res.xpath('//div[@id="thumbs"]//img/@data-src').extract()
            arr = []
            for href in li:
                if not href.startswith("http"):
                    href = "https:{}".format(href)
                arr.append(href)

            return arr if arr else []

        def parse_item(self, response):
            name = self.get_name(response)
            url = response.url
            image_urls = self.get_image_urls(response)
            item = Car()
            item['url'] = url
            year = self.year.strip()
            item['image_urls'] = image_urls
            arr_name = name.split(" ")
            if arr_name[0] == "Land" or arr_name[0] == "Alfa":
                name = "{} {}".format(" ".join(arr_name[:3]), year)
            else:
                name = "{} {}".format(" ".join(arr_name[:2]), year)
            item['name'] = name

            yield item

        def parse(self, response):
            links = response.xpath('//div[@id="obsah"]//h2/a/@href').extract()
            years = response.xpath('//table[@class="parametry"]//tr[contains(., "Vyrobeno")]//td/text()').extract()
            for i, url in enumerate(links):
                url = self.fix_url(url)
                year = years[i].strip()
                url = url + "?vyrobeno={}".format(year)
                yield Request(url, callback=self.parse_detail)

            links = response.xpath('//div[@class="pager"]//a/@href').extract()
            for url in links:
                url = self.fix_url(url)
                yield Request(url, callback=self.parse)

        def fix_url(self, url):
            if url.startswith("//"):
                url = "https:{}".format(url)
            else:
                if not url.startswith("http"):
                    url = "https://{}/{}".format(self.domain, url)
            return url

        def parse_detail(self, response):
            if "skoda" in response.url:
                raise DropItem

            if "volkswagen" in response.url:
                raise DropItem

            iframes = response.xpath('//iframe/@src').extract()
            for frame in iframes:
                if "aaaauto" in frame:
                    # AAA Auto
                    raise DropItem

            if "?vyrobeno=" in response.url:
                parts = response.url.split("?vyrobeno=")
                self.year = parts[1].strip()
                # detail
                url = response.xpath('//a[@class="fotogalerie-link"]/@href').extract_first()
                if not url:
                    raise DropItem  # frame

                url = self.fix_url(url)
                yield Request(url, callback=self.parse_item)
