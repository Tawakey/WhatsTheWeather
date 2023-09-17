FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1

WORKDIR /bot
COPY . ./
RUN pip install -r requirements.txt


CMD ["python3", "bot.py"]