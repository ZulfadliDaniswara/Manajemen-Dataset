from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path("otp/", views.otp_number, name="otp_number"),
    path("new_password/", views.new_password, name="new_password"),
    path("homepage/", views.homepage, name="homepage"),
    path('logout/', views.logout_view, name='logout'),
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
    path('inbox/', views.inbox_view, name='inbox'),
    path('inbox/<int:message_id>/view/', views.view_message, name='view_message'),
    path('inbox/<int:message_id>/reply/', views.reply_message, name='reply_message'),
    path('api/receive-message/', views.receive_message_api, name='receive_message_api'),
    path('dataset/<int:dataset_id>/print/', views.print_dataset_pdf, name='print_dataset_pdf'),
]
