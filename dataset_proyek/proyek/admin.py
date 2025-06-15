# di dalam file admin.py
from django.contrib import admin
from .models import Dataset, DownloadLog # Impor DownloadLog

admin.site.register(Dataset)
admin.site.register(DownloadLog) # Daftarkan model ini