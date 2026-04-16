FROM python:3.11

WORKDIR /code

ENV PYTHONPATH="/code:${PYTHONPATH}"

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./migrations /code/migrations
COPY ./alembic.ini /code/alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
