from django.db import transaction
from .models import Article, Paragraph, Image
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging

logger = logging.getLogger(__name__)


def fetch_and_save_article():
    url = 'https://www.chima.org.cn/Html/News/Articles/17293.html'

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        with transaction.atomic():
            # 创建文章记录
            article_title = soup.title.string if soup.title else "无标题"
            article = Article.objects.create(
                title=article_title,
                source_url=url
            )

            content_div = soup.find('article') or soup.find('div', class_='content') or soup

            # 第一遍处理：收集元素
            elements = []
            current_img_index = 0
            for element in content_div.find_all(['p', 'img']):
                if element.name == 'img':
                    src = element.get('src', '')
                    if not (re.search(r'/Common/images/', src) or
                            re.search(r'/UserUpLoad/', src) or
                            src.endswith('206387806206834608595421129.jpg')):
                        elements.append({
                            'type': 'image',
                            'src': urljoin(url, src),
                            'identifier': f"图{current_img_index + 1}".replace(" ", ""),
                            'order': current_img_index
                        })
                        current_img_index += 1
                else:
                    text = element.get_text(strip=True)
                    if text:
                        # 计算段落的顺序（仅统计已存在的段落数量）
                        paragraph_count = len([e for e in elements if e['type'] == 'paragraph'])
                        elements.append({
                            'type': 'paragraph',
                            'text': text,
                            'order': paragraph_count
                        })

            # 批量创建图片
            images = []
            for e in elements:
                if e['type'] == 'image':
                    images.append(
                        Image(
                            article=article,
                            url=e['src'],
                            identifier=e['identifier'],
                            order=e['order']
                        )
                    )
            Image.objects.bulk_create(images)

            # 批量创建段落（先不关联图片）
            paragraphs = []
            for e in elements:
                if e['type'] == 'paragraph':
                    paragraphs.append(
                        Paragraph(
                            article=article,
                            content=e['text'],
                            order=e['order']
                        )
                    )
            Paragraph.objects.bulk_create(paragraphs)

            # 第二遍处理：建立图文关联
            # 将图片按标识符存入字典
            saved_images = {}
            for img in article.images.all():
                saved_images[img.identifier] = img

            # 遍历段落，寻找图片引用
            for para in Paragraph.objects.filter(article=article):
                # 使用正则表达式匹配 "图X" 格式
                match = re.search(r'图\s*(\d+)', para.content)
                if match:
                    img_num = match.group(1)
                    identifier = f"图{img_num}"
                    # 通过标识符查找对应的图片
                    related_image = saved_images.get(identifier)
                    if related_image:
                        para.image_ref = related_image
                        para.save()

            logger.info(f"成功抓取文章：{article.title}")
            return article

    except Exception as e:
        logger.error(f"保存数据时发生错误: {str(e)}", exc_info=True)
        return None