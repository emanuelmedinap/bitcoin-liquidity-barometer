# Cloud Run image for the Streamlit report app.
# Serves the committed static bundle only — no BigQuery at runtime.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    PORT=8080

WORKDIR /srv

# Dependencies first, for layer caching.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# App code + the static bundle it reads at serve time (figure, CSV, index.html).
# Deliberately no BigQuery client and no SQL/generator — nothing is queried at runtime.
COPY app/ ./app/
COPY index.html ./
COPY analysis/liquidity_overlay.png analysis/liquidity_overlay_data.csv ./analysis/

# Cloud Run sends traffic to $PORT (default 8080). Bind Streamlit to it on 0.0.0.0.
EXPOSE 8080
# Shell form so ${PORT} expands from the environment Cloud Run injects.
CMD streamlit run app/streamlit_app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
