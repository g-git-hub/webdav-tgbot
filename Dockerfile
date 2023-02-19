FROM python:3.11.1-alpine
WORKDIR /app
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
COPY main.py .
ENV PATH="/.venv/bin:$PATH"
CMD ["pipenv", "run", "python", "main.py"]