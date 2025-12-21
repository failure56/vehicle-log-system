FROM python:3.11-slim

WORKDIR /app

# Install test dependencies
COPY requirements.txt /app/tests/
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /app/tests/requirements.txt

# Copy test files
COPY . /app/tests/

CMD ["pytest", "tests/", "-v"]
