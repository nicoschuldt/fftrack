from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint, Index, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base class for our models
Base = declarative_base()


class Song(Base):
    """
    Represents a song in the database.

    Attributes:
        song_id: A unique identifier for the song.
        title: The title of the song.
        artist: The artist or band who performed the song.
        album: The album on which the song appears.
        release_date: The release date of the song.
    """
    __tablename__ = 'songs'

    song_id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String)
    release_date = Column(Date)
    youtube_link = Column(String)

    fingerprints = relationship('Fingerprint', back_populates='song')


class Fingerprint(Base):
    """
    Represents an audio fingerprint in the database.

    Attributes:
        fingerprint_id: A unique identifier for the fingerprint.
        song_id: The ID of the song this fingerprint belongs to.
        fingerprint: The fingerprint data.
    """
    __tablename__ = 'fingerprints'
    __table_args__ = (
        UniqueConstraint('song_id', 'offset', 'hash', name='_song_hash_offset_uc'),
        Index('idx_song_hash', 'hash'),
    )

    fingerprint_id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False)
    hash = Column(String(20), nullable=False, index=True)
    offset = Column(Integer, nullable=False)

    song = relationship('Song', back_populates='fingerprints')


# Database connection URL
DATABASE_URL = "sqlite:///fftrack.db"

engine = create_engine(DATABASE_URL, echo=False)  # Set echo=False for prod


def create_database():
    """
    Creates the database tables based on the models.
    """
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_database()
