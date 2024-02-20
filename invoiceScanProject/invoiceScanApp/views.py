from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import User
# Create your views here.

def home(request):
    if request.method=='POST':
        form = UploadFileForm(request.POST, request.FILES)
        file = request.FILES['file']
        user = User.objects.create(doc=file)
        user.save()
        return HttpResponse("the user with id " + str(user.pk) + " has the file : "+ str(user.doc))
    else:
        form = UploadFileForm();
    return render(request,"home.html", {'form': form} )
