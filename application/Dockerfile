FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt ./
COPY . ./
RUN pip install -r requirements.txt
EXPOSE 8000