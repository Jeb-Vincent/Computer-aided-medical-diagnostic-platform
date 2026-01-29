from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static
# urlpatterns = [
#
#    path('', views.index, name='home'),
#    path('first/', views.first, name='first'),
#    path('sysm/', views.sysm, name='sysm'),
#    path('process_image/', views.process_image_view, name='process_image'),
#    path('process-dicom/', views.process_dicom, name='dicom_processor'),
#    path('chat/', views.chat_view, name='chat'),
#    path('get_response/', views.get_ai_response, name='get_response'),
#    path('articles/', views.article_list, name='article_list'),
#    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
#    path('videos/', views.video_list, name='video_list'),
#    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
#    path('prices/', views.prices_view, name='prices'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urls.py
from django.urls import path
from myapp.views import (
    IndexView,
    FirstView,
    SYSMView,
    ChatView,
    ArticleListView,
    ArticleDetailView,
    VideoListView,
    VideoDetailView,
    ImageProcessingView,
    DicomProcessingView,
    PriceAnalysisView,
    AIChatHandler
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', IndexView.as_view(), name='home'),
    path('first/', FirstView.as_view(), name='first'),
    path('sysm/', SYSMView.as_view(), name='sysm'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('process_image/', ImageProcessingView.as_view(), name='process_image'),
    path('process-dicom/', DicomProcessingView.as_view(), name='dicom_processor'),
    path('get_response/', AIChatHandler.handle_request, name='get_response'),
    path('articles/', ArticleListView.as_view(), name='article_list'),
    path('article/<int:pk>/', ArticleDetailView.as_view(), name='article_detail'),
    path('videos/', VideoListView.as_view(), name='video_list'),
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='video_detail'),
    path('prices/', PriceAnalysisView.as_view(), name='prices'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)