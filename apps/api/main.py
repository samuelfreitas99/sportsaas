from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, organizations, games, ledger, org_members, billing, users, guests, finance, internal_billing
#from app.db.session import engine
#from app.db.base_class import Base
#import app.db.base  # garante que os models foram importados


app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(organizations.router, prefix="/api/v1/orgs", tags=["orgs"])
app.include_router(org_members.router, prefix="/api/v1", tags=["org_members"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(guests.router, prefix="/api/v1", tags=["guests"])
app.include_router(games.router, prefix="/api/v1", tags=["games"])
app.include_router(ledger.router, prefix="/api/v1", tags=["ledger"])
app.include_router(finance.router, prefix="/api/v1", tags=["finance"])
app.include_router(internal_billing.router, prefix="/api/v1", tags=["internal"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Sport SaaS API"}

#@app.on_event("startup")
#def on_startup():
#    Base.metadata.create_all(bind=engine)
