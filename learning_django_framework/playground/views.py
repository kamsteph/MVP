from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def say_hello_world(request):
    return render(request,'hello.html')