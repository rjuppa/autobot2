# -*- coding: utf-8 -*-
import hashlib
import logging
import os

from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.project import get_project_settings
from scrapy.utils.python import to_bytes

logger = logging.getLogger(__name__)


class CarsPipeline(object):
    def process_item(self, item, spider):
        return item


class CarsImagesPipeline(ImagesPipeline):
    MIN_WIDTH = 100
    MIN_HEIGHT = 100

    def file_path(self, request, response=None, info=None):

        name = self.get_name(response)

        logger.debug("=======")
        logger.debug("== 0 ==")
        logger.debug("=======")

        # check if called from file_key with url as first argument
        if not isinstance(request, Request):
            url = request
        else:
            url = request.url

        media_guid = hashlib.sha1(
            to_bytes(url)).hexdigest()  # change to request.url after deprecation
        media_ext = os.path.splitext(url)[1]  # change to request.url after deprecation
        return 'all/%s%s' % (media_guid, media_ext)