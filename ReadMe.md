# Docker Compose Setup (Development & Production)

This project uses **two Docker Compose configurations**:

- **Development** → runs on port `8000`
- **Production** → runs on port `8004`.

NGINX terminates HTTPS and forwards requests to the container.

---

# Project Structure

```
face_detection/
├ docker-compose.yaml
├ docker-compose.prod.yaml
├ Dockerfile
├ server.py
├ deepface_backup/
├ user_images/
├ extracted_faces/
└ temp/
```

---

### Run Development

```bash
docker compose up --build
```

Access locally:

```
http://localhost:8000
```

---

# Run Production

```bash
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build
```

The container will run:

```
host:8004 → container:8000
```

---

# NGINX Reverse Proxy

NGINX handles **HTTPS termination** and forwards requests.

Example routing:

| Public URL             | Internal Service |
| ---------------------- | ---------------- |
| https://server-ip:8003 | 127.0.0.1:8004   |

Example NGINX proxy rule:

```nginx
server {
    listen 8003 ssl;

    ssl_certificate path/to/crt;
    ssl_certificate_key path/to/key;

    location / {
        proxy_pass http://127.0.0.1:8004;
    }
}
```

---

# Important Notes

### DeepFace Models

DeepFace model weights are mounted from the host:

```
./deepface_backup → /root/.deepface/weights
```

This avoids downloading models every time the container starts.

---

### Image & Data Folders

The following folders are mounted so data persists outside the container:

```
user_images/
extracted_faces/
temp/
```

---

### Docker Ignore

Create `.dockerignore` to prevent large files from entering the build context:

```
.git
__pycache__
*.pyc
deepface_backup
user_images
extracted_faces
temp
```

This drastically reduces build time.

---

# Useful Commands

### Rebuild container

```bash
docker compose up --build
```

### Run in background

```bash
docker compose up -d
```

### Stop containers

```bash
docker compose down
```

### View logs

```bash
docker compose logs -f
```

---

# Deployment Workflow

Typical production deployment:

1. Pull latest code
2. Ensure model files exist
3. Run compose

```bash
git pull
docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build
```

---

# Access

```
https://<server-ip>:8004
```

Requests are forwarded by NGINX to the container running on port `8000`.
