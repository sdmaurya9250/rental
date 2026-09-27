from fastapi import FastAPI
from workers import asgi, WorkerEntrypoint

app = FastAPI(title="Rental API")

@app.get("/")
async def root():
    return {"message": "Rental Backend is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Required for Cloudflare Python Workers
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)