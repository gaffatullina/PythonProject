# MAMMAMIA Salon Services Bot

Welcome to the **MAMMAMIA Salon Services Bot** project! This Telegram bot helps users calculate the cost of salon services, offering a seamless experience for selecting and pricing beauty services.

---

## 🚀 Getting Started

### Prerequisites
Ensure you have the following installed on your system:
- **Git**
- **Docker** and **Docker Compose**

### Clone the Repository
To start, clone the project repository:
```bash
git clone git@github.com:gaffatullina/PythonProject.git
cd PythonProject
```

### Set Up Environment Variables
Create a `.env` file in the project directory with the following content:
```env
POSTGRES_DB=your_postgres_database
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
TOKEN="ADD YOUR BOT TOKEN HERE"
```
Replace the placeholder values with your own credentials.

---

## 🛠️ How to Run
To launch the bot, simply execute the following command in the project directory:
```bash
chmod +x ./build.sh
```

Before starting, make sure to stop any local **PostgreSQL** service running on your machine. Leaving it active might cause port conflicts with Docker.

