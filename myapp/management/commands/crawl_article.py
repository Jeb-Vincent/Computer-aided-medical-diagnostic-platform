from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, NavigableString
import re
from myapp.models import Article, Paragraph, Image


class ArticleCrawler:
    BASE_URL = 'https://www.chima.org.cn'
    IMAGE_FILTERS = [
        r'/Common/images/',
        r'/UserUpLoad/',
        r'206387806206834608595421129\.jpg$'
    ]

    def __init__(self, url):
        self.full_url = urljoin(self.BASE_URL, url) if not url.startswith('http') else url
        self.article = None
        self.image_counter = 1

    def fetch_content(self):
        try:
            response = requests.get(
                self.full_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise Exception(f"请求失败: {str(e)}")

    def parse_content(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        # 提取标题
        title_tag = soup.find('h1', class_='article_title')
        title = title_tag.get_text(strip=True) if title_tag else '无标题'

        # 解析日期
        created_at = timezone.now()
        sub_tit_div = soup.find('div', class_='sub_tit')
        if sub_tit_div:
            for span in sub_tit_div.find_all('span'):
                text = span.get_text(strip=True)
                if '发布时间：' in text:
                    date_str = text.split('发布时间：')[-1].strip()
                    created_at = self.parse_date(date_str)
                    break

        # 创建或获取文章
        self.article, created = Article.objects.get_or_create(
            source_url=self.full_url,
            defaults={'title': title, 'created_at': created_at}
        )
        if not created:
            return False

        # 处理正文内容
        content_div = soup.find('div', id='zoom') or soup.find('div', class_='article_cont') or soup
        self.process_mixed_content(content_div)
        return True

    def parse_date(self, date_str):
        try:
            return timezone.datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return timezone.now()

    def process_mixed_content(self, container):
        with transaction.atomic():
            order = 0
            # 获取所有直接子元素（包含文本节点）
            elements = container.find_all(recursive=False)

            for element in elements:
                # 跳过隐藏元素
                if element.get('style') and 'display: none' in element.get('style'):
                    continue

                order += 1
                if element.name == 'img':
                    self.process_image(element, order)
                else:
                    self.process_element(element, order)

    def process_element(self, element, order):
        """处理包含混合内容的元素"""
        current_order = order
        # 使用生成器处理混合内容
        for content in element.contents:
            if isinstance(content, NavigableString):
                text = content.strip()
                if text:
                    Paragraph.objects.create(
                        article=self.article,
                        content=text,
                        order=current_order
                    )
                    current_order += 1
            elif content.name == 'img':
                self.process_image(content, current_order)
                current_order += 1
            elif content.name in ['p', 'div', 'section']:
                # 递归处理嵌套元素
                self.process_element(content, current_order)
                current_order += 1

    def process_image(self, img_tag, order):
        src = img_tag.get('src', '')
        if not self.is_valid_image(src):
            return

        # 创建完整图片URL
        full_image_url = urljoin(self.BASE_URL, src)

        # 创建图片记录
        image = Image.objects.create(
            article=self.article,
            url=full_image_url,
            identifier=f"img_{self.image_counter}",
            order=self.image_counter
        )
        self.image_counter += 1

        # 创建图片占位段落
        Paragraph.objects.create(
            article=self.article,
            content="[IMAGE_PLACEHOLDER]",
            image_ref=image,
            order=order
        )

    def is_valid_image(self, src):
        return not any(
            re.search(pattern, src)
            for pattern in self.IMAGE_FILTERS
        )


class Command(BaseCommand):
    help = '抓取文章并存储图文关系'

    def add_arguments(self, parser):
        parser.add_argument('urls', nargs='+', type=str, help='文章URL列表')

    def handle(self, *args, **options):
        for rel_url in options['urls']:
            try:
                crawler = ArticleCrawler(rel_url)
                html_content = crawler.fetch_content()
                result = crawler.parse_content(html_content)

                if result:
                    msg = f'成功保存：{crawler.article.title}（图片{crawler.image_counter - 1}张）'
                    self.stdout.write(self.style.SUCCESS(msg))
                else:
                    self.stdout.write(f'文章已存在：{rel_url}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'抓取失败 [{rel_url}]：{str(e)}'))