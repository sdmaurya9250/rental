# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from workers import asgi, WorkerEntrypoint
#
# app = FastAPI(title="Rental API")
#
# # Allow frontend to talk to backend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Later you can restrict this
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# @app.get("/")
# async def root():
#     return {"message": "Rental Backend is running on Cloudflare"}
#
# @app.get("/health")
# async def health():
#     return {"status": "ok"}
#
# # Required for Cloudflare Python Workers
# class Default(WorkerEntrypoint):
#     async def fetch(self, request):
#         return await asgi.fetch(app, request, self.env)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi, WorkerEntrypoint

# Changed imports (removed "app.")
from routes.auth import router as auth_router
from routes.health import router as health_router

app = FastAPI(title="RentPeople API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)