# Prometheus #

Prometheus is used to scrape all hosts performance metrics using the exporters. Then, these metrics are used by [Grafana](/grafana/README.md) for monitoring visualization, alerting and application testing.

**Used exporters:**
* [Node exporter](https://github.com/prometheus/node_exporter) - to scrape main machine metrics (CPU usage, Disk I/O, MEM usage, etc.). Launched on **all nodes**.
* Also, **Prometheus** scrape its own monitoring-related metrics.

### Installation ###

1. Launch Prometheus as a **docker container** ([image](https://hub.docker.com/r/prom/prometheus/)) with the additional options to mount our created config file. Also, indicate the name of the container and assign the *unless-stopped* restart policy.
```commandline
docker run -d -p 9090:9090 -v $PWD/prom/prometheus.yml:/etc/prometheus/prometheus.yml --name grfnapp_prom --restart unless-stopped prom/prometheus
```

**Prometheus** should be working properly on [http://localhost:9090](http://localhost:9090)