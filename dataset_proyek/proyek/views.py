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

from .models import Dataset, ExternalMessage
from .forms import RegisterForm
from io import BytesIO

import tempfile
import os
import json
import requests
from datetime import datetime

# Contoh token dari kelompok pengirim (bisa disimpan di settings/env)
AUTHORIZED_API_TOKEN = '123456789abcdef'  # Ganti dengan token asli, atau ambil dari settings

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

def all_datasets(request):
    datasets = [
        {'nama': 'Racer Car', 'gambar': 'gambar/ferrari.jpg'},
        {'nama': 'Football League', 'gambar': 'gambar/rashford.jpeg'},
        {'nama': 'Super Hero', 'gambar': 'gambar/dataset3.jpg'},
    ]
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

        # Jangan simpan file di session

        return redirect('create_dataset2')

    return render(request, 'create_dataset.html')



def create_dataset2(request):
    if request.method == 'POST':
        request.session['creator_name'] = request.POST.get('creator_name')
        request.session['verifier_name'] = request.POST.get('verifier_name')

        return redirect('create_dataset3')  # Redirect ke halaman terakhir

    return render(request, 'create_dataset2.html')

from django.contrib.auth.decorators import login_required

@login_required
def create_dataset3(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        dataset_file = request.FILES.get('dataset_file')
        num_rows = request.POST.get('num_rows')
        num_features = request.POST.get('num_features')
        keywords = request.POST.get('keywords')

        name = request.session.get('name')
        description = request.session.get('description')
        category = request.session.get('category')
        format_type = request.session.get('format')
        creator = request.session.get('creator_name')
        verifier = request.session.get('verifier_name')

        if not all([name, description, category, format_type, creator, verifier, image, dataset_file, num_rows, num_features, keywords]):
            return render(request, 'create_dataset3.html', {
                'error': 'Harap isi semua kolom dan upload semua file!'
            })

        # Simpan ke database
        Dataset.objects.create(
            title=name,
            description=description,
            category=category,
            file_format=format_type,
            image=image,
            dataset_file=dataset_file,
            creator_name=creator,
            verifier_name=verifier,
            num_rows=int(num_rows),
            num_features=int(num_features),
            keywords=keywords,
            owner=request.user
        )

        # Jangan gunakan flush(), gunakan pop() untuk hapus hanya yang diperlukan
        for key in ['name', 'description', 'category', 'format', 'creator_name', 'verifier_name']:
            request.session.pop(key, None)

        return redirect('your_dataset')

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

    context = {
        'dataset': dataset,
        'keywords_list': [k.strip() for k in keywords_list],  # bersihkan spasi
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
        dataset.num_rows = request.POST.get('num_rows')
        dataset.num_features = request.POST.get('num_features')
        dataset.keywords = request.POST.get('keywords')
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

@csrf_exempt
def receive_message_api(request):
    if request.method == 'POST':
        # 🔐 Autentikasi token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Unauthorized: Token header missing or invalid.'}, status=401)

        token = auth_header.split(' ')[1]
        if token != AUTHORIZED_API_TOKEN:
            return JsonResponse({'error': 'Unauthorized: Invalid token.'}, status=403)

        try:
            # Check if request contains multipart data (file upload)
            content_type = request.headers.get('Content-Type', '')
            
            if content_type.startswith('multipart/form-data'):
                # Handle multipart form data (with file)
                data = {
                    'project_name': request.POST.get('project_name'),
                    'description': request.POST.get('description'),
                    'target': request.POST.get('target'),
                    'data_type': request.POST.get('data_type'),
                    'aktivitas_pemrosesan': request.POST.get('aktivitas_pemrosesan'),
                    'jumlah_fitur': request.POST.get('jumlah_fitur'),
                    'ukuran_dataset': request.POST.get('ukuran_dataset'),
                    'format_file': request.POST.get('format_file'),
                    'start_date': request.POST.get('start_date'),
                    'end_date': request.POST.get('end_date'),
                    'status': request.POST.get('status'),
                    'sender': request.POST.get('sender', 'unknown')
                }
                
                # Handle uploaded file if present
                uploaded_file = request.FILES.get('file')
                if uploaded_file:
                    # You can process the file here
                    # For example, save it or read its content
                    pass
                    
            else:
                # Handle JSON data (without file)
                data = json.loads(request.body)

            # Validate required fields
            required_fields = ['project_name', 'description', 'target', 'data_type', 
                             'aktivitas_pemrosesan', 'jumlah_fitur', 'ukuran_dataset', 
                             'format_file', 'start_date', 'end_date', 'status']
            
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

            message = ExternalMessage.objects.create(
                project_name=data['project_name'],
                description=data['description'],
                target=data['target'],
                data_type=data['data_type'],
                aktivitas_pemrosesan=data['aktivitas_pemrosesan'],
                jumlah_fitur=int(data['jumlah_fitur']),
                ukuran_dataset=data['ukuran_dataset'],
                format_file=data['format_file'],
                start_date=datetime.strptime(data['start_date'], "%Y-%m-%d").date(),
                end_date=datetime.strptime(data['end_date'], "%Y-%m-%d").date(),
                status=data['status'],
                sender=data.get('sender', 'unknown')
            )

            return JsonResponse({'message': 'Pesan berhasil diterima.'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def reply_message(request, message_id):
    message = get_object_or_404(ExternalMessage, id=message_id)

    if request.method == 'POST':
        # Ambil data dari form
        data = {
            'project_name': request.POST.get('project_name'),
            'description': request.POST.get('description'),
            'target': request.POST.get('target'),
            'data_type': request.POST.get('type_data'),
            'aktivitas_pemrosesan': request.POST.get('processing'),
            'jumlah_fitur': request.POST.get('num_features'),
            'ukuran_dataset': request.POST.get('dataset_size'),
            'format_file': request.POST.get('format_file'),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
            'status': 'pending',
            'sender': 'web-kamu'  # Optional
        }

        file = request.FILES.get('file')  # Bisa juga None

        token = getattr(settings, 'TARGET_API_TOKEN', 'dummy_token')
        headers = {
            'Authorization': f'Token {token}'
        }

        try:
            if file:
                # Kirim sebagai multipart form jika ada file
                multipart_data = data.copy()
                files = {'file': (file.name, file.read(), file.content_type)}

                response = requests.post(
                    url='https://data.factiven.me/api/receive-message/',
                    data=multipart_data,
                    files=files,
                    headers=headers,
                    timeout=10
                )
            else:
                # Kirim sebagai JSON jika tanpa file
                headers['Content-Type'] = 'application/json'
                response = requests.post(
                    url='https://data.factiven.me/api/receive-message/',
                    data=json.dumps(data),
                    headers=headers,
                    timeout=10
                )

            if response.status_code == 201:
                return redirect('inbox')  # Ganti sesuai URL-mu
            else:
                return render(request, 'reply_message.html', {
                    'message': message,
                    'form_errors': f'Gagal mengirim. Status: {response.status_code}, Respon: {response.text}'
                })

        except requests.exceptions.RequestException as e:
            return render(request, 'reply_message.html', {
                'message': message,
                'form_errors': f'Koneksi gagal: {str(e)}'
            })

    return render(request, 'reply_message.html', {'message': message})