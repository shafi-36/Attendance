# Deployment

This project is set up to deploy with Docker images published by GitHub Actions to GitHub Container Registry.

## 1. Push to GitHub

Commit and push the project to the `main` or `master` branch. The workflow at `.github/workflows/dockerize.yml` will build and publish:

- `ghcr.io/<owner>/<repo>-backend:latest`
- `ghcr.io/<owner>/<repo>-frontend:latest`

You can also run the workflow manually from the GitHub Actions tab.

## 2. Prepare the server

On your VPS or deployment machine, install Docker and Docker Compose.

Create a project folder:

```bash
mkdir -p attendance-system
cd attendance-system
```

Copy these files into that folder:

- `.env`
- `docker-compose.deploy.yml`

## 3. Set deployment image names

Edit `.env` on the server and add your actual GitHub owner/repo:

```env
BACKEND_IMAGE=ghcr.io/<owner>/<repo>-backend:latest
FRONTEND_IMAGE=ghcr.io/<owner>/<repo>-frontend:latest
```

Keep your SMTP, JWT, and MinIO settings in the same `.env` file.

## 4. Login to GitHub Container Registry

If the package is private:

```bash
docker login ghcr.io
```

Use your GitHub username and a GitHub token with package read permission.

If the package is public, login may not be needed.

## 5. Start the app

```bash
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d
```

Open:

- Frontend: `http://<server-ip>:8501`
- Backend API: `http://<server-ip>:8010/docs`
- MinIO console: `http://<server-ip>:9001`

## 6. Update after new changes

After pushing new changes and waiting for GitHub Actions to finish:

```bash
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d
```

