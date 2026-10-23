FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app && mkdir -p /data/snapshots && chown -R app:app /data
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app price_service.py ./price_service.py
COPY --chown=app:app iran_market_data.py ./iran_market_data.py
COPY --chown=app:app source_registry.py ./source_registry.py
COPY --chown=app:app temporal_data.py ./temporal_data.py
COPY --chown=app:app tindex_provider.py ./tindex_provider.py
COPY --chown=app:app tindex_normalizer.py ./tindex_normalizer.py
COPY --chown=app:app iran_live_data.py ./iran_live_data.py
COPY --chown=app:app headline_signal_engine.py ./headline_signal_engine.py
COPY --chown=app:app research_pipeline.py ./research_pipeline.py
COPY --chown=app:app research ./research
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "price_service:app", "--host", "0.0.0.0", "--port", "8000"]
