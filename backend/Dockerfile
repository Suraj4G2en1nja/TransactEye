FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Use gunicorn to serve your backend app; adjust module name to 'backend'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend:app"]
