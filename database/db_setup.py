from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()


class UserPreference(Base):
    """Preferensi user dari feedback (like/dislike)."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100))
    feedback_type = Column(String(10))          # like / dislike
    outfit_style = Column(String(50))
    outfit_items = Column(Text)
    reason = Column(Text, nullable=True)
    tanggal = Column(DateTime, default=datetime.now)


class SearchHistory(Base):
    """Riwayat pencarian untuk analisis."""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100))
    prompt = Column(Text)
    parsed_occasion = Column(String(50))
    parsed_style = Column(String(50))
    parsed_budget = Column(Float, nullable=True)
    result_summary = Column(Text)
    tanggal = Column(DateTime, default=datetime.now)


def init_db(db_url: str = "sqlite:///database/fashion.db"):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


if __name__ == "__main__":
    engine, Session = init_db()
    print("Database berhasil dibuat!")
