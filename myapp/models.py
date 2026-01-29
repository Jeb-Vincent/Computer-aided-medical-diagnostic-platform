from django.utils import timezone

from django.db import models

class Article(models.Model):
    title = models.CharField("标题", max_length=200)
    source_url = models.URLField("来源网址")
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Paragraph(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='paragraphs')
    content = models.TextField("内容")
    image_ref = models.ForeignKey('Image',
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                related_name='paragraph_ref')
    order = models.PositiveIntegerField("顺序", default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.article.title} - 段落{self.order}"

class Image(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    url = models.URLField("图片地址", max_length=500)
    identifier = models.CharField("图片标识", max_length=20, db_index=True)
    order = models.PositiveIntegerField("顺序", default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.article.title} - {self.identifier}"

class Video(models.Model):
    title = models.CharField("视频标题", max_length=255)
    video_url = models.URLField("视频地址", max_length=500)
    published_at = models.DateTimeField("发布时间",default=timezone.now)
    source_name = models.CharField("来源机构", max_length=255, default="中华医学会科学普及部")
    created_at = models.DateTimeField("抓取时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:20]

class CTAPrice(models.Model):
    project_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

    class Meta:
        db_table = 'cta_prices'  # 指定表名


class CTPrice(models.Model):
    project_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

    class Meta:
        db_table = 'ct_prices'  # 指定表名
