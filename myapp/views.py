# views.py
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Article, Video, CTPrice, CTAPrice
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from collections import defaultdict
import pydicom
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import time
from django.core.cache import cache
from functools import wraps
from PIL import Image
import numpy as np
import io
from myapp.src.home.ubuntu.js.test_image import generate_image


# 基类视图
class BaseListView(ListView):
    paginate_by = 10
    template_name = None
    context_object_name = 'items'

    def get_queryset(self):
        return self.model.objects.all().order_by('-created_at')


# 文章相关视图
class ArticleListView(BaseListView):
    model = Article
    template_name = 'article_list.html'


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'article_detail.html'
    queryset = Article.objects.prefetch_related('paragraphs', 'images')


# 视频相关视图
class VideoListView(BaseListView):
    model = Video
    template_name = 'video_list.html'
    ordering = '-published_at'


class VideoDetailView(DetailView):
    model = Video
    template_name = 'video_detail.html'

# 速率限制装饰器
def rate_limit(limit=10, per=60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            client_ip = request.META.get('REMOTE_ADDR')
            cache_key = f'rate_limit_{client_ip}'
            requests_list = [t for t in cache.get(cache_key, []) if time.time() - t < per]

            if len(requests_list) >= limit:
                return JsonResponse({'error': '请求过于频繁，请稍后再试'}, status=429)

            requests_list.append(time.time())
            cache.set(cache_key, requests_list, per)
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
# 图像处理类
class ImageProcessor:
    @staticmethod
    def process_image(file):
        pil_image = Image.open(file).convert('L')
        image_np = np.array(pil_image)
        processed_image = generate_image(image_np)
        return Image.fromarray((processed_image.squeeze() * 127.5 + 127.5).astype(np.uint8))

    @staticmethod
    def image_to_response(image):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return HttpResponse(buffer.getvalue(), content_type="image/png")


@method_decorator(csrf_exempt, name='dispatch')
class ImageProcessingView(View):
    def post(self, request):
        if 'imageUpload' not in request.FILES:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        try:
            processed_image = ImageProcessor.process_image(request.FILES['imageUpload'])
            return ImageProcessor.image_to_response(processed_image)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# DICOM处理类
class DicomProcessor:
    @staticmethod
    def handle_upload(file):
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))
        filename = fs.save(f"upload_{uuid.uuid4().hex}.dcm", file)
        return fs.path(filename)

    @staticmethod
    def process_file(dcm_path, threshold):
        try:
            dcm = pydicom.dcmread(dcm_path)
            ct_values = dcm.pixel_array * getattr(dcm, 'RescaleSlope', 1) + getattr(dcm, 'RescaleIntercept', 0)
            bin_img = np.where(ct_values > threshold, 255, 0).astype(np.uint8)

            output_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"result_{uuid.uuid4().hex}.png")

            plt.imsave(output_path, bin_img, cmap='gray')
            plt.close()
            return os.path.join(settings.MEDIA_URL, 'processed', os.path.basename(output_path))
        except Exception as e:
            raise ValueError(f"处理失败: {str(e)}")


class DicomProcessingView(View):
    def get(self, request):
        return render(request, 'dicom_processor.html')

    def post(self, request):
        context = {}
        try:
            dcm_file = request.FILES['dicom_file']
            threshold = int(request.POST.get('threshold', 650))
            input_path = DicomProcessor.handle_upload(dcm_file)
            context['result_url'] = DicomProcessor.process_file(input_path, threshold)
            os.remove(input_path)
        except Exception as e:
            context['error'] = str(e)
        return render(request, 'dicom_processor.html', context)

# 价格分析
class PriceAnalyzer:
    def __init__(self, model, targets):
        self.data = model.objects.all()
        self.targets = targets
        self.stats = defaultdict(lambda: {'total': 0.0, 'count': 0})

    def analyze(self):
        for item in self.data:
            for target in self.targets:
                if target in item.project_name:
                    self.stats[target]['total'] += float(item.price)
                    self.stats[target]['count'] += 1

    @property
    def averages(self):
        return {k: (v['total']/v['count'] if v['count'] else 0)
                for k, v in self.stats.items()}

