from testcontainers.postgres import PostgresContainer


# stinky ass hack for test, i hate this
def setup_test_container():
    postgres = PostgresContainer(
        "docker.io/pgvector/pgvector:0.8.0-pg17",
        port=5432,
        username="postgres",
        password="postgres",
        dbname="postgres",
    ).with_bind_ports(5432, 5432)

    postgres.start()


def pytest_sessionstart(session):
    setup_test_container()
