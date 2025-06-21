# models.py

from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    file_format = models.CharField(max_length=50)

    image = models.ImageField(upload_to='dataset_images/')
    dataset_file = models.FileField(upload_to='dataset_files/', null=True, blank=True)

    creator_name = models.CharField(max_length=100)
    verifier_name = models.CharField(max_length=100)
    num_rows = models.IntegerField()
    num_features = models.IntegerField()
    keywords = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    is_public = models.BooleanField(default=False)

    click_count = models.PositiveIntegerField(default=0, verbose_name="Jumlah Dilihat")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Jumlah Diunduh")

    def __str__(self):
        return self.title

class DownloadLog(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='download_logs')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dataset.title} downloaded at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# nama_app/models.py
from django.db import models

class ExternalMessage(models.Model):
    # === Tambahkan blok ini untuk pilihan status dropdown ===
    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        COMPLETE = 'Complete', 'Complete'
        CANCELLED = 'Cancelled', 'Cancelled'
    # ===================================================

    project_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    target = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255)
    aktivitas_pemrosesan = models.CharField(max_length=255)
    jumlah_fitur = models.IntegerField()
    ukuran_dataset = models.CharField(max_length=100)
    format_file = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # === Pastikan field status Anda seperti ini ===
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    # ==========================================

    sender = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

# Kode Anda untuk ReplyMessage sudah benar
class ReplyMessage(models.Model):
    original_message = models.OneToOneField(
        ExternalMessage,
        on_delete=models.CASCADE,
        related_name='reply'
    )
    message_text = models.TextField()
    dataset_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply for '{self.original_message.project_name}'"