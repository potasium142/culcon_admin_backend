# Culinary Connect - Installation Guide

## Minimum system requirement

1. Operating System: Debian 12 or equivalent distro
2. Memory:
	1. Java backend / Frontend: 512 Mb
	2. Python backend: 6 Gb
	3. LLM Container: 4 Gb
3. Disk space: 10 Gb of free disk space
4. Network: Port 8080, 8000, 3000, 3001, 11434 are unoccupied
5. Require software
	- Container deployment: Docker or any equivalent container runner 
	- Manual deployment:
        - Requirement environment:
            1. Python 3.10.15
            2. JRE 21
            3. NodeJS 21
            4. Docker
        - Require system packages: wget, curl, libpq, libgl, libglib

## Deployment order
1. PostgreSQL with PGVector extension
2. Ollama LLM Server
3. Python backend
4. Java backend
5. Frontend

## Installation
### Starting container
#### PostgreSQL
1. Pull PostgreSQL with PGVector image

    ```bash 
    docker pull pgvector/pgvector:0.8.0-pg15
    ```
2. Run container with these environment variable set

    |Name|Value|
    |-|-|
    |POSTGRES_PASSWORD|postgres|

And bindport ```5432:5432```



