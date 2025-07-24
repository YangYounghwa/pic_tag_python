from django.shortcuts import render, redirect
from django.http import HttpResponse

def dashboard_page(request):
    return render(request, 'dashboard.html')

# Create your views here.
