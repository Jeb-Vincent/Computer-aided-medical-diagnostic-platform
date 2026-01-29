from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from myapp.management.commands.crawl_article import ArticleCrawler
from urllib.parse import urljoin
import requests

class Command(BaseCommand):
    help = '自动爬取所有目录页的文章链接并抓取'

    def handle(self, *args, **options):
        base_directory_url = 'https://www.chima.org.cn/Html/News/Columns/34/'
        page = 1
        has_next_page = True

        while has_next_page:
            try:
                # 构造当前分页的URL
                current_url = f'{base_directory_url}{page}.html'
                self.stdout.write(f'正在爬取目录页：{current_url}')

                # 获取当前页面内容
                response = requests.get(current_url, timeout=10)
                response.encoding = 'utf-8'  # 根据实际编码调整
                soup = BeautifulSoup(response.text, 'html.parser')

                # 提取当前页面的所有文章链接
                article_links = []
                for li in soup.select('.column_list li.box_li'):
                    a_tag = li.select_one('.arR_top a.dy_title')
                    if a_tag and 'href' in a_tag.attrs:
                        href = a_tag['href']
                        # 拼接完整URL
                        full_link = urljoin(base_directory_url, href)
                        article_links.append(full_link)

                # 处理当前页面的链接
                for link in article_links:
                    self.stdout.write(f'正在爬取文章：{link}')
                    try:
                        article_crawler = ArticleCrawler(link)
                        content = article_crawler.fetch_content()
                        result = article_crawler.parse_content(content)
                        if result:
                            self.stdout.write(
                                self.style.SUCCESS(f'成功保存：{article_crawler.article.title}')
                            )
                        else:
                            self.stdout.write(f'文章已存在：{link}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'抓取失败 [{link}]：{str(e)}')
                        )

                # 检查是否还有下一页（此处需要根据实际页面结构判断）
                # 例如，检查是否存在"下一页"按钮或分页链接
                # 这里假设当页面不再有文章项时停止
                has_next_page = len(article_links) > 0

                page += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'目录页处理失败（第{page}页）：{str(e)}')
                )
                has_next_page = False  # 出错则停止循环