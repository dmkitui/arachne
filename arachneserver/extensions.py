from scrapy import signals
from scrapy.exporters import CsvItemExporter, JsonItemExporter
from datetime import datetime
from arachneserver.flaskapp import spiders_info


class ExportData(object):

    def __init__(self):
        self.files = {}
        self.exporter = None

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signals.item_scraped)
        return ext

    def spider_opened(self, spider):
        raise NotImplementedError

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file_to_save = self.files.pop(spider)
        file_to_save.close()

    def item_scraped(self, item, spider):
        self.exporter.export_item(item)
        return item


class ExportCSV(ExportData):
    """
    Exporting to export/csv/spider-name.csv file
    """
    def spider_opened(self, spider):
        file_to_save = open('exports/csv/%s.csv' % spider.name, 'w+b')
        self.files[spider] = file_to_save
        self.exporter = CsvItemExporter(file_to_save)
        self.exporter.start_exporting()


class ExportJSON(ExportData):
    """
    Exporting to export/json/spider-name.json file
    """
    def spider_opened(self, spider):
        file_to_save = open('exports/json/%s.json' % spider.name, 'w+b')
        self.files[spider] = file_to_save
        self.exporter = JsonItemExporter(file_to_save)
        self.exporter.start_exporting()


class ApplicationData(object):
    """
    Extension to handle the spider information reading from file and writing the a just completed spider's information
     to file.
    """
    def __init__(self, stats):
        self.files = {}
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.stats)
        crawler.signals.connect(ext.spider_opened, signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signals.spider_closed)
        return ext

    @staticmethod
    def spider_opened(spider):
        from arachneserver.flaskapp import SPIDER_STATUS
        try:
            SPIDER_STATUS[spider.name]['running'] = True
        except KeyError:
            SPIDER_STATUS[spider.name] = {}
            SPIDER_STATUS[spider.name]['running'] = True

        SPIDER_STATUS[spider.name]['time_started'] = datetime.now()

    def spider_closed(self, spider):
        from arachneserver.flaskapp import SPIDER_STATUS
        stats = self.stats.get_stats()
        data = {
            'last_run': stats['finish_time'],
            'avg_time': stats['finish_time'] - stats['start_time'],
            'running': False,
            'exit_code': stats['finish_reason']
        }
        SPIDER_STATUS[spider.name] = data
        spiders_info(action='write')
