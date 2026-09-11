FROM python:3.12-slim

WORKDIR /app

COPY cache/requirements.txt ./cache/requirements.txt
RUN pip install --no-cache-dir -r ./cache/requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["bash"]
