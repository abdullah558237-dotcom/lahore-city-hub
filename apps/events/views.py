from django.shortcuts import render, redirect

def event_list(request):
    return redirect('core:home')
