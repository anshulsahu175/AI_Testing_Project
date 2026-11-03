# Test runner image: Python, pinned requirements, and Chromium for the Playwright UI tests.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_MOCKS=true

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# Mock mode by default, so no API keys are needed. Pass USE_MOCKS=false plus keys for real models.
CMD ["pytest", "-n", "2"]
