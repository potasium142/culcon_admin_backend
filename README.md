# Culinary Connect - Installation Guide

## Minimum system requirement

1. Operating System: Debian 12 or equivalent distro
2. Memory:
   1. Java backend / Frontend: 512Mb
   2. Python backend: 6Gb
   3. LLM Container: 4Gb
3. Disk space: 10Gb of free disk space
4. Network: Port 8080, 8000, 3000, 3001, 11434 are unoccupied
5. GPU Acceleration : Nvidia GPU w 8Gb VRAM / CUDA support
6. Require software
   - Container deployment: Docker or any equivalent container runner
   - Manual deployment:
     - Requirement environment:
       1. Python 3.10.15
       2. JRE 21
       3. NodeJS 21
       4. Docker
     - Require system packages: wget, curl, libpq, libgl, libglib
     - Require system packages for GPU acceleration: nvidia-gpu, nvidia-container-toolkit

> System will automatically fallback for CPU acceleration if no GPU was detected

## Deployment order

1. PostgreSQL with PGVector extension
2. Ollama LLM Server
3. Python backend
4. Java backend
5. Frontend

## Installation

### Starting container

1. PostgreSQL

   1. Pull PostgreSQL with PGVector image

      ```bash
      docker pull pgvector/pgvector:0.8.0-pg16
      ```

   2. Run container with these environment variable / parameters set

      | Name                     | Value        |
      | ------------------------ | ------------ |
      | **POSTGRES_PASSWORD \*** | **postgres** |
      | POSTGRES_USER            | postgres     |
      | POSTGRES_DB              | postgres     |

      > \* is required parameter

   3. Start container

      ```bash
      docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=<password> pgvector/pgvector:0.8.0-pg16
      ```

2. Ollama LLM Server

   1. Pull Ollama image

   ```bash
    docker pull ollama/ollama
   ```

   2. Create a directory to mount data

   3. Setup LLM model

      - **Using pretrained weight**

      ```bash
      curl <ollama endpoint>/api/pull -d '{"model":"gemma3:1b"}'
      ```

      - **Finetuned weight**

        1. Extract finetuned weight into a directory
        2. Create `Modelfile` file with context
           > FROM .
           > SYSTEM <system prompt>
        3. Create a temporary container to build model
           ```bash
           docker create --name llm_build_tmp -v <data directory>:/root/.ollama -v <weight directory>:/weight ollama
           docker start llm_build_tmp
           docker exec -it llm_build_tmp ollama create <model name> -f /weight/Modelfile
           docker stop llm_build_tmp
           docker rm llm_build_tmp
           ```

   4. Run LLM container
      ```bash
      docker run -d -p 11434:11434 -v <data directory>:/root/.ollama ollama
      ```
      > Add `--gpus=all` for GPU acceleration
