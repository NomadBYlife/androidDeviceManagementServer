from django.shortcuts import render

def index(request):
    return render(request, 'socket_client/index2.html')

