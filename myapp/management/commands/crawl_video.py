import re
import requests
import logging
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urljoin
from dateutil.parser import parse
from myapp.models import Video
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)


class CmaCatalogCrawler:
    def __init__(self, url, command):
        self.base_url = "https://www.cma.org.cn"
        self.command = command
        self.session = requests.Session()

        # 配置请求头和重试策略
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.base_url
        }

        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def fetch_page(self, page_num):
        """获取分页数据（XML格式）"""
        try:
            response = self.session.post(
                'https://www.cma.org.cn/module/web/jpage/dataproxy.jsp',
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://www.cma.org.cn',
                    'Referer': self.base_url + '/col/col982/index.html',
                    **self.headers
                },
                data={
                    'col': '1',
                    'webid': '1',
                    'path': '/',
                    'columnid': '982',
                    'sourceContentType': '1',
                    'unitid': '325',
                    'webname': '%E4%B8%AD%E5%8D%8E%E5%8C%BB%E5%AD%A6%E4%BC%9A',  # URL编码后的中文
                    'permissiontype': '0',
                    'page': page_num,
                    'pageSize': '20',
                    'uid': '325'  # 新增必要参数
                },
                timeout=15
            )
            response.raise_for_status()

            # 修复XML解析
            root = ET.fromstring(response.text)
            return {
                'total': int(root.find('totalrecord').text),
                'pages': int(root.find('totalpage').text),
                'html': ''.join([r.text for r in root.findall('recordset/record')])
            }
        except Exception as e:
            self.command.stdout.write(
                self.command.style.WARNING(f"第 {page_num} 页请求失败: {str(e)}")
            )
            return None

    def parse_links(self, html_content):
        """解析HTML内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        for li in soup.find_all('li'):
            a_tag = li.find('a', target='_blank')
            if not a_tag or not a_tag.get('href'):
                continue

            full_url = urljoin(self.base_url, a_tag['href'])

            # 日期解析增强
            date_span = li.find('span', class_='riq')
            pub_date = None
            if date_span and date_span.text.strip():
                try:
                    pub_date = datetime.strptime(date_span.text.strip(), "%Y年%m月%d日")
                except ValueError:
                    try:
                        pub_date = parse(date_span.text.strip())
                    except:
                        pass

            links.append({
                'url': full_url,
                'published_at': pub_date
            })

            self.command.stdout.write(
                self.command.style.NOTICE(f"发现链接: {full_url}" +
                                          (f" 日期: {pub_date}" if pub_date else ""))
            )
        return links

    def crawl(self):
        """执行爬取流程"""
        all_links = []
        try:
            # 获取第一页数据
            first_page = self.fetch_page(1)
            if not first_page:
                return []

            total_pages = first_page['pages']
            self.command.stdout.write(
                self.command.style.SUCCESS(f"总页数: {total_pages} 总记录: {first_page['total']}")
            )

            # 处理第一页
            page_links = self.parse_links(first_page['html'])
            all_links.extend(page_links)
            self.command.stdout.write(
                self.command.style.SUCCESS(f"第 1/{total_pages} 页 找到 {len(page_links)} 条记录")
            )

            # 遍历后续页
            for page in range(2, total_pages + 1):
                page_data = self.fetch_page(page)
                if not page_data:
                    continue

                page_links = self.parse_links(page_data['html'])
                all_links.extend(page_links)
                self.command.stdout.write(
                    self.command.style.SUCCESS(f"第 {page}/{total_pages} 页 找到 {len(page_links)} 条记录")
                )

        except Exception as e:
            self.command.stdout.write(
                self.command.style.ERROR(f"目录爬取失败: {str(e)}")
            )
            logger.exception("Crawl error")

        return all_links


class CmaVideoCrawler:
    """视频详情页处理器"""

    def __init__(self, url, list_published_at=None):
        self.url = url
        self.list_published_at = list_published_at
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.cma.org.cn/col/col982/index.html'
        }

    def parse_video(self):
        """解析视频详情页"""
        try:
            response = self.session.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"请求失败: {str(e)}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 标题解析
        title = soup.select_one('td.title').text.strip() if soup.select_one('td.title') else '无标题'

        # 解析 <video> 标签
        video_url = None
        video_tag = soup.find('video')
        if video_tag:
            src = video_tag.get('src')
            if src:
                video_url = urljoin(self.url, src)  # 解决相对路径问题

        # 如果 <video> 没有 src，则尝试从 JavaScript 里找
        if not video_url:
            script_tags = soup.find_all('script', text=True)
            for script in script_tags:
                match = re.search(r'flashvars=\{[^}]*f:"(.*?)"', script.text)
                if match:
                    video_url = urljoin(self.url, match.group(1))
                    break

        # 解析发布日期
        published_at = self.list_published_at
        if not published_at:
            date_text = soup.find(text=lambda t: '发布日期' in str(t))
            if date_text:
                try:
                    published_at = parse(date_text.split('：')[1].strip())
                except:
                    published_at = None

        return {
            'title': title,
            'video_url': video_url,
            'published_at': published_at,
            'source_name': "中华医学会科学普及部"
        }

    def save_to_db(self, data):
        """保存到数据库"""
        if not data['video_url']:
            raise ValueError("无效的视频地址")

        # 去重检查
        if Video.objects.filter(video_url=data['video_url']).exists():
            return {'status': 'exists', 'message': '视频已存在'}

        try:
            video = Video.objects.create(
                title=data['title'],
                video_url=data['video_url'],
                published_at=data['published_at'],
                source_name=data['source_name']
            )
            return {'status': 'success', 'video': video}
        except Exception as e:
            raise ValueError(f"数据库保存失败: {str(e)}")

    def run(self):
        """执行完整流程"""
        try:
            video_data = self.parse_video()
            result = self.save_to_db(video_data)
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'title': result['video'].title,
                    'video_id': result['video'].id
                }
            return result
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class Command(BaseCommand):
    help = "爬取中华医学会科普视频"

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='目标URL（目录页或视频页）')
        parser.add_argument('--verbose', action='store_true', help='显示详细日志')
        parser.add_argument('--max-page', type=int, default=0, help='最大爬取页数（测试用）')

    def handle_catalog(self, url, options):
        """处理目录页爬取"""
        self.stdout.write(self.style.SUCCESS("🚀 启动目录爬虫..."))
        crawler = CmaCatalogCrawler(url, self)

        try:
            video_list = crawler.crawl()
            if options['max_page'] > 0:
                video_list = video_list[:options['max_page'] * 20]

            self.stdout.write(self.style.SUCCESS(f"🔍 共发现 {len(video_list)} 个视频链接"))

            for idx, item in enumerate(video_list, 1):
                if options['verbose']:
                    self.stdout.write(
                        self.style.HTTP_INFO(f"🔄 处理进度: {idx}/{len(video_list)}") +
                        self.style.NOTICE(f" | 当前URL: {item['url']}")
                    )

                try:
                    result = CmaVideoCrawler(
                        item['url'],
                        list_published_at=item['published_at']
                    ).run()

                    if result['status'] == 'success':
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ 成功抓取: {result['title']} (ID: {result['video_id']})")
                        )
                    elif result['status'] == 'exists':
                        self.stdout.write(
                            self.style.WARNING(f"⏩ 跳过已存在: {item['url']}")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"❌ 失败: {result.get('message', '未知错误')}")
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ 处理异常: {str(e)}")
                    )
                    logger.error(f"视频处理失败: {item['url']} - {str(e)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 目录处理失败: {str(e)}"))
            logger.exception("目录爬取异常")

    def handle_single(self, url, options):
        """处理单个视频页"""
        try:
            result = CmaVideoCrawler(url).run()
            if result['status'] == 'success':
                self.stdout.write(
                    self.style.SUCCESS(f"✅ 成功抓取视频: {result['title']} (ID: {result['video_id']})")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ 失败: {result.get('message', '未知错误')}")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 处理失败: {str(e)}"))

    def handle(self, *args, **options):
        if 'col/col982/index' in options['url']:
            self.handle_catalog(options['url'], options)
        else:
            self.handle_single(options['url'], options)