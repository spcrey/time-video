import json
import os
import multiprocessing
from functools import wraps
import uuid

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, FileResponse, Http404 
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .forms import VideoUploadForm
from .models import DoubleVideo

# Create your views here.

with open(os.path.join('videos', 'image_paths.json')) as file:
    image_paths = json.load(file)['image_paths']

def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('videos:user_login'))
        return view_func(request, *args, **kwargs)
    return wrapper

# url: http://localhost:8000/videos/
def index(request):
    return HttpResponseRedirect(reverse('videos:upload'))

# url: http://localhost:8000/videos/template/
def template(request):
    username = request.user.username.upper() if request.user.is_authenticated else None
    return render(request, 'videos/base.html', {'username': username})

def create_double_video_by_uploading_file(request, uploading_file):
    image_id = len(DoubleVideo.objects.filter(create_user_id=request.user.id).order_by('-upload_time')) % len(image_paths)
    double_video = DoubleVideo()
    shotname, extension = os.path.splitext(uploading_file.name)
    double_video.name = shotname
    double_video.upload_time = timezone.now()
    double_video.create_user_id = request.user.id
    double_video.lr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
    double_video.hr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
    double_video.image_path = image_paths[image_id]
    double_video.save()
    return double_video

@custom_login_required
def upload_post(request):
    latest_double_video = DoubleVideo.objects.order_by('-upload_time').filter(create_user_id=request.user.id).first()
    if latest_double_video and not latest_double_video.is_complete:
        return render(request, 'videos/upload_failure.html')

    form = VideoUploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploading_file = request.FILES.getlist('file')[0]
        double_video = create_double_video_by_uploading_file(request, uploading_file)
        os.makedirs('video_files', exist_ok=True)
        destination = open(double_video.lr_video_path, 'wb+')
        for chunk in uploading_file.chunks():
            destination.write(chunk)
        destination.close()
        # create video upload process, new multiprocessing
        multiprocess = multiprocessing.Process(target=video_handling, args=(double_video, ))
        multiprocess.start()
        return HttpResponseRedirect(reverse('videos:process'))
    else:
        return render(request, 'videos/upload_failure.html')

# url: http://localhost:8000/videos/upload/
def upload(request):
    if request.method == 'POST':
        return upload_post(request)
    else:
        form = VideoUploadForm()
        username = request.user.username.upper() if request.user.is_authenticated else None
        return render(request, 'videos/upload.html', {'form': form, 'username': username})
    
# video upload handling
def video_handling(dv_file_model):
    input_dir = dv_file_model.lr_video_path
    output_dir = dv_file_model.hr_video_path
    instruction = f'python RealBasicVSR-master/inference_realbasicvsr.py --input_dir={input_dir} --output_dir={output_dir} > /dev/null 2>&1'
    os.system(instruction)
    dv_file_model.is_complete = True
    dv_file_model.save()

# url: http://localhost:8000/videos/collection/
@custom_login_required
def collection(request):
    double_video_list = DoubleVideo.objects.filter(create_user_id=request.user.id, is_complete=True, is_collection=True).order_by('-upload_time')
    username = request.user.username.upper()
    context = {
        'double_video_list': double_video_list,
        'username': username
    }
    return render(request, 'videos/collection.html', context)

def set_collection(video_id, is_collection):
    file_model = DoubleVideo.objects.get(pk=video_id)
    file_model.is_collection = is_collection
    file_model.save()
    return HttpResponseRedirect(reverse('videos:detail', kwargs={'video_id': video_id}))

# url: http://localhost:8000/videos/add_collection/
@custom_login_required
def add_collection(request, video_id):
    return set_collection(video_id, True)

# url: http://localhost:8000/videos/del_collection/
@custom_login_required
def del_collection(request, video_id):
    return set_collection(video_id, False)

# url: http://localhost:8000/videos/history/
@custom_login_required
def history(request):
    double_video_list = DoubleVideo.objects.filter(create_user_id=request.user.id, is_complete=True).order_by('-upload_time')
    username = request.user.username.upper()
    context = {
        'double_video_list': double_video_list,
        'username': username,
    }
    return render(request, 'videos/history.html', context)

# url: http://localhost:8000/videos/process/
@custom_login_required
def process(request):
    latest_double_video = DoubleVideo.objects.filter(create_user_id=request.user.id).order_by('-upload_time').first()
    username = request.user.username.upper()
    if latest_double_video:
        print(latest_double_video)
        if latest_double_video.is_complete:
            return render(request, 'videos/process.html', {
                'status': 'complete', 'username': username, 'lastest_double_video_id': latest_double_video.pk,
            })
        else:
            return render(request, 'videos/process.html', {
                'status': 'incomplete', 'username': username,
            })
    else:
        return render(request, 'videos/process.html', {
            'status': 'no_video', 'username': username,
        })

@custom_login_required
# url: http://localhost:8000/videos/detail/
def detail(request, video_id):
    try:
        double_video = DoubleVideo.objects.get(pk=video_id)
        if not request.user.id == double_video.create_user_id:
            raise Http404('not your video')
    except DoubleVideo.DoesNotExist:
        raise Http404('video does not exist')
    return render(request, 'videos/detail.html', context={
        'video_id': video_id, 'video_name': double_video.name, 'is_collection': double_video.is_collection
    }) 

# url: http://localhost:8000/videos/download/
@custom_login_required    
def download(request, video_id):
    try:
        double_video = DoubleVideo.objects.get(pk=video_id)
        if not request.user.id == double_video.create_user_id:
            raise Http404('not your video')
        double_video = DoubleVideo.objects.get(id=video_id)
        file = open(double_video.hr_video_path, 'rb')
        response = FileResponse(file, content_type='video2/mp4')  
        return response 
    except DoubleVideo.DoesNotExist:
        raise Http404('video does not exist')

# url: http://localhost:8000/videos/user_login/
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('videos:upload'))
        else:
            return render(request, 'videos/user_login_failure.html')
    else:
        return render(request, 'videos/user_login.html') 

# url: http://localhost:8000/videos/user_login/
@custom_login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('videos:upload'))
