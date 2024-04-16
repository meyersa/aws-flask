FROM ubuntu:latest

# Update
RUN apt update && apt upgrade -y

# Install Python
RUN apt install -y python3 python3-pip

# Install dependencies
RUN pip3 install flask jinja2 gunicorn

# Copy source
COPY ./src /src

# Work in source
WORKDIR /src

# Start Server with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
