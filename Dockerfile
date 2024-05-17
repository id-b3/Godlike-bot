FROM python:3.12-alpine

WORKDIR /discord/godlike
RUN mkdir ./data
COPY src/ src/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/discord/godlike/src"
RUN python3 "/discord/godlike/src/dbutils.py"
CMD ["python3", "./src/main.py"]