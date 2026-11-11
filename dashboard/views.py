from django.shortcuts import render
import json

# Create your views here.
def service_list(request):
    with open("results.json", "r") as file:
        loaded_data = json.load(file)
        return render(request, 'dashboard/service_list.html', {'services': loaded_data})