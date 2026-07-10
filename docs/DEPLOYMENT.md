# RiskLens AI — Deployment Guide

This guide covers everything from a 2-minute local demo (for interviews) to a
containerized, MySQL-backed production-style deployment.

---

## 1. Local Demo Mode (SQLite, zero config)

Best for: interviews, portfolio walkthroughs, quick recruiter demos.

```bash
cd RiskLens_AI
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # DB_ENGINE=sqlite by default
python -m src.ml.train        # trains LR / RF / XGBoost, ~30-60s
streamlit run src/app.py
```

Open **http://localhost:8501**. Data persists to `data/risklens.db` (SQLite file)
between runs — delete it to reset the demo.

---

## 2. Production Mode (MySQL)

### 2.1 Provision MySQL

Any MySQL 8.0+ instance works: local install, Docker container, AWS RDS,
Azure Database for MySQL, or GCP Cloud SQL.

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed_data.sql     # optional demo rows
```

### 2.2 Configure environment

`.env`:
```
DB_ENGINE=mysql
MYSQL_HOST=<your-host>
MYSQL_PORT=3306
MYSQL_USER=<your-user>
MYSQL_PASSWORD=<your-password>
MYSQL_DATABASE=risklens_ai
```

### 2.3 Train and run

```bash
pip install -r requirements.txt
python -m src.ml.train
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 3. Docker Deployment

**Dockerfile** (place at project root):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m src.ml.train

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**docker-compose.yml** (app + MySQL):

```yaml
version: "3.9"
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: risklens_ai
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/1-schema.sql
      - ./database/seed_data.sql:/docker-entrypoint-initdb.d/2-seed.sql
    ports:
      - "3306:3306"

  app:
    build: .
    environment:
      DB_ENGINE: mysql
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: rootpass
      MYSQL_DATABASE: risklens_ai
    depends_on:
      - mysql
    ports:
      - "8501:8501"
```

```bash
docker compose up --build
```

---

## 4. Cloud Deployment Options

| Platform | Notes |
|---|---|
| **Streamlit Community Cloud** | Easiest for a public portfolio link. Use `DB_ENGINE=sqlite` (ephemeral) or point to a hosted MySQL (e.g., PlanetScale, AWS RDS) via `st.secrets`. |
| **AWS (ECS/Fargate + RDS MySQL)** | Production-representative: containerize with the Dockerfile above, RDS for MySQL, ALB in front of Streamlit. |
| **Azure App Service + Azure MySQL** | Similar pattern; App Service can run the Docker image directly. |
| **Render / Railway** | Quick managed deploy from the Dockerfile, add a managed MySQL add-on. |

---

## 5. Operational Notes

- **Retraining cadence**: In production, retrain `python -m src.ml.train` on a
  schedule (e.g., monthly) as new loan performance data becomes available, and
  version `models/best_model.joblib` (e.g., in S3 with a timestamped key).
- **Secrets**: Never commit `.env`. Use your platform's secret manager
  (AWS Secrets Manager, Azure Key Vault, Streamlit `st.secrets`) in production.
- **Monitoring**: `audit_logs` table gives a lightweight activity trail; for real
  production use, pair with structured logging (e.g., to CloudWatch/Datadog) and
  model-performance drift monitoring (PSI/CSI on key features over time).
- **Backups**: Schedule regular MySQL backups (mysqldump/RDS automated snapshots)
  since `customers`, `loan_applications`, and `predictions` are the system of
  record for lending decisions.
