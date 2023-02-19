FROM python:3.11.1-slim AS base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS deps
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base AS runtime
COPY --from=deps /.venv ./.venv
ENV PATH="/.venv/bin:$PATH"
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser
COPY main.py .
CMD ["python", "main.py"]