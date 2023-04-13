FROM python:3.9-slim-buster

EXPOSE 8000

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY /sunnyside-tie .

CMD ["python", "app.py"]