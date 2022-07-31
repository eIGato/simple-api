FROM python:3.10

RUN pip install --no-cache-dir -U pip

RUN mkdir -p /src
WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY . .

RUN pip install --no-cache-dir --no-deps -r requirements.txt -r requirements-dev.txt

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
