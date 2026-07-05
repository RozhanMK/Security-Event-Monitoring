# Security event monitoring using FastAPI

This is my first FastAPI project. I wanted to build something related to my favorite fields, such as IoT and computer security.

This project involves a user management system based on JWT. By registering, signing up, resetting passwords, etc., new events get created automatically.

Also, authorized users can create new events manually. Since I care about coding in a standard structure, I tried using [this repository](https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend) as a guide.

One of the features that makes this project unique among beginner FastAPI projects is that the dashboard shows live changes. This means that users can see new incoming events in real time without needing to refresh the page. The real-time feature is implemented using Redis Streams and WebSockets.

Furthermore, a rate limiter (based on IP) is implemented using Redis. I tried to avoid using polling in my rate limiter.

uv is used for package management, which I found to be a better option than pip. PostgreSQL and Redis are deployed using Docker Compose.

Start the database and Redis:

```bash
docker compose up -d
```

Run the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Run the frontend:

```bash
cd frontend
python -m http.server 5500
```

The code for the frontend was written by ChatGPT (because I'm not interested in frontend development). So unfortunately, the dashboard does not look very fancy. Sorry about that.
