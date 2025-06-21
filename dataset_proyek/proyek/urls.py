# nama_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Pastikan views diimport seperti ini

# Setup Router untuk membuat semua URL API secara otomatis
router = DefaultRouter()
router.register(r'messages', views.MessageViewSet, basename='message')

# Daftar semua "alamat" atau URL di aplikasi Anda
urlpatterns = [
    # A. URL UNTUK API (Untuk diakses program/teman Anda)
    path('api/v1/', include(router.urls)),

    # B. URL UNTUK HALAMAN WEB
    path('', views.landing_page, name='landing'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path("otp/", views.otp_number, name="otp_number"),
    path("new_password/", views.new_password, name="new_password"),
    path("homepage/", views.homepage, name="homepage"),
    path('logout/', views.logout_view, name='logout'),

    # URL Dataset
    path('datasets/', views.all_datasets, name='all_datasets'),
    path('lastview/', views.lastview_dataset, name='lastview_dataset'),
    path('create_dataset/', views.create_dataset, name='create_dataset'),
    path('create_dataset2/', views.create_dataset2, name='create_dataset2'),
    path('create_dataset3/', views.create_dataset3, name='create_dataset3'),
    path('your-dataset/', views.your_dataset, name='your_dataset'),
    path('dataset/<int:id>/', views.view_dataset, name='view_dataset'),
    path('dataset/<int:id>/edit/', views.edit_dataset, name='edit_dataset'),
    path('dataset/<int:id>/delete/', views.delete_dataset, name='delete_dataset'),
    path('download/<int:dataset_id>/', views.download_dataset, name='download_dataset'),
    path('dataset/<int:dataset_id>/print/', views.print_dataset_pdf, name='print_dataset_pdf'),
    path('search/', views.search_results_view, name='search_results'),
    path('statistik/', views.dataset_statistics_view, name='dataset_stats'),
    path('dataset/<int:dataset_id>/aktivitas/', views.dataset_activity_view, name='dataset_activity'),

    # URL untuk Fungsionalitas Pesan
    path('inbox/', views.inbox_page, name='inbox'),
    path('message/<int:message_id>/', views.view_message_page, name='view_message'),
    path('reply/<int:pk>/', views.reply_message_page, name='reply_message'),
    path('api/dataset-reply/', views.get_latest_reply, name='api-dataset-reply'),
]