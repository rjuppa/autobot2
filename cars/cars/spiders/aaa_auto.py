import sys
from scrapy.exceptions import DropItem
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse

from cars.items import Car


def get_domain(url):
    parsed = urlparse(url)
    return u'{uri.netloc}'.format(uri=parsed)


class AAAAutoSpider(CrawlSpider):
        """
        Scrapes products from site: aaaauto.cz

        """
        name = 'aaaauto'
        allowed_domains = ['aaaauto.pl', 'aaaauto.cz', 'aaaauto.sk', 'aaaauto.hu', 'aaaauto.eu']
        # start_urls = ['https://www.aaaauto.cz/ojete-vozy/', ]
        # start_urls = ['https://www.aaaauto.pl/pojazdy-uzywane', ]
        # start_urls = ['https://www.aaaauto.hu/hasznalt-autok/', ]
        start_urls = ['https://www.aaaauto.sk/ojazdene-vozidla/', ]

        rules = (
            # browse for detail
            Rule(LinkExtractor(restrict_css='div.cars h2', deny=[]), callback='parse_item'),

            # pagination
            Rule(LinkExtractor(restrict_css='div.pagination')),

            # product page
            # Rule(LinkExtractor(restrict_css='#sProdList .sku'), callback='parse_item')
        )

        def get_name(self, res):
            # name (string)
            # Car headline containing the brand and product name
            # arr = res.xpath('//div[@id="carCardHead"]//h1//text()').extract()
            # name = " ".join(arr)

            name = res.xpath('//div[@class="carAbout"]//h1/text()').extract()

            if not name:
                return ''

            if isinstance(name, list):
                name = " ".join(name)

            name = name.replace(u'  ', u' ')
            name = name.replace(u'\xa0', u' ')
            name = name.replace(u',', u' ')
            return name

        def get_brand(self, res):
            # brand: (string)
            # Product Brand Name
            text = res.xpath(
                '//div[@class="proDescAndReview"]'
                '//span[@itemprop="http://schema.org/brand"]/text()').extract_first()
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
            # text = res.xpath('//table[@class="transparentTable"]//tr/td/text()').extract_first()
            text = res.xpath('//div[@id="carButtons"]//table//tr/td/text()').extract_first()
            return text if text else ''

        def get_distance(self, res):
            # information: (string)
            # Dict array of specification objects in {name: specname, value: specvalue}
            dt = res.xpath('//section[@id="pdpSection_pdpProdDetails"]//dt/label/text()').extract()
            dd = res.xpath('//section[@id="pdpSection_pdpProdDetails"]//dd/a/text()').extract()
            result = dict()
            dt_count = len(dt)
            dd_count = len(dd)
            for i in range(min(dt_count, dd_count)):
                label = dt[i]
                value = dd[i]
                if label and value and value != '-':
                    result[label] = value
            return result

        def get_file_urls(self, res):
            # file_urls: (string list)
            # String array of "Technical Docs" URLs
            li = res.xpath('//section[@id="techDocsHook"]'
                           '//ul[@id="technicalData"]//a/@href').extract()
            return li if li else []

        def get_image_urls(self, res):
            # image_urls: (string list)
            # String Array of additional image urls
            # li = res.xpath('//div[@id="photosSlider"]//a[@itemprop="contentUrl"]/@href').extract()
            li = res.xpath(
                '//div[@class="carAbout"]//div[@id="fotoSlidesIn"]//span/a/@href').extract()
            return [url for url in li]

        def get_primary_image_url(self, res):
            # primary_image_url: (string)
            # URL of the main product image
            src = res.xpath('//img[@id="productMainImage"]/@data-full').extract_first()
            if src:
                return src
            src = res.xpath('//img[@id="productMainImage"]/@src').extract_first()
            return src if src and src[0] != '/' else ''

        def get_trail(self, res):
            # trail: (string list)
            return res.xpath('//div[@id="breadcrumb"]//li//a/text()').extract()[0:-1]

        def parse_item(self, response):
            name = self.get_name(response)
            url = response.url
            image_urls = self.get_image_urls(response)

            item = Car()
            item['url'] = url
            item['name'] = name
            # item['brand'] = self.get_brand(response)
            # item['price'] = self.get_price(response)
            item['year'] = self.get_year(response)
            # item['distance'] = self.get_distance(response)
            item['image_urls'] = image_urls

            yield item

        def parse_name(self, response):
            item = Car()
            name = self.get_name(response)
            url = response.url
            print("-----------: {}".format(name))
            item['url'] = response.url
            item['name'] = name
