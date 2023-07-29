import base64
import requests
import logging
from django.shortcuts import render
from .models import GrafanaServer, Dashboard, Board

org_id = 1
def get_embed_url(grafana_server, dashboard_uid, dashboard_slug, panel_id):
    base_url = f"{grafana_server.url}"
    url_params = "&".join([f"panelId={panel_id}"])
    embed_url = f"{base_url}d-solo/{dashboard_uid}/{dashboard_slug}?orgId={org_id}&{url_params}"
    return embed_url


def fetch_and_save_panel_data(grafana_server):

    # Fetch all dashboards from the specified folder and save their data to the database
    if grafana_server and grafana_server.folder:
        api_url = f"{grafana_server.url}api/search"
        headers = {
            'Authorization': f"Basic {base64.b64encode(f'{grafana_server.username}:{grafana_server.password}'.encode()).decode()}"
        }
        params = {
            'folderIds': f"({grafana_server.folder})",
            'type': 'dash-db',
        }
        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for non-200 status codes
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while fetching dashboards: {e}")
            return

        if response.status_code == 200:
            dashboards_data = response.json()

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


def main_dashboard(request):
    grafana_server = GrafanaServer.objects.first()
    selected_dashboards = []
    dashboard_title = ""
    embed_url = ""
    panels_data = []

    if request.method == 'POST':
        # Handle form submission to save Grafana server information
        url = request.POST.get('url')
        username = request.POST.get('username')
        password = request.POST.get('password')
        folder = request.POST.get('folder')

        if url and username and password and folder:
            if grafana_server:
                grafana_server.url = url
                grafana_server.username = username
                grafana_server.password = password
                grafana_server.folder = folder
                grafana_server.save()
            else:
                grafana_server = GrafanaServer.objects.create(url=url, username=username, password=password, folder=folder)

            # Fetch all dashboards from the specified folder and save their data to the database
            fetch_and_save_panel_data(grafana_server)

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

    # If the request is not a POST or no valid form data is submitted, display the dashboard as usual
    return render(request, 'grfn_app/main_dashboard.html', {
        'grafana_server_url': grafana_server.url if grafana_server else None,
        'dashboards': Dashboard.objects.all(),
        'selected_dashboards': selected_dashboards,
        'dashboard_title': dashboard_title,
        'panels_data': panels_data,
        'embed_url': embed_url,
    })