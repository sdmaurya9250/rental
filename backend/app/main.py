# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from workers import asgi, WorkerEntrypoint
#
# from routes.auth import router as auth_router
# from routes.health import router as health_router
# from routes.profile import router as profile_router
#
# app = FastAPI(title="RentPeople API", version="1.0.0")
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# app.include_router(health_router)
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(profile_router, prefix="/api", tags=["Profile"])
#
#
# class Default(WorkerEntrypoint):
#     async def fetch(self, request):
#         return await asgi.fetch(app, request, self.env)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi, WorkerEntrypoint

from routes.auth import router as auth_router
from routes.health import router as health_router
from routes.profile import router as profile_router
from routes.upload import router as upload_router   # ← add this

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
app.include_router(profile_router, prefix="/api", tags=["Profile"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])   # ← add this


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)