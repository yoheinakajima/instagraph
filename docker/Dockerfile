FROM python:3.11
WORKDIR /app
COPY ../requirements.txt .
RUN pip install -r requirements.txt
COPY .. /app/
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
