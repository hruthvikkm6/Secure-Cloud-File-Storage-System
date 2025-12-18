 FROM python:3.11-slim as builder
WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN pip wheel --wheel-dir /usr/src/app/wheels -r requirements.txt
FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system app && adduser --system --group app
COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
RUN chmod +x ./start.sh
RUN chown -R app:app /app
USER app
CMD ["./start.sh"]