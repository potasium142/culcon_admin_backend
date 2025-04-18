# Culinary Connect - Installation Guide

## Minimum system requirement

1. Operating System: Debian 12 or equivalent distro
2. Memory:
   - Java backend / Frontend: 512Mb
   - Python backend: 6Gb
   - LLM Container: 4Gb
3. Disk space: 10Gb of free disk space
4. Network: Port 8080, 8000, 3000, 3001, 11434 are unoccupied
5. GPU Acceleration \* : Nvidia GPU w 8Gb VRAM / CUDA support
6. Require software
   - Git, wget, curl
   - Docker or any equivalent container runner
   - Require system packages for GPU acceleration: nvidia-gpu, nvidia-container-toolkit

> [!NOTE]
>
> \* System will automatically fallback for CPU acceleration if no GPU was detected

## Deployment order

1. PostgreSQL with PGVector extension
2. Ollama LLM Server
3. Python backend
4. Java backend
5. Frontend

## Installation

### PostgreSQL

1.  Pull PostgreSQL with PGVector image

    ```bash
    docker pull pgvector/pgvector:0.8.0-pg16
    ```

2.  Run container with these environment variable / parameters set

    | Name                     | Value        |
    | ------------------------ | ------------ |
    | **POSTGRES_PASSWORD \*** | **postgres** |
    | POSTGRES_USER            | postgres     |
    | POSTGRES_DB              | postgres     |

    > [!IMPORTANT]
    >
    > \* is required parameter

3.  Start container

    ```bash
    docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=<password> pgvector/pgvector:0.8.0-pg16
    ```

### Ollama LLM Server

1.  Pull Ollama image

    ```bash
    docker pull ollama/ollama
    ```

2.  Create a directory to mount data

3.  Setup LLM model

    - **Using pretrained weight**

    ```bash
    curl <ollama endpoint>/api/pull -d '{"model":"gemma3:1b"}'
    ```

    - **Finetuned weight (Safetensor)**

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

4.  Run LLM container
    ```bash
    docker run -d -p 11434:11434 -v <data directory>:/root/.ollama ollama
    ```
    > [!TIP]
    >
    > Add `--gpus=all` for GPU acceleration

### **BACKEND**

> [!IMPORTANT]
> The table below is share environment variable **essential** for both backend

| Name                  | Default value\* | Description           |
| --------------------- | --------------- | --------------------- |
| DB_URL                | localhost       | URL for database      |
| DB_USERNAME           | postgres        | Username for database |
| DB_PASSWORD           | postgres        | Password for database |
| SMTP_USER             |                 | Username for SMTP     |
| SMTP_PASSWORD         |                 | Password for SMTP     |
| CLOUDINARY_NAME       |                 | Cloudinary cloud name |
| CLOUDINARY_API_KEY    |                 | Cloudinary API key    |
| CLOUDINARY_API_SECRET |                 | Cloudinary API secret |
| PAYPAL_CLIENT_ID      |                 | PayPal client id      |
| PAYPAL_CLIENT_SECRET  |                 | PayPal client secret  |

> [!NOTE]
>
> - \* Default value only apply for **python backend**
> - Environment variable can be set in `.env` for local run

> [!IMPORTANT]
>
> - **_These environment variable need to be set when the container was create_**
> - Add `-e <variable>=<value>` argument for every variable and its value

#### Python backend

1. Clone repository

   ```bash
   git clone https://github.com/potasium142/culcon_admin_backend/
   cd culcon_admin_backend
   ```

2. Build container

   ```bash
   docker build -f Containerfile -t <image tags>
   ```

3. Create directory for AI weights

   ```bash
   mkdir weights
   ```

4. Download AI weights

   ```bash
   bash ./weights_download.bash
   ```

   > [!TIP]
   >
   > `-d <directory>` to set output directory

5. Create container

   > [!IMPORTANT]
   >
   > - Environment variable for python backend
   > - \* is required

   | Name                 | Value              | Description               |
   | -------------------- | ------------------ | ------------------------- |
   | SECRET_KEY \*        |                    | Secret key for JWT        |
   | LLM_ENDPOINT \*      |                    | Endpoint for LLM          |
   | TOKEN_EXPIRE_MINUTES | 7200               | Expire time for JWT token |
   | DB_NAME              | postgres           | Target database's name    |
   | DB_PORT              | 5432               | Target port of database   |
   | DB_DRIVER            | postgresql+psycopg | Database driver           |
   | SMTP_PORT            | 587                | Port for SMTP             |

   ```bash
   docker run -p 8000:8000 -e <variable>=<value> ... -v <weights directory>:/workdir/ai/weights <image tags>
   ```

   > [!TIP]
   >
   > Add `--gpus=all` for GPU acceleration, or system will use CPU only otherwise

#### Java backend

1. Clone repository

   ```bash
   git clone https://github.com/potasium142/culcon_backend/
   cd culcon_backend
   ```

2. Build container

   ```bash
   docker build -f Containerfile -t <image tags>
   ```

3. Create container

   > [!IMPORTANT]
   >
   > - Environment variable for ~Spring Boot backend~
   > - All variables in the table are required

   | Name                        | Description                     |
   | --------------------------- | ------------------------------- |
   | JWT_SECRET_KEY              | Secret key for JWT              |
   | JWT_EXPIRATION              | Expire time for JWT token       |
   | GOOGLE_OAUTH2_CLIENT_ID     | Google OAuth2 client ID         |
   | GOOGLE_OAUTH2_CLIENT_SECRET | Google OAuth2 client secret     |
   | GOOGLE_AUTH_REDIRECT_URI    | Redirect URI for Google OAuth2  |
   | FRONTEND_ENDPOINT           | Endpoint for customer frontend  |
   | DEPLOY_URL                  | Deploy endpoint of this backend |

   ```bash
   docker run -p 8080:8080 -e <variable>=<value> ... <image tags>
   ```

#### Frontend

> [!NOTE]
>
> This apply for both frontend
