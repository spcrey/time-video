import uuid
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, Http404 
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

import os
import multiprocessing

from .forms import UploadVideoForm
from .models import DoubleVideo

# Create your views here.

# main page, http://localhost:8000/videos
def index(request):
    return HttpResponse('Hello World, You\'re at the videos index.')

# videos playing page, http://localhost:8000/videos/playing
def playing(request):
    return render(request, 'videos/playing.html')

# super resolution videos history page, http://localhost:8000/videos/history
def history(request):
    latest_double_video_list = DoubleVideo.objects.order_by('-upload_time')
    user_double_video_list = []
    user_id = request.user.id
    for video in latest_double_video_list:
        if video.user_id == user_id:
            user_double_video_list.append(video)

    context = {
        'user_double_video_list': user_double_video_list,
    }
    return render(request, 'videos/history.html', context)

# super resolution videos collection page, http://localhost:8000/videos/collection
def collection(request):
    latest_double_video_list = DoubleVideo.objects.order_by('-upload_time')
    user_double_video_list = []
    user_id = request.user.id
    for video in latest_double_video_list:
        if video.user_id == user_id and video.is_collection:
            user_double_video_list.append(video)

    context = {
        'user_double_video_list': user_double_video_list,
    }
    return render(request, 'videos/collection.html', context)

multiprocessing_num = multiprocessing.Value('d', 0)
tem_hr_video_path = ''

def detail(request, video_id):
    print(video_id)
    try:
        file_model = DoubleVideo.objects.get(pk=video_id)
    except DoubleVideo.DoesNotExist:
        raise Http404('video does not exist')
    global tem_hr_video_path
    tem_hr_video_path = file_model.hr_video_path
    return render(request, 'videos/playing.html') 

# video upload handling
def upload_handling(file_model):
    input_dir = file_model.lr_video_path
    output_dir = file_model.hr_video_path
    instruction = f'python RealBasicVSR-master/inference_realbasicvsr.py --input_dir={input_dir} --output_dir={output_dir} > /dev/null 2>&1'
    print('model start')
    os.system(instruction)
    print('model end')
    global tem_hr_video_path
    tem_hr_video_path = file_model.hr_video_path
    multiprocessing_num.value = 1
    
def download(request):  
    file = open(tem_hr_video_path, 'rb')
    response = FileResponse(file, content_type='vedeo/mp4')  
    return response 

# video upload process, http://localhost:8000/videos/upload_process
def upload_process(request):
    if  multiprocessing_num.value == 0:
        return render(request, 'videos/upload_process.html', {
            'status': 'incomplete',
        })
    else:
        return render(request, 'videos/upload_process.html', {
            'status': 'complete',
        })

# video upload page, http://localhost:8000/videos/upload
def upload(request):

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse('Please log in first')

        form = UploadVideoForm(request.POST, request.FILES)

        if form.is_valid():
            files = request.FILES.getlist('file')
            file = files[0]
            file_model = DoubleVideo()
            shotname, extension = os.path.splitext(file.name)
            file_model.name = shotname
            file_model.lr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
            file_model.upload_time = timezone.now()
            file_model.user_id = request.user.id
            file_model.hr_video_path = os.path.join('video_files', f'{uuid.uuid4()}{extension}')
            file_model.save()
            destination = open(file_model.lr_video_path, 'wb+')
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()

            # create video upload process, new multiprocessing
            multiprocessing_num.value = 0
            multiprocess = multiprocessing.Process(target=upload_handling, args=(file_model, ))
            multiprocess.start()

            return HttpResponseRedirect(reverse('videos:upload_process'))

        else:
            return render(request, 'videos/upload_failure.html')
    
    else:
        form = UploadVideoForm()
        return render(request, 'videos/upload.html', locals())

# user login page, http://localhost:8000/videos/user_login
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return render(request, 'videos/user_login_succeed.html')
        else:
            return render(request, 'videos/user_login_failure.html')

    return render(request, 'videos/user_login.html') 