

# 🛡️ AI-Based Web Security Suite

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Cache-red?style=for-the-badge&logo=redis)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</p>

> **An AI-powered Web Security Platform that combines Vulnerability Scanning, Web Application Firewall (WAF), Real-Time Monitoring, AI-assisted Security Analysis, and Automated Reporting into a single dashboard.**

---

# 📖 Table of Contents

- Overview
- Features
- Tech Stack
- System Architecture
- Project Structure
- Installation
- Running the Project
- Docker Deployment
- Project Workflow
- Screenshots
- Demo Video
- Future Improvements
- Contributing
- License

---

# 📖 Overview

The **AI-Based Web Security Suite** is a modern full-stack cybersecurity platform designed to simplify web application security testing and monitoring.

The application integrates:

- 🔍 Automated Vulnerability Scanner
- 🤖 Google Gemini AI Security Analysis
- 🛡️ Web Application Firewall (WAF)
- 📊 Interactive Dashboard
- 📑 PDF Security Reports
- ⚡ Real-Time Monitoring
- 📡 WebSocket Notifications
- 🗄 PostgreSQL Database
- 🔄 Background Scan Processing using Celery & Redis

The objective is to provide developers and security professionals with an all-in-one solution for identifying, monitoring, and mitigating web security threats.

---

# ✨ Features

- ✅ User Authentication & Authorization
- ✅ Website Management
- ✅ Vulnerability Scanner
- ✅ SQL Injection Detection
- ✅ Cross-Site Scripting (XSS) Detection
- ✅ HTTP Security Header Analysis
- ✅ AI-Powered Vulnerability Explanation
- ✅ Automated Security Reports
- ✅ Web Application Firewall (WAF)
- ✅ Dashboard Analytics
- ✅ Scan History
- ✅ Real-Time Notifications
- ✅ Background Scan Execution
- ✅ PostgreSQL Storage
- ✅ REST API
- ✅ Swagger API Documentation

---

# 🛠 Tech Stack

## Backend

- FastAPI
- Python
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery
- Uvicorn

## Frontend

- React
- JavaScript
- HTML5
- CSS3
- Vite

## Artificial Intelligence

- Google Gemini API

## Security

- Web Application Firewall (WAF)
- Vulnerability Scanner
- Authentication & Authorization
- OWASP Security Checks

---

# 🏗 System Architecture

> Replace the image below with your architecture diagram.

<p align="center">
<img width="1536" height="1024" alt="system architecture" src="https://github.com/user-attachments/assets/b7c51e35-0775-4109-a739-c8564d4dc508" />
</p>

---

# 📂 Project Structure

```text
AI-Based-Web-Security-Suite/

│

├── backend/
│   ├── app/
│   ├── scanners/
│   ├── waf/
│   ├── reports/
│   ├── requirements.txt
│   └── run_waf.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── screenshots/
│
├── docker-compose.yml
│
├── README.md
│
└── LICENSE
```

---

# ⚙️ Installation & Setup

## Prerequisites

Install the following software before running the project:

- Python 3.11+
- Node.js (v18+)
- PostgreSQL
- Redis
- Git

---

## 📥 Clone Repository

```bash
git clone https://github.com/MohammedHabibQureshi/AI-Based-Web-Security-Suite.git

cd AI-Based-Web-Security-Suite
```

---

# 🚀 Initial Setup & Installation

## Backend Setup (Python Virtual Environment)

Open a terminal in the project root, navigate to the backend folder, create the virtual environment, and install dependencies:

```powershell
cd backend

python -m venv venv

.\venv\Scripts\activate

pip install -r requirements.txt
```

---

## Frontend Setup (Node.js / NPM)

Open another terminal in the project root, navigate to the frontend folder, and install package dependencies:

```powershell
cd frontend

npm install
```

---

# ▶️ Running the Suite Locally

Start **three separate terminals**.

---

## 🖥️ Terminal 1 – Start the Backend API Server

This service handles:

