# Online Medical Report Management System

## Run locally
1. Install Python 3.11 or later.
2. Run `python -m pip install -r requirements.txt`.
3. Run `python app.py`.
4. Open `http://127.0.0.1:5000`.

## Run with Docker
```bash
docker build -t medical-report-app .
docker run -d --name medical-report-container -p 5000:5000 -v medical_uploads:/app/uploads medical-report-app
```
Open `http://localhost:5000`.

## Jenkins
Create a Jenkins Pipeline job, connect the GitHub repository, and configure it to use the repository's `Jenkinsfile`. The Jenkins agent needs Python and Docker installed and permission to run Docker commands.

## Kubernetes
Build and make the image available to the Kubernetes cluster, then run:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl get pods
kubectl get services
```
Open the service through the cluster node's address on port `30080`.

## Notes
This is an academic demonstration starter. For real medical data, add HTTPS, CSRF protection, strict authorization, audit logs, encrypted storage, backups, and a production database. SQLite and local container storage are not a production healthcare deployment.
