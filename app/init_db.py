from .database import engine
from .models.base import Base

def init():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init()