# Grafana #

In this project Grafana is used to visualize our monitoring metrics scraped by [Prometheus](/prometheus/README.md) and alert us in case of any incidents in our cluster and for our [application](/application) testing purposes at the same time. We will connect to it and use the **Grafana API** to show panels from it.

### Installation ###

1. Launch Grafana as a **docker container** ([image](https://hub.docker.com/r/grafana/grafana)) on the **control1** machine with an additional option to allow **embedded panels** and install the *Grafana clock* plugin for one of our future dashbaords:

```commandline
docker run -d -p 3000:3000 --name grafana -e GF_INSTALL_PLUGINS=grafana-clock-panel -e GF_SECURITY_ALLOW_EMBEDDING=true --restart unless-stopped grafana/grafana
```
2. Make sure **Prometheus** data source is properly configured by checking if the correct IP is specified in *Administration >> Data Sources >> the Prometheus server* URL field.
3. Create a folder to put our testing dashboards to. For example, let's call it *API Test*.
3. Install some basic dashboards to monitor our services and put them into the created folder:
   * [Node Exporter Full](https://grafana.com/grafana/dashboards/1860-node-exporter-full/)
   * [Prometheus 2.0 Overview](https://grafana.com/grafana/dashboards/3662-prometheus-2-0-overview/)