# MakroQuest API — non-editable kurulum (wheel gibi site-packages'a gider).
# Veri yolu MAKROQUEST_DATA_DIR ile verilir; __file__ tabanlı yol varsayımı yok.
FROM python:3.12-slim

WORKDIR /app

# Bağımlılık + kod katmanı
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

# Korpus + vakalar + golden set imaja gömülür
COPY data ./data
ENV MAKROQUEST_DATA_DIR=/app/data

# HF Spaces 7860 bekler; Render $PORT enjekte eder — ikisiyle de uyumlu
EXPOSE 7860
CMD ["sh", "-c", "uvicorn makroquest.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
