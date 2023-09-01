FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt ./
COPY . ./
RUN pip install -r requirements.txt
EXPOSE 8000
LABEL org.opencontainers.image.source=https://github.com/danilgotvyansky/grafana_onepage_project