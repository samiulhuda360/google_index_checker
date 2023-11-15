import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import URLCheckForm
from .models import URLCheck
from io import StringIO
from django.http import JsonResponse
from index_checker_project.celery import app
from celery.result import AsyncResult
from django.urls import reverse
from pandas import read_excel
import logging
from .models import UrlIndexStatus
# Import the Celery task
from .tasks import check_and_save_urls

def reset_view(request):
    # Retrieve task IDs from the session or database
    task_ids = request.session.get('task_ids', [])

    # Revoke each task
    for task_id in task_ids:
        app.control.revoke(task_id, terminate=True)

    # Clear the session and UrlIndexStatus table
    del request.session['task_ids']
    UrlIndexStatus.objects.all().delete()

    # Redirect to a safe page or render a template
    return redirect('check-urls')




def fetch_url_status(request):
    url_status_list = list(UrlIndexStatus.objects.values())
    return JsonResponse({'url_status_list': url_status_list})

def url_check_view(request):
    if request.method == 'POST':
        UrlIndexStatus.objects.all().delete()
        form = URLCheckForm(request.POST, request.FILES)
        print(form.errors)  # This will print form errors, if any
        if form.is_valid():
            urls = []

            # Check if URLs are uploaded as an Excel file
            if 'urls_file' in request.FILES:
                urls_file = request.FILES['urls_file']
                # Read the Excel file into a pandas DataFrame
                excel_data = read_excel(urls_file)
                # Extract URLs assuming there is a column named 'URL'
                try:
                 urls = excel_data['URL'].tolist()
                except KeyError as e:
                    # Log the error or inform the user
                    print(f"Column not found in the Excel file: {e}")
                    urls = []  # Or handle the error as appropriate
            # If URLs are provided in the text area
            elif form.cleaned_data['urls_text']:
                urls = form.cleaned_data['urls_text'].splitlines()

            # Normalize the URLs by stripping whitespace
            urls = [url.strip() for url in urls if url.strip()]

            # Initiate the Celery tasks
            task_ids = []
            task = check_and_save_urls.delay(urls)
            task_ids.append(task.id)

            # Store the task IDs in the session
            request.session['task_ids'] = task_ids
            # Redirect to a new URL where the task status will be checked
            return redirect('task_status')  # Use the name of the URL pattern for task_status view

    else:
        form = URLCheckForm()

    url_status_list = UrlIndexStatus.objects.all()  # Fetch all UrlIndexStatus objects
    return render(request, 'index_check/url_check.html', {'form': form, 'url_status_list': url_status_list})
    
# Set up logging
# logger = logging.getLogger(__name__)

def task_status(request):
    # logger.debug("Entered task_status view")

    task_ids = request.session.get('task_ids', [])
    
    # logger.info(f"Task IDs in session: {task_ids}")  # Log the task IDs
    
    if not task_ids:
        return JsonResponse({'all_done': True, 'redirect_url': reverse('download_csv')})

    task_status_list = [(task_id, AsyncResult(task_id).ready()) for task_id in task_ids]

    # # Log each task status
    # for task_id, status in task_status_list:
    #     logger.info(f"Task {task_id} completion status: {status}")

    all_done = all(status for _, status in task_status_list)

    # logger.info(f"All tasks done: {all_done}")  # Log the overall status

    if all_done:
        return JsonResponse({'all_done': True, 'redirect_url': reverse('download_csv')})
    else:
        return JsonResponse({'all_done': False})


def download_csv(request):
    task_ids = request.session.get('task_ids', [])
    
    # Generate the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="url_checks.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['URL', 'Index Status'])
    
    urls_to_delete = []

    for task_id in task_ids:
        task_result = AsyncResult(task_id)
        results = task_result.get()  
        if isinstance(results, list):
            for url, is_indexed in results:
                writer.writerow([url, is_indexed])
                urls_to_delete.append(url)
        else:
            writer.writerow([results[0], results[1]])
            urls_to_delete.append(results[0])

    # Delete the records from the database
    UrlIndexStatus.objects.filter(url__in=urls_to_delete).delete()

    # Clear the session or handle it as needed
    del request.session['task_ids']

    return response