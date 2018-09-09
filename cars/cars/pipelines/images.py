from scrapy.pipelines.images import ImagesPipeline
import hashlib
import logging
import os

from scrapy import Request
from scrapy.utils.python import to_bytes

logger = logging.getLogger(__name__)


class CarsImagesPipeline(ImagesPipeline):
    MIN_WIDTH = 100
    MIN_HEIGHT = 100

    def get_media_requests(self, item, info):
        return [Request(url, meta={'name': item.get('name')}) for url in item.get(self.images_urls_field, [])]

    def file_path(self, request, response=None, info=None):

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            url = request
        else:
            url = request.url

        name: str = request.meta['name']
        separator = " "
        if separator in name:
            model = name.split(separator)[0]
        else:
            model = "X"
        make = name.replace(u' ', u'_')
        media_guid = hashlib.sha1(to_bytes(url)).hexdigest()
        media_ext = os.path.splitext(url)[1]
        path = "{}/{}/{}{}".format(model, make, media_guid, media_ext)
        logger.info(path)
        return path
