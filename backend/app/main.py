from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi, WorkerEntrypoint

app = FastAPI(title="Rental API")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later you can restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Rental Backend is running on Cloudflare"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Required for Cloudflare Python Workers
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)