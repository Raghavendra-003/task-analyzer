from django.http import HttpResponse

def home(request):
    return HttpResponse("Task Analyzer API is running. Use /api/tasks/analyze/")