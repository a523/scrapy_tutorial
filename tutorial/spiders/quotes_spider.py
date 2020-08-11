import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"  # spider 的名字, 项目唯一

    start_urls = [
            'http://quotes.toscrape.com/page/1/',
            'http://quotes.toscrape.com/page/2/',
        ]

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css("div.tags a.tag::text").getall(),
            }
