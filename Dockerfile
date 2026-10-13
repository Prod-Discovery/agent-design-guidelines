FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py review.py usage.py stats_page.py patterns.json index.html ./
COPY demo ./demo
COPY scripts/build_patterns.py scripts/ids.json ./scripts/
# Checks patterns.json and writes patterns.md. A broken patterns.json fails the build,
# so a bad edit never reaches the live site.
RUN python scripts/build_patterns.py

# One worker with threads: each review mostly waits on Claude for 10 to 30 seconds.
CMD exec gunicorn app:app --bind ":${PORT:-8080}" --workers 1 --threads 8 --timeout 120
