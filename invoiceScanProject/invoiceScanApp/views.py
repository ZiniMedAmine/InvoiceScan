from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import User
from django.core.exceptions import ValidationError

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['file']
                user = User.objects.create(doc=file)
                user.save()
                return HttpResponse("the user with id "+str(user.pk) + "uploaded this image : "+str(user.doc))
            except ValidationError as e:
                form.add_error('file', e)  
        else:
            pass
    else:
        form = UploadFileForm()
    return render(request, "home.html", {'form': form})
