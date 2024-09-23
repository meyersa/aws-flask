FROM python:3

# Copy requirements
COPY ./requirements.txt /requirements.txt

# Install dependencies
RUN pip3 install -r /requirements.txt --break-system-packages

# Copy source
COPY ./src /src

# Work in source
WORKDIR /src

# Start Server with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
