from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.templatetags.static import static
from xhtml2pdf import pisa
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, status, views
from django.db.models import F
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay

from .models import Dataset, ExternalMessage
from .forms import RegisterForm
from io import BytesIO
from .models import ExternalMessage
from .serializers import MessageSerializer
from datetime import datetime
from django.db.models import Q
from .models import Dataset, DownloadLog 
from xhtml2pdf import pisa

import pandas as pd 
import tempfile
import os
import json
import requests

def landing_page(request):
    return render(request, 'landingpage.html')

#====================landing page ====================

def signup_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
        else: 
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Silakan isi email terlebih dahulu.")
        else:
            return redirect("otp_page")
    return render(request, "forgot_password")

def otp_number(request):
    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        if not otp:
            messages.error(request, "Silakan isi OTP terlebih dahulu.")
        else:
            return redirect("new_password")
    return render(request, "otp_number.html")

def new_password(request):
    if request.method == "POST":
        new_pass = request.POST.get("new_password", "").strip()

        if not new_pass:
            messages.error(request, "Password baru tidak boleh kosong.")
            return redirect("new_password")

        user = User.objects.first()  # Dummy user pertama
        if user:
            user.set_password(new_pass)
            user.save()
            messages.success(request, "Password berhasil diubah. Silakan login.")
            return redirect("login")
        else:
            messages.error(request, "User tidak ditemukan.")
            return redirect("login")

    return render(request, "new_password.html")

#====================login page ====================

def homepage(request):
    return render(request, "homepage.html")

def logout_view(request):
    auth_logout(request)
    return redirect('landing')

@login_required
def all_datasets(request):
    datasets = Dataset.objects.filter(is_public=True).order_by('-created_at')
    return render(request, 'all_dataset.html', {'datasets': datasets})

def lastview_dataset(request):
    last_viewed = [
        {'nama': 'Spider Hero', 'gambar': 'gambar/dataset4.jpg'},
        {'nama': 'Space Data', 'gambar': 'gambar/dataset2.jpg'},
    ]
    return render(request, 'lastview_dataset.html', {'datasets': last_viewed})

def create_dataset(request):
    if request.method == 'POST':
        request.session['name'] = request.POST.get('name')  
        request.session['description'] = request.POST.get('description')
        request.session['category'] = request.POST.get('category')
        request.session['format'] = request.POST.get('format')
        return redirect('create_dataset2')
    return render(request, 'create_dataset.html')

# Halaman 2 – Tambahan metadata pembuat dan verifikator
def create_dataset2(request):
    if request.method == 'POST':
        request.session['creator_name'] = request.POST.get('creator_name')
        request.session['verifier_name'] = request.POST.get('verifier_name')

        return redirect('create_dataset3')

    return render(request, 'create_dataset2.html')

# Halaman 3 – Upload file, gambar, checkbox publikasi, simpan ke DB
@login_required
def create_dataset3(request):
    if request.method == 'POST':
        dataset_file = request.FILES.get('dataset_file')
        
        # Ambil data lain dari form
        image = request.FILES.get('image')
        is_public = request.POST.get('is_public') == 'on'
        
        num_rows = 0
        num_features = 0
        keywords = "" # Default value jika file tidak ada atau bukan CSV

        if dataset_file:
            # Validasi sederhana, pastikan file adalah .csv
            if not dataset_file.name.endswith('.csv'):
                messages.error(request, 'File harus berformat .csv')
                return render(request, 'create_dataset3.html')
            
            try:
                # Baca file csv menggunakan pandas
                df = pd.read_csv(dataset_file)
                
                # UBAH: Ambil jumlah baris dan fitur dari file
                num_rows = df.shape[0]
                num_features = df.shape[1]
                
                # UBAH: Ambil nama kolom/fitur dan gabungkan menjadi string
                # Ini akan disimpan di field 'keywords'
                keywords = ', '.join(df.columns)
                
            except Exception as e:
                messages.error(request, f"Gagal memproses file CSV: {e}")
                return render(request, 'create_dataset3.html')
        else:
            messages.error(request, 'Anda belum mengunggah file dataset.')
            return render(request, 'create_dataset3.html')
        # --- AKHIR DARI LOGIKA BARU ---

        # Ambil semua data dari session
        title = request.session.get('name')
        description = request.session.get('description')
        category = request.session.get('category')
        file_format = request.session.get('format')
        creator_name = request.session.get('creator_name')
        verifier_name = request.session.get('verifier_name')
        owner = request.user

        # Validasi session (kode Anda sebelumnya, sudah bagus)
        required_keys = ['name', 'description', 'category', 'format', 'creator_name', 'verifier_name']
        missing = [k for k in required_keys if k not in request.session]
        if missing:
            messages.error(request, f"Data berikut hilang dari session: {', '.join(missing)}")
            return redirect('create_dataset')

        dataset = Dataset.objects.create(
            title=title,
            description=description,
            category=category,
            file_format=file_format,
            image=image,
            dataset_file=dataset_file,
            creator_name=creator_name,
            verifier_name=verifier_name,
            owner=owner,
            is_public=is_public,
            
            # UBAH: Gunakan variabel yang sudah diisi otomatis
            num_rows=num_rows,
            num_features=num_features,
            keywords=keywords
        )

        messages.success(request, "Dataset berhasil dibuat!")
        # Hapus session setelah berhasil disimpan agar tidak terpakai lagi
        for key in required_keys:
            if key in request.session:
                del request.session[key]
                
        return redirect('your_dataset') # Ganti 'your_dataset' dengan nama URL tujuan Anda

    return render(request, 'create_dataset3.html')
