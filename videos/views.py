import json
import uuid
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, Http404 
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from functools import wraps

import os
import multiprocessing

from .forms import UploadVideoForm
from .models import DoubleVideo

def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('videos:user_login'))
        return view_func(request, *args, **kwargs)
    return wrapper

with open(os.path.join("videos", "img_paths.json")) as file:
    img_paths = json.load(file)["img_paths"]

# Create your views here.

@custom_login_required
def set_collection(request, video_id, is_collection):
    file_model = DoubleVideo.objects.get(pk=video_id)
    file_model.is_collection = is_collection
    file_model.save()
    return HttpResponseRedirect(reverse('videos:detail', kwargs={'video_id': video_id}))

# @login_required
def add_collection(request, video_id):
    return set_collection(request, video_id, True)

def del_collection(request, video_id):
    return set_collection(request, video_id, False)

# url: http://localhost:8000/videos
def index(request):
    return HttpResponseRedirect(reverse('videos:upload'))

# url: http://localhost:8000/videos/playing
@custom_login_required
def playing(request):
    return render(request, 'videos/playing.html')

# url: http://localhost:8000/videos/history
@custom_login_required
def history(request):
    user_double_video_list = DoubleVideo.objects.order_by('-upload_time').filter(user_id=request.user.id)
    username = request.user.username.upper()

    context = {
        'user_double_video_list': user_double_video_list,
        "is_authenticated": True, "username": username,
    }
    return render(request, 'videos/history.html', context)

# url: http://localhost:8000/videos/collection
@custom_login_required
def collection(request):
    collection_user_double_video_list = DoubleVideo.objects.order_by('-upload_time').filter(user_id=request.user.id, is_collection=True)
    username = request.user.username.upper()
    context = {
        'user_double_video_list': collection_user_double_video_list,
        "is_authenticated": True, "username": username
    }
    return render(request, 'videos/collection.html', context)

@custom_login_required
def detail(request, video_id):
    try:
        file_model = DoubleVideo.objects.get(pk=video_id)
        if request.user.is_authenticated:
            user_id = request.user.id
            if not user_id == file_model.user_id:
                raise Http404('not your video')
    except DoubleVideo.DoesNotExist:
        raise Http404('video does not exist')
    return render(request, 'videos/playing.html', context={
        "video_id": video_id, "no_collection": not file_model.is_collection
    }) 

# video upload handling
def upload_handling(request, file_model):
    input_dir = file_model.lr_video_path
    output_dir = file_model.hr_video_path
    instruction = f'python RealBasicVSR-master/inference_realbasicvsr.py --input_dir={input_dir} --output_dir={output_dir} > /dev/null 2>&1'
    os.system(instruction)
    request.user.first_name = "complete"
    request.user.save()
    
def download(request, video_id):
    try:
        file_model = DoubleVideo.objects.get(pk=video_id)
        if request.user.is_authenticated:
            user_id = request.user.id
            if not user_id == file_model.user_id:
                raise Http404('not your video')
    except DoubleVideo.DoesNotExist:
        raise Http404('video does not exist')
    double_video = DoubleVideo.objects.get(id=video_id)
    file = open(double_video.hr_video_path, 'rb')
    response = FileResponse(file, content_type='vedeo/mp4')  
    return response 

# url: http://localhost:8000/videos/upload_process
@custom_login_required
def upload_process(request):
    username = request.user.username.upper()
    if request.user.first_name == "video handling":
        return render(request, 'videos/upload_process.html', {
            'status': 'incomplete', "is_authenticated": True, "username": username
        })
    else:
        file_model = DoubleVideo.objects.filter(user_id=request.user.id).last() 
        return render(request, 'videos/upload_process.html', {
            'status': 'complete', "lastest_id": file_model.pk, 
            "is_authenticated": True, "username": username
        })

@custom_login_required
def upload_post(request):
    if request.user.first_name == "video handling":
        return render(request, 'videos/upload_failure.html')

    form = UploadVideoForm(request.POST, request.FILES)

    if form.is_valid():
        if len(DoubleVideo.objects.filter(user_id=request.user.id)) == 0:
            id = 1
        else:
            id = DoubleVideo.objects.filter(user_id=request.user.id).last().pk + 1
        files = request.FILES.getlist('file')
        file = files[0]
        file_model = DoubleVideo()
        shotname, extension = os.path.splitext(file.name)
        file_model.name = shotname
        file_model.lr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
        file_model.upload_time = timezone.now()
        file_model.user_id = request.user.id
        file_model.hr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
        file_model.img_path = img_paths[int(id%6)]
        file_model.save()
        destination = open(file_model.lr_video_path, 'wb+')
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()

        # create video upload process, new multiprocessing
        multiprocess = multiprocessing.Process(target=upload_handling, args=(request, file_model, ))
        multiprocess.start()
        request.user.first_name = "video handling"
        request.user.save()
        return HttpResponseRedirect(reverse('videos:upload_process'))

    else:
        return render(request, 'videos/upload_failure.html')

# url: http://localhost:8000/videos/upload
def upload(request):
    if request.method == 'POST':
        return upload_post(request)
    else:
        form = UploadVideoForm()
        is_authenticated = request.user.is_authenticated
        username = request.user.username.upper() if is_authenticated else None
        return render(request, 'videos/upload.html', {"form": form, "is_authenticated": request.user.is_authenticated, "username": username})

# url: http://localhost:8000/videos/user_login
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('videos:upload'))
        else:
            return render(request, 'videos/user_login_failure.html')

    return render(request, 'videos/user_login.html') 

# url: http://localhost:8000/videos/user_login
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('videos:upload'))