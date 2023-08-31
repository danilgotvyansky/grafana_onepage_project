# application/grfn_app/tests.py
from django.test import TestCase
import requests
from django.conf import settings
from unittest.mock import patch, Mock  # import the Mock class
from .models import GrafanaServer, Dashboard, Board
from .views import adjust_url, fetch_and_save_panel_data  # import your views

# Create your tests here.

# Tests that a GrafanaServer object can be retrieved from the database
class TestGrafana(TestCase):
    def test_retrieve_grafana_server_from_database(self):
        grafana_server = GrafanaServer(url="http://example.com", username="admin", password="password")
        grafana_server.save()
        retrieved_grafana_server = GrafanaServer.objects.get(url="http://example.com")
        assert retrieved_grafana_server.username == "admin"
        assert retrieved_grafana_server.password == "password"

    @patch('grfn_app.views.requests.get')
    def test_successful_fetch_and_save_panel_data(self, get_request):
        grafana_server = GrafanaServer(url="http://example.com", username="admin", password="password")
        grafana_server.save()

        mock_response1 = Mock(status_code=200)
        mock_response1.json = Mock(return_value=[
            {'uid': 'dashboard1', 'title': 'Dashboard 1', 'isStarred': True},
            {'uid': 'dashboard2', 'title': 'Dashboard 2', 'isStarred': True}
        ])
        mock_response2 = Mock(status_code=200)
        mock_response2.json = Mock(return_value={
            'dashboard': {
                'panels': [
                    {
                        'id': 35,
                        'title': 'Dummy panel 1',
                        'embedUrl': 'http://example.com/d-solo/dashboard1/dummy-panel-1?orgId=1&panelId=35'
                    },
                    {
                        'id': 11,
                        'title': 'Dummy panel 2',
                        'embedUrl': 'http://example.com/d-solo/dashboard1/dummy-panel-2?orgId=1&panelId=11'
                    }
                ],
            }
        })
        mock_response3 = Mock(status_code=200)
        mock_response3.json = Mock(return_value={
            'dashboard': {
                'panels': [
                    {
                        'id': 36,
                        'title': 'Dummy panel 3',
                        'embedUrl': 'http://example.com/d-solo/dashboard2/dummy-panel-3?orgId=1&panelId=36'
                    },
                    {
                        'id': 12,
                        'title': 'Dummy panel 4',
                        'embedUrl': 'http://example.com/d-solo/dashboard2/dummy-panel-4?orgId=1&panelId=12'
                    }
                ],
            }
        })

        get_request.side_effect = [mock_response1, mock_response2, mock_response3]

        response = fetch_and_save_panel_data(grafana_server)

        self.assertTrue(response)


    @patch('grfn_app.views.requests.get', side_effect=requests.exceptions.RequestException)
    def test_adjust_url_unreachable(self, get_request):
        adjusted_url = adjust_url('http://example.com', 'username', 'password')
        self.assertIsNone(adjusted_url)


    @patch('grfn_app.views.requests.get')
    def test_adjust_url_https_capability(self, get_request):
        get_request.return_value.status_code = 200
        adjusted_url = adjust_url('http://example.com', 'username', 'password')
        self.assertEqual(adjusted_url, 'https://example.com/')