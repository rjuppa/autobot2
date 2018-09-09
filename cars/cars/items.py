# -*- coding: utf-8 -*-
import scrapy


class Car(scrapy.Item):
    url = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    price = scrapy.Field()
    year = scrapy.Field()
    distance = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
