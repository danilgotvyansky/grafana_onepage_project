# Grafana One-Page Dynamic Board portfolio project # 
Grafana One-Page Dynamic Board portfolio project by Danylo Hotvianskyi. Stack: Django, Grafana, Prometheus, Docker, MariaDB, Nginx, Bash, GitHub Actions

## Overview ##

### Application description ###

The [application](/application) is a form of dynamic Grafana panel viewer. It connects to a [Grafana server](#grafana), fetches certain dashboard and panel details, and displays them using a slideshow. It provides users the ability to control the slideshow and choose the time interval between the slides. The application leverages Django's ORM to store information related to the server, dashboards, and panels, and provides an interactive interface to control and view the data.
  
  P.S. I am not a good tester and frontender, so don't judge me strong for those please :)

<details> 
 <summary>Expand for detailed description</summary> 
  
  #### Backend ####

  Backend part of the application is mainly represented by the models.py and views.py files.

  1. In [models.py](application/grfn_app/models.py), the models represent the entities in Grafana which are being used in this application.
  * `GrafanaServer` model: Stores Grafana server credentials data for API calls.
  * `Dashboard` model: It represents the Grafana dashboards with a unique id and slug for URLs. Dashboards' slugs are used to construct panel `embed_url` for the [frontend](#frontend) part of the application.
  * `Board` model: Represents a panel in Grafana. It has the foreign key relation with the `Dashboard` model and has properties like `panel id`, `panel title`, and an `embed_url` for Grafana iframe embedding. There are also some additional properties like slide interval and time range.

  2. In [views.py](application/grfn_app/views.py):
  * `adjust_url()` function adjusts the Grafana server's URL allowing both http and https protocols, appending the necessary `/` at the end, and checking if the server can be reached.
  * `get_embed_url()` generates the URL to embed a panel.
  * `fetch_and_save_panel_data()` connects to the Grafana API endpoint to fetch dashboard data and then fetches individual dashboard details including the panels inside them. This data is then saved in the respective models.
  * `disconnect_grafana()` disconnects from the Grafana server by deleting all records from the related models.
  * `change_slide_interval()`: This view is used for **AJAX requests** handling from the front-end to change the slide intervals of panels.
  * `main_dashboard()` is the main view for this application. This handles both `GET` and `POST` requests. It handles the form submissions for entering Grafana server details, selecting dashboards, selecting panels from these dashboards, and more. This view then renders all this data on the [frontend](#frontend).

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

Services that produces the local cluster can be found in the [compose.yaml](compose.yaml) file.

It consists of:
* [Nginx](#nginx) container.
* Two [application](#application-description) containers.
* Two **MariaDB** containers.
* [Grafana](#grafana) container.
* [Prometheus](#prometheus) container.
* [Node-exporter](#node-exporter) container.
* [Docker network](#docker-network)

Later it is planned to include other exporters as well. 

Local cluster provisioning is being handled by the [local-cluster.sh](local-cluster.sh) and [compose.yaml](compose.yaml) files. 

See [Local cluster provisioning](#local-cluster-provisioning) for detailed instructions.

<details> 
 <summary>Expand for detailed description</summary>

  #### Nginx ####
  * Nginx is used as **proxy** and for **load balancing** the traffic between two application containers.
  * [default.conf](nginx/default.conf) maps the application containers using the docker network aliases.
  * It also sets the `server_name` to `grafana-app.local.com` domain.
  * Image: [nginx](https://hub.docker.com/_/nginx)

  #### Grafana ####
  * Grafana is used to visualize our monitoring metrics scraped by [Prometheus](#prometheus). 
  * It is also used for our [application](#application-description) testing purposes at the same time.
  * [provisioning](grafana/provisioning) folder contains dashboards' and datasources' initial configuration not to automate the launching process.
  * [dashboards](grafana/provisioning/dashboards) folder contains [Node Exporter Full](https://grafana.com/grafana/dashboards/1860-node-exporter-full/) and [Prometheus All Metrics](https://grafana.com/grafana/dashboards/19268-prometheus/).
  * Image: [grafana/grafana](https://hub.docker.com/r/grafana/grafana)
  
  #### Prometheus ####
  * Prometheus is used to scrape all hosts performance metrics using the exporters.
  * [prometheus.yml](prom/prometheus.yml) maps the exporter endpoint using the docker network aliases.
  * Image: [prom/prometheus](https://hub.docker.com/r/prom/prometheus)

  #### Node-exporter ####
  * Node-exporter is used to gather parent host performance metrics and is required for the application testing to make the **Node Exporter** dashboard work properly.
  * Image: [prom/node-exporter](https://hub.docker.com/r/prom/node-exporter)
  
  #### Docker network ####
  * There is custom `mynetwork` created and assigned to each cluster service.

</details>

### Local cluster provisioning ###

1. Create an `.env` file and ensure it contains all environment variables:
  <details> 
   <summary>Expand</summary>
      
      DB_HOST1=172.19.10.2
      DB_HOST2=172.19.10.22
      DB_PORT1=3306
      DB_PORT2=3307
      DB_NAME=
      DB_USER=
      DB_PASSWORD=
      DB_REPL1=
      DB_REPL2=
      DB_REPL1_PASSWORD=
      DB_REPL2_PASSWORD=
      MARIADB_ROOT_PASSWORD=
      DJANGO_SECRET_KEY=
      DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://docker.for.mac.localhost,http://grafana-app.local.com,http://localhost:8000,http://localhost:80,http://docker.for.mac.localhost:80,http://grafana-app.local.com:80,http://localhost:3000,http://docker.for.mac.localhost:3000
      DEBUG=True
      GRAFANA_USER_EMAIL=
      GRAFANA_USER=
      GRAFANA_USER_PASSWORD=
      GRAFANA_ADMIN_PASSWORD=
      GRAFANA_HOST=
  </details>

2. Execute the [local-cluster.sh](local-cluster.sh) script in the same directory where your `.env` file is located:

```commandline
bash local-cluster.sh
```

This file is created to automate the process of local cluster provisioning in terms of:
* Build all services in Docker compose.
* Source `.env` file only once.
* Set up **MariaDB Master-Master replication** between two database servers on startup.
* Launch containers in a proper order to ensure their activity won't affect the `MASTER_POS` value until the replication is fully set.
* Grant specific database permissions and settings after containers launch and replication setup.
* Do the initial [Grafana](#grafana) configuration for application demo testing via API: change admin user password, create the test user, star dashboards for that user.

3. Pass host mapping for the servername:

```commandline
echo "0.0.0.0    grafana-app.local.com" >> /etc/hosts
```
4. Access [http://grafana-app.local.com](http://grafana-app.local.com) to open an application.
5. Enter [http://localhost:3000](http://localhost:3000) to the **Grafana Server URL** and other details of the created test user using the `GRAFANA_USER` and `GRAFANA_USER_PASSWORD` values from the `.env` file.
6. Select Dashboards, panels and feel free to use all other application features.

### Video demo ###
<\There will be a video demo>

### CI/CD ###

CI/CD is represented by:
* [ci_build-test.yaml](.github/workflows/ci_build-test.yaml) - is triggered once there any **pull request** opened to compare with main branch and if there are any changes in the `application/*` path. 
  * Workflow sets up the *MariaDB* server for application testing including the permissions for the test user configuration.
  * Displays the database status for debugging.
  * Installs the application dependencies.
  * Run tests from [tests.py](application/tests.py).
  * All environmental variables are being fetched from the **GitHub Actions Repository secrets**.
  * Successful workflow run should indicate developers that the changes are ready for review and further merge.
* [ci_build-push.yaml](.github/workflows/ci_build-push.yaml) - is triggered on **push** to the `main` branch and if there are any changes in the `application/*` path.
  * Workflow authenticates to the **GitHub Container Registry**.
  * Builds the image out of the [application](/application) directory using [Dockerfile](application/Dockerfile) and assigns the `latest-app`* tag to it.
  * Pushes the image to the **GitHub Container Registry**.

\* `latest-app` tag is used because later there custom images of other services might be built in future.

**CD** part will be created later once there will be public hosting of this project.