class ChartGenerator:
    @staticmethod
    def create_pie_chart(data, title, colors):
        fig, ax = plt.subplots(figsize=(12, 8))
        if data:
            labels = list(data.keys())
            sizes = list(data.values())
            ax.pie(sizes,
                   labels=labels,
                   autopct=lambda pct: f'{pct:.1f}%\n{int(pct * sum(sizes) / 100)}元',
                   colors=colors,
                   wedgeprops={'linewidth': 1, 'edgecolor': 'white'})
            ax.set_title(title, fontsize=20)
        return fig

    @staticmethod
    def create_bar_chart(labels, values, colors):
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.bar(labels, values, color=colors)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 10,
                   f'{int(height)}元', ha='center')
        ax.set_ylabel('平均价格（元）', fontsize=16)
        return fig

class PriceAnalysisView(TemplateView):
    template_name = 'prices.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plt.rcParams.update({
            'font.sans-serif': ['SimHei'],
            'axes.unicode_minus': False,
            'font.size': 14
        })

        # CT分析
        ct_analyzer = PriceAnalyzer(CTPrice, ['CT平扫', '螺旋CT平扫', 'CT增强', '螺旋CT增强'])
        ct_analyzer.analyze()
        ct_chart = ChartGenerator.create_pie_chart(
            ct_analyzer.averages,
            'CT 检查项目平均价格分布',
            ['#ff9999', '#ffb399', '#ffcc99', '#ffffb3']
        )

        # CTA分析
        cta_analyzer = PriceAnalyzer(CTAPrice, ['胸腹主动脉', '冠脉CTA的无创FFR分析', '头颈CTA', '腹主动脉CTA'])
        cta_analyzer.analyze()
        cta_chart = ChartGenerator.create_pie_chart(
            cta_analyzer.averages,
            'CTA 检查项目平均价格分布',
            ['#ff9999', '#ffb399', '#ffcc99', '#ffffb3']
        )

        # 价格对比
        ct_avg = (sum(ct_analyzer.averages.values()) / len(ct_analyzer.averages)) if ct_analyzer.averages else 0
        cta_avg = (sum(cta_analyzer.averages.values()) / len(cta_analyzer.averages)) if cta_analyzer.averages else 0
        comparison_chart = ChartGenerator.create_bar_chart(
            ['CT', 'CTA'],
            [ct_avg, cta_avg],
            ['#ff9999', '#ffb399']
        )

        context.update({
            'graphic_ct': self.figure_to_base64(ct_chart),
            'graphic_cta': self.figure_to_base64(cta_chart),
            'graphic_comparison': self.figure_to_base64(comparison_chart),
            'ct_avg_price': int(ct_avg),
            'cta_avg_price': int(cta_avg)
        })
        return context

    @staticmethod
    def figure_to_base64(fig):
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

# AI聊天处理类
class AIChatHandler:
    API_URL = "https://api.deepseek.com/chat/completions"
    API_KEY = "sk-14b890eb5c9841db9f0bf4c2794f455e"

    @classmethod
    @method_decorator(csrf_exempt)
    @method_decorator(rate_limit(10, 60))
    def handle_request(cls, request):
        if request.method != 'POST':
            return JsonResponse({'error': '无效的请求方法'}, status=405)

        message = request.POST.get('message', '').strip()
        if not message:
            return JsonResponse({'error': '消息不能为空'}, status=400)

        try:
            response = requests.post(
                cls.API_URL,
                headers={"Authorization": f"Bearer {cls.API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{
                        "role": "user",
                        "content": message
                    }],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            response.raise_for_status()
            return JsonResponse({
                'response': response.json()['choices'][0]['message']['content']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# 静态页面视图
class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_articles': Article.objects.order_by('-created_at')[:4],
            'latest_video': Video.objects.order_by('-published_at')[:4]
        })
        return context


class FirstView(TemplateView):
    template_name = 'first.html'


class SYSMView(TemplateView):
    template_name = 'sysm.html'


class ChatView(TemplateView):
    template_name = 'chat.html'