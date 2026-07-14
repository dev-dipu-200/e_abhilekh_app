FROM python:3.11-slim AS builder

WORKDIR /build

COPY requrements.txt .
RUN pip install --no-cache-dir --user -r requrements.txt

FROM python:3.11-slim

RUN apt-get update -qq && apt-get install -y -qq \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
