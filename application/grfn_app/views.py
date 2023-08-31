# application/grfn_app/views.py
import base64
import requests
import logging
from django.shortcuts import render,redirect
from .models import GrafanaServer, Dashboard, Board
from urllib.parse import urlparse
from django.contrib import messages
from django.db import connection

org_id = 1


def adjust_url(url, username, password):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https']:
        url = 'http://' + url

    parsed_url = urlparse(url)
    if not parsed_url.path.endswith('/'):
        url += '/'

    # Check for https capability and adjust the url if supported
    try:
        https_url = url.replace('http://', 'https://')
        api_url = f"{https_url}api/search"  # Checking the API endpoint directly
        headers = {
           'Authorization': f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
        }
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return https_url

    except requests.exceptions.RequestException:
        # If requests fails, that means https is not supported
        try:
            api_url = f"{url}api/search" # Checking the API endpoint directly
            headers = {
                'Authorization': f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
            }
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                return url

        except requests.exceptions.RequestException:
            pass

    return None

def get_embed_url(grafana_server, dashboard_uid, dashboard_slug, panel_id):
    base_url = f"{grafana_server.url}"
    url_params = "&".join([f"panelId={panel_id}"])
    embed_url = f"{base_url}d-solo/{dashboard_uid}/{dashboard_slug}?orgId={org_id}&{url_params}"
    return embed_url


def fetch_and_save_panel_data(grafana_server):
    # Fetch all starred dashboards and save their data to the database
    if grafana_server:
        api_url = f"{grafana_server.url}api/search"
        headers = {
            'Authorization': f"Basic {base64.b64encode(f'{grafana_server.username}:{grafana_server.password}'.encode()).decode()}"
        }
        params = {
            'isStarred': 'true',
            'type': 'dash-db',
        }
        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for non-200 status codes

            if response.status_code == 200:
                dashboards_data = response.json()
                # print(dashboards_data)
                # Filter out dashboards where 'isStarred' is not True
                dashboards_data = [dashboard for dashboard in dashboards_data if dashboard.get('isStarred', False)]

                for dashboard_data in dashboards_data:
                    dashboard_uid = dashboard_data.get('uid', '')
                    dashboard_slug = dashboard_data.get('title', '').lower().replace(' ', '-')
                    dashboard_title = dashboard_data.get('title', '')
                    print(f"Fetching panels for dashboard: {dashboard_title}")

                    # Update or create the Dashboard objects
                    dashboard, created = Dashboard.objects.update_or_create(
                        dashboard_uid=dashboard_uid,
                        defaults={'title': dashboard_title, 'dashboard_slug': dashboard_slug}
                    )

                    # Use the correct API endpoint to fetch the dashboard details
                    api_url = f"{grafana_server.url}api/dashboards/uid/{dashboard_uid}"
                    try:
                        response = requests.get(api_url, headers=headers)
                        response.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        print(f"Error occurred while fetching dashboard details: {e}")
                        continue

                    if response.status_code == 200:
                        dashboard_details = response.json()
                        panels = dashboard_details.get('dashboard', {}).get('panels', [])

                        for panel in panels:
                            panel_id = panel.get('id')
                            panel_title = panel.get('title')
                            # Construct the embed URL for the panel
                            embed_url = get_embed_url(grafana_server, dashboard_uid, dashboard_slug, panel_id)

                            # Try to fetch the existing panel data for the same dashboard
                            existing_panel = Board.objects.filter(panel_id=panel_id, dashboard=dashboard).first()

                            if existing_panel:
                                # If panel data for the same dashboard and panel_id exists, update its data
                                existing_panel.panel_title = panel_title
                                existing_panel.embed_url = embed_url
                                existing_panel.save()
                            else:
                                panel_obj = Board.objects.create(
                                    panel_id=panel_id,
                                    dashboard=dashboard,
                                    panel_title=panel_title,
                                    embed_url=embed_url,
                                )
                return True
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching dashboards: {e}")
            return False


def disconnect_grafana(request):
    # delete records from tables in the provided order
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM grfn_app_board;")
        cursor.execute("DELETE FROM grfn_app_dashboard;")
        cursor.execute("DELETE FROM grfn_app_grafanaserver;")
    # Then, redirect to the main_dashboard view to reload the page
    return redirect('main_dashboard')


def main_dashboard(request):
    grafana_server = GrafanaServer.objects.first()
    selected_dashboards = []
    dashboard_title = ""
    embed_url = ""
    panels_data = []
    selected_panel = None

    if request.method == 'POST':
        # Handle form submission to save Grafana server information
        url = request.POST.get('url')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if url and username and password:
            try:
                adjusted_url = adjust_url(url, username, password)
                if not adjusted_url:
                    messages.error(request,
                                   'Entered URL is not a valid Grafana server link. Please check and try again.')
                elif grafana_server:
                    grafana_server.url = adjusted_url
                    grafana_server.username = username
                    grafana_server.password = password

                    if fetch_and_save_panel_data(grafana_server):
                        grafana_server.save()
                    else:
                        messages.error(request,
                                       'Unable to reach the entered URL. Please check the Grafana server link and try again.')
                else:
                    grafana_server = GrafanaServer(url=adjusted_url, username=username, password=password)

                    if fetch_and_save_panel_data(grafana_server):
                        grafana_server.save()
                    else:
                        messages.error(request,
                                       'Unable to reach the entered URL. Please check the Grafana server link and try again.')
            except Exception as ex:
                messages.error(request,
                               f"Error occurred while adjusting the URL. Please check if the URL is valid. \
        Error: {ex}")

        # If the 'action' field is present in the POST data, process the 'Select Dashboards' form submission
        if 'action' in request.POST:
            selected_dashboards = request.POST.getlist('selected_dashboards')

            if selected_dashboards and grafana_server:
                # Fetch panel data from the database for the selected dashboards
                for dashboard_uid in selected_dashboards:
                    dashboard = Dashboard.objects.filter(dashboard_uid=dashboard_uid).first()
                    if dashboard:
                        # Get the panels associated with this dashboard from the database
                        panels = Board.objects.filter(dashboard=dashboard)
                        for panel in panels:
                            panels_data.append({'id': panel.panel_id, 'title': panel.panel_title})

            # If the 'Select Panels' form is submitted, fetch the selected panel's embed URL and dashboard title
            if 'action' in request.POST and 'selected_panels' in request.POST:
                selected_panel_id = int(request.POST.get('selected_panels', ''))
                selected_panel = Board.objects.filter(panel_id=selected_panel_id).first()
                if selected_panel:
                    embed_url = selected_panel.embed_url
                    dashboard_title = selected_panel.dashboard.title

        # If the 'Select Time Range' form is submitted, save the selected time range to the database
        if 'action' in request.POST and 'time_range' in request.POST:
            selected_time_range = request.POST.get('time_range')
            panels = Board.objects.all()
            for panel in panels:
                panel.time_range = selected_time_range
                panel.save()

    # If the request is not a POST or no valid form data is submitted, display the dashboard as usual
    return render(request, 'grfn_app/main_dashboard.html', {
        'grafana_server_url': grafana_server.url if grafana_server else None,
        'dashboards': Dashboard.objects.all(),
        'selected_dashboards': selected_dashboards,
        'dashboard_title': dashboard_title,
        'panels_data': panels_data,
        'embed_url': embed_url,
        'selected_panel': selected_panel,
    })