#@login_required
@login_required(login_url='/login/') 
def your_dataset(request):
    datasets = Dataset.objects.filter(owner=request.user)
    return render(request, 'your_dataset.html', {
        'datasets': datasets
    })

#@login_required

def view_dataset(request, id):
    dataset = get_object_or_404(Dataset, pk=id)
    keywords_list = dataset.keywords.split(",") if dataset.keywords else []

    dataset.click_count = F('click_count') + 1
    dataset.save()
    dataset.refresh_from_db()

    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    download_activity = (DownloadLog.objects
                         .filter(dataset=dataset, timestamp__range=[start_date, end_date])
                         .annotate(day=TruncDay('timestamp'))
                         .values('day')
                         .annotate(count=Count('id'))
                         .order_by('day'))
    print("--- DEBUGGING: DATA MENTAH DARI DATABASE ---")
    print(list(download_activity))

    date_map = { (start_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(31) }
    
    for activity in download_activity:
        day_str = activity['day'].strftime('%Y-%m-%d')
        if day_str in date_map:
            date_map[day_str] = activity['count']
            
    activity_labels = list(date_map.keys())
    activity_data = list(date_map.values())

    print("\n--- DEBUGGING: DATA FINAL UNTUK GRAFIK ---")
    print("Labels:", activity_labels)
    print("Data:", activity_data)
    print("------------------------------------------")

    context = {
        'dataset': dataset,
        'keywords_list': [k.strip() for k in keywords_list],
        'activity_labels': json.dumps([d[5:] for d in activity_labels]),
        'activity_data': json.dumps(activity_data)
    }
    
    return render(request, 'view_dataset.html', context)

@login_required
def edit_dataset(request, id):
    dataset = get_object_or_404(Dataset, id=id, owner=request.user)

    if request.method == 'POST':
        dataset.title = request.POST.get('title')
        dataset.description = request.POST.get('description')
        dataset.category = request.POST.get('category')
        dataset.file_format = request.POST.get('file_format')
        dataset.creator_name = request.POST.get('creator_name')
        dataset.verifier_name = request.POST.get('verifier_name')
        if request.FILES.get('image'):
            dataset.image = request.FILES.get('image')
        dataset.save()
        return redirect('your_dataset')

    return render(request, 'edit_dataset.html', {'dataset': dataset})

#@login_required
def delete_dataset(request, id):
    dataset = get_object_or_404(Dataset, id=id, owner=request.user)
    dataset.delete()
    return redirect('your_dataset')

def download_dataset(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)

    dataset.download_count = F('download_count') + 1
    dataset.save()

    DownloadLog.objects.create(dataset=dataset)

    if not dataset.dataset_file:
        raise Http404("File tidak ditemukan.")

    file_path = dataset.dataset_file.path

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    else:
        raise Http404("File tidak ditemukan.")

def print_dataset_pdf(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    keywords_list = dataset.keywords.split(",") if dataset.keywords else []

    # Render template ke HTML string
    html_string = render_to_string("dataset_template_pdf.html", {
        'dataset': dataset,
        'keywords_list': keywords_list
    })

    # Siapkan response HTTP untuk PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{dataset.title}.pdf"'

    # Konversi HTML ke PDF
    result = BytesIO()
    pdf = pisa.CreatePDF(src=html_string, dest=result)

    if not pdf.err:
        response.write(result.getvalue())
        return response
    else:
        return HttpResponse("Gagal generate PDF", status=500)

def inbox_view(request):
    messages = ExternalMessage.objects.all().order_by('-timestamp')
    return render(request, 'inbox.html', {'messages': messages})

def view_message(request, message_id):
    message = get_object_or_404(ExternalMessage, id=message_id)
    return render(request, 'view_message.html', {'message': message})

def search_results_view(request):
    
    # Langkah 1: Ambil kata kunci pencarian dari URL (parameter ?q=...)
    query = request.GET.get('q', '')
    
    results = []
    
    # Langkah 2: Hanya lakukan pencarian jika ada kata kunci yang dimasukkan
    if query:
        results = Dataset.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(keywords__icontains=query)
        ).distinct() # distinct() untuk memastikan tidak ada hasil yang sama ditampilkan berulang
    
    # Langkah 4: Siapkan data (context) untuk dikirim ke template
    context = {
        'query': query,     
        'results': results,  
    }
    
    # Langkah 5: Render template untuk menampilkan halaman hasil pencarian
    return render(request, 'search_results.html', context)

def dataset_statistics_view(request):
    top_datasets = Dataset.objects.order_by('-click_count')[:10]
    
    labels = []
    click_data = []
    download_data = []

    for dataset in top_datasets:
        labels.append(dataset.title)
        click_data.append(dataset.click_count)
        download_data.append(dataset.download_count)
        
    context = {
        'labels': json.dumps(labels),
        'click_data': json.dumps(click_data),
        'download_data': json.dumps(download_data),
    }
    
    return render(request, 'view_dataset.html', context)

def dataset_activity_view(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # 1. Tentukan rentang waktu (30 hari terakhir)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # 2. Lakukan query agregasi ke database
    # Ambil log download, kelompokkan per hari (TruncDay), dan hitung jumlahnya (Count)
    download_activity = (DownloadLog.objects
                         .filter(dataset=dataset, timestamp__range=[start_date, end_date])
                         .annotate(day=TruncDay('timestamp'))
                         .values('day')
                         .annotate(count=Count('id'))
                         .order_by('day'))
    
    # 3. Siapkan data untuk Chart.js
    # Buat dictionary tanggal dari 30 hari terakhir dengan nilai awal 0
    date_map = { (start_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(31) }
    
    # Isi dictionary dengan data dari database
    for activity in download_activity:
        day_str = activity['day'].strftime('%Y-%m-%d')
        if day_str in date_map:
            date_map[day_str] = activity['count']
            
    # Ubah dictionary menjadi dua list untuk label dan data grafik
    labels = list(date_map.keys())
    data = list(date_map.values())

    context = {
        'dataset': dataset,
        'labels': json.dumps([d[5:] for d in labels]), # Hanya ambil format 'MM-DD'
        'data': json.dumps(data)
    }
    return render(request, 'nama_app/dataset_activity.html', context)

def sent_items_view(request):
    # Ambil semua objek balasan yang pernah dikirim, urutkan dari yang terbaru
    sent_replies = SentReply.objects.all().order_by('-sent_at')
    
    context = {
        'sent_replies': sent_replies
    }
    return render(request, 'sent_items.html', context)

class ReceiveMessageView(generics.CreateAPIView):

    queryset = ExternalMessage.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_data = {
            "status": "success",
            "message": "Pesan berhasil diterima.",
            "data": serializer.data
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
class ReceiveMessageView(generics.CreateAPIView):
    queryset = ExternalMessage.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_data = {
            "status": "success",
            "message": "Pesan berhasil diterima dan disimpan.",
            "data": serializer.data
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

def reply_message_page(request, pk):
    try:
        message_to_reply = ExternalMessage.objects.get(pk=pk)
    except ExternalMessage.DoesNotExist:
        return redirect('inbox') 

    default_text = "dataset sudah tersedia silahkan download di web kami"

    if request.method == 'POST':
        # Ambil teks dari textarea di form HTML
        message_text = request.POST.get('message_text', default_text)

        # Siapkan data JSON yang akan dikirim
        reply_data = {
            'reply_to_project': message_to_reply.project_name,
            'message': message_text,
            'original_sender': message_to_reply.sender
        }

        # Kirim data ke API teman Anda
        try:
            teman_api_url = settings.TEMAN_API_URL
            requests.post(url=teman_api_url, json=reply_data, timeout=10).raise_for_status()
            return redirect('inbox')
        except RequestException as e:
            # Jika gagal, kembali ke halaman reply dengan pesan error
            error_message = f"Gagal mengirim balasan: {e}"
            context = {
                'message': message_to_reply,
                'default_message': message_text, # Tampilkan teks yang gagal dikirim
                'error_message': error_message
            }
            return render(request, 'reply_message.html', context)

    context = {
        'message': message_to_reply,
        'default_message': default_text
    }
    return render(request, 'reply_message.html', context)