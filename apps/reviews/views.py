from django.shortcuts import render, redirect

def review_index(request):
    return redirect('core:home')
