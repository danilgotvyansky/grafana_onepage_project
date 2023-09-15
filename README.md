# Grafana One-Page Dynamic Board portfolio project # 
Grafana One-Page Dynamic Board portfolio project by Danylo Hotvianskyi. Stack: Django, Grafana, Prometheus, Docker, MariaDB, Nginx, Bash

## Overview ##

### Application description ###
<details> 
 <summary>Expand for description</summary> 
  
  The [application](application) is a form of dynamic Grafana panel viewer. It connects to a [Grafana server](#grafana), fetches certain dashboard and panel details, and displays them using a slideshow. It provides users the ability to control the slideshow and choose the time interval between the slides. The application leverages Django's ORM to store information related to the server, dashboards, and panels, and provides an interactive interface to control and view the data.
  
  P.S. I am not a good tester and frontender, so don't judge me strong for those please :)
  
  #### Backend ####

  Backend part of the application is mainly repsented by the models.py and views.py files.

  1. In [models.py](application/grfn_app/models.py), the models represent the entities in Grafana which are being used in this application.
  * `GrafanaServer` model: Stores Grafana server credentials data for API calls.
  * `Dashboard` model: It represents the Grafana dashboards with a unique id and slug for URLs. Dashboards' slugs are used to construct panel `embed_url` in the [frontend](#frontend) part of the application.
  * `Board` model: Represents a panel in Grafana. It has the foreign key relation with the `Dashboard` model and has properties like `panel id`, `panel title`, and an `embed_url` for Grafana iframe embedding. There are also some additional properties like slide interval and time range.

2. In [views.py](application/grfn_app/views.py):
    - `adjust_url()` function adjusts the Grafana server's URL allowing both http and https protocols, appending the necessary `/` at the end, and checking if the server can be reached.
    - `get_embed_url()` generates the URL to embed a panel.
    - `fetch_and_save_panel_data()` connects to the Grafana API endpoint to fetch dashboard data and then fetches individual dashboard details including the panels inside them. This data is then saved in the respective models.
    - `disconnect_grafana()` disconnects from the Grafana server by deleting all records from the related models.
    - `change_slide_interval()`: This view is used for **AJAX requests** handling from the front-end to change the slide intervals of panels.
    - `main_dashboard()` is the main view for this application. This handles both `GET` and `POST` requests. It handles the form submissions for entering Grafana server details, selecting dashboards, selecting panels from these dashboards, and more. This view then renders all this data on the [frontend](#frontend).
  
  #### Frontend ####

  Frontend is represented by the main_dashboard.html template and simple.min.css. 

  In [main_dashboard.html](application/grfn_app/templates/grfn_app/main_dashboard.html), the user interacts with the web interface rendered by the Django application.
  * It allows users to input Grafana server details.
  * It provides the ability to select dashboards from a checkbox list which is fetched dynamically from the server.
  * It also provides the ability to select panels from the selected dashboards.
  * The slide interval can also be controlled from the front-end which sends `POST` requests to the backend using `AJAX` and updates the values in the database.
  * It shows sliders of Grafana panels in a slideshow fashion with controls like play, stop, next, and previous.
  * Uses [simple.min.css](application/grfn_app/static/simple.min.css) as a CSS template. It is not developed by me, however, I failed to find its author to mention them here.
  
  #### Settings ####
    
  [settings.py](application/grfn_project/settings.py)
  
  * Setup for integrating MySQL database with Django, password validation, and default primary key field type.
  * Defines settings for serving static files.
  * Leverages environment variables for sensitive and instance-specific settings such as the SECRET_KEY, DEBUG settings, database credentials, etc with the help of Django-Environ library.
  * Defines the `CSRF_TRUSTED_ORIGINS` to allow testing the application inside docker container and resolve the *CSRF untrustworthy origin* error.
  
  #### Tests ####

  The tests are written using Django's `TestCase` and Python's `unittest.mock` for mocking requests. The main focus is to test the correct behaviour of creating dashboards in the database and handling requests to Grafana Server.

  [tests.py](application/grfn_app/tests.py)
  
  This includes test cases for the functionalities of the application:
  
  * Tests creating a dashboard with its associated properties.
  * Tests whether a Grafana server can be retrieved from the database.
  * Tests successful request for fetching and saving panel data.
  * Testing error handling when a URL cannot be reached.
  * Tests the function to adjust URLs to use HTTPS if available.

  #### Application local testing ####
  Use the instructions from the [Local Cluster](#local-cluster) paragraph of this readme to deploy an application using **Docker compose** or follow the instructions below to omit hard containerization: 
  * Fill in the **.env** file with all the required values. **(!)** .env file should be located in the repository root directory (e.g. /grafana_onepage_project)
  * Install dependencies from [requirements.txt](application/requirements.txt):
  ```commandline
  pip3 install -r application/requirements.txt
  ```
  * Run the **MariaDB** container:
  ```commandline
  docker run -d \
  -p 3306:3306 \
  --env-file .env \
  --name mariadb \
  --restart unless-stopped \
  mariadb
  ```
  * Migrate models to the database:
  ```
  python3 application/manage.py migrate
  ```
  * Start application:
  ```
  python3 application/manage.py runserver
  ```

  You would also need to launch **Grafana**, **Prometheus**, **Node-exporter**, import some dashboards and star them to test all application features completely.
  
 </details>

### Local Cluster ###

### Grafana ###