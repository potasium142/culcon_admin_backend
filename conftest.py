import os
from testcontainers.postgres import PostgresContainer


# stinky ass hack for test, i hate this
def setup_test_container():
    os.environ["DB_PORT"] = "6969"
    postgres = PostgresContainer(
        "docker.io/pgvector/pgvector:0.8.0-pg17",
        port=6969,
        username="postgres",
        password="postgres",
        dbname="postgres",
    ).with_bind_ports(6969, 6969)

    postgres.start()


def pytest_sessionstart(session):
    setup_test_container()
