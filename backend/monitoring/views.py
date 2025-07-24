from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

def dashboard(request):
    return render(request, 'dashboard.html')

def monitoring(request):
    return render(request, 'dashboard.html')

def detection(request):
    return render(request, 'dashboard.html')

def statistics(request):
    return render(request, 'dashboard.html')

def settings(request):
    return render(request, 'dashboard.html')
