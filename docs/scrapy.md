

# scrapy 文档笔记

> 原文地址： https://docs.scrapy.org/en/latest/intro/tutorial.html#intro-tutorial

## 入门教程

1. 创建一个 scrapy 项目
2. 写一个 spider 用来爬取网站和其他的数据
3. 通过命令行导出爬到的数据
4. 修改 spider 以递归链接
5. 使用 spider 的参数

### 创建项目

```shell
scrapy startproject tutorial
```

### 第一个Spider

在`tutorial/spiders`文件夹下增加文件`quotes_spider.py`

```python
class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def start_requests(self):
        urls = [
            'http://quotes.toscrape.com/page/1/',
            'http://quotes.toscrape.com/page/2/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
```

运行爬虫

```shell
# 在项目根目录执行
scrapy crawl quotes
```

### start _requests 方法的快捷方式

直接在类里面定义start_urls 属性就行， 如下：

```python
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"  # spider 的名字, 项目唯一

    start_urls = [
            'http://quotes.toscrape.com/page/1/',
            'http://quotes.toscrape.com/page/2/',
        ]   # 新增加的属性

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = 'quotes-%s.html' % page
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

```

### 利用 scrapy shell 提取数据
用命令行的交互方式可以方便的尝试该如何提取数据
```shell
scrapy shell "http://quotes.toscrape.com/page/1/"
```
支持方式：
1. css

```shell
response.css('title') # 元素名字
```
2. xpath
```shell
response.xpath('//title')
```

### 在 spider 里面提取数据

修改 `quotes_spider.py`

```shell
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
        'http://quotes.toscrape.com/page/2/',
    ]

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
            }
```

运行spider，爬取到的信息会在日志中输出

### 存储爬取到的信息

使用[Feed exports](https://docs.scrapy.org/en/latest/topics/feed-exports.html#topics-feed-exports)

```shell
scrapy crawl quotes -o quotes.json
```

> **注意：** 当两次运行命令使用相同的输出文件，Scrapy 会追加内容到文件后部，而不是覆盖整个文件。

### 追踪链接(递归链接)

```python
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"  # spider 的名字, 项目唯一

    start_urls = [
            'http://quotes.toscrape.com/page/1/',
        ]

    def parse(self, response):
      	# 返回当前页面提取到的信息
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css("div.tags a.tag::text").getall(),
            }

        next_page = response.css('li.next a::attr(href)').get()  # 提取下一页链接
        if next_page:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)  # 递归调用

```

### 创建（递归）请求的快捷方式

```python
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"  # spider 的名字, 项目唯一

    start_urls = [
            'http://quotes.toscrape.com/',
        ]

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css("div.tags a.tag::text").getall(),
            }

        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

```

也可以同时跟踪多个链接

```python
for href in response.css('ul.pager a::attr(href)'):
    yield response.follow(href, callback=self.parse) 
```

如果提取的是超链接元素，这里还有一个快捷方式:

```python
for a in response.css('ul.pager a'):
    yield response.follow(a, callback=self.parse)
```

直接从可迭代的对象创建多个请求（而不是用上面的循环），可以使用`response.follow_all`

```python
anchors = response.css('ul.pager a')
yield from response.follow_all(anchors, callback=self.parse)
```

或者，更进一步简写：

```python
yield from response.follow_all(css='ul.pager a', callback=self.parse)
```

### 更复杂的多个链接递归追踪

```python
import scrapy


class AuthorSpider(scrapy.Spider):
    name = 'author'

    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        author_page_links = response.css('.author + a')
        yield from response.follow_all(author_page_links, self.parse_author)

        pagination_links = response.css('li.next a')
        yield from response.follow_all(pagination_links, self.parse)

    def parse_author(self, response):
        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        yield {
            'name': extract_with_css('h3.author-title::text'),
            'birthdate': extract_with_css('.author-born-date::text'),
            'bio': extract_with_css('.author-description::text'),
        }
```

*默认情况下 scrapy 会自动过滤掉对已经访问过的URL的重复请求。*

