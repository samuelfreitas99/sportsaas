from app.db.session import engine
from app.db.base import Base

def main():
    Base.metadata.create_all(bind=engine)
    print("OK - schema created via SQLAlchemy create_all()")

if __name__ == "__main__":
    main()