- Database ORM
- User Authentication
- Vulnerability Scanning
- WebSocket Broadcasts
- AI Processing

```powershell
cd backend

.\venv\Scripts\uvicorn.exe app.main:app --port 8000 --reload
```

### Backend API

```
http://localhost:8000
```

### Swagger Documentation

```
http://localhost:8000/docs
```

---

## 🛡️ Terminal 2 – Start the WAF Proxy Server

This service intercepts real-time HTTP requests, filters malicious traffic using signature-based rules, and forwards legitimate requests to target websites.

```powershell
cd backend

.\venv\Scripts\python.exe run_waf.py
```

### WAF Proxy

```
http://localhost:8080
```

---

## 💻 Terminal 3 – Start the React Frontend Dashboard

```powershell
cd frontend

npm run dev
```

### Frontend Dashboard

```
http://localhost:5173
```

---

# 🐳 Running via Docker Compose

If Docker is installed, the complete application stack (Frontend, Backend, PostgreSQL, Redis, etc.) can be launched with a single command.

### Step 1

Rename the environment file.

```powershell
copy .env.example .env
```

### Step 2

Build and start all containers.

```powershell
docker-compose up -d --build
```

Docker Compose automatically starts:

- FastAPI Backend
- React Frontend
- PostgreSQL
- Redis
- Celery Workers
- WAF Service

---

# 🌐 Default URLs

| Service | URL |
|----------|-----|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| WAF Proxy | http://localhost:8080 |

---

# 🔄 Project Workflow

```text
                    User
                      │
                      ▼
          React Frontend Dashboard
                      │
                      ▼
               FastAPI Backend
            ┌─────────┴─────────┐
            │                   │
            ▼                   ▼
 Vulnerability Scanner     Google Gemini AI
            │                   │
            └─────────┬─────────┘
                      ▼
              Security Analysis
                      │
                      ▼
             PostgreSQL Database
                      │
                      ▼
             PDF Report Generation

Incoming HTTP Traffic
          │
          ▼
   Web Application Firewall
          │
          ▼
     Target Web Application
```

---

# 📸 Project Screenshots

## 1️⃣ Login Page

![Login]<img width="911" height="750" alt="ss0" src="https://github.com/user-attachments/assets/d5050683-dc55-42bc-8db0-259621b503e2" />

---

## 2️⃣ Dashboard

![Dashboard](screenshots/dashboard.png)

---

## 3️⃣ Website Management

![Website](screenshots/websites.png)

---

## 4️⃣ Vulnerability Scanner

![Scanner](screenshots/scanner.png)

---

## 5️⃣ Scan Progress

![Progress](screenshots/progress.png)

---

## 6️⃣ AI Security Analysis

![AI Analysis](screenshots/ai-analysis.png)

---

## 7️⃣ Web Application Firewall

![WAF](screenshots/waf.png)

---

## 8️⃣ Security Reports

![Reports](screenshots/report.png)

---

## 9️⃣ Activity Logs

![Logs](screenshots/logs.png)

---

# 🎥 Project Demonstration

A complete walkthrough of the project is available below.

The demonstration covers:

- Project Overview
- Login
- Dashboard
- Website Management
- Vulnerability Scanning
- AI Analysis
- WAF Protection
- Report Generation
- Activity Logs

▶️ **Watch the Demo**

[![Watch Demo](screenshots/dashboard.png)](https://YOUR_VIDEO_LINK_HERE)

> Replace the above link with your YouTube or GitHub video URL.

---

# 🚀 Future Improvements

- Docker Deployment
- Kubernetes Support
- IDS/IPS Integration
- CVE Database Integration
- SIEM Integration
- Email Alerts
- Multi-user Roles
- Machine Learning Threat Detection
- Cloud Deployment (AWS/Azure)

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push to your branch.
5. Open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Mohammad Habib Qureshi**

B.Tech – Computer Science Engineering (IoT Specialization in Cybersecurity & Blockchain)

KL University

---

⭐ **If you found this project useful, don't forget to star the repository!**
