from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fftrack.database.models import Base


def get_test_engine():
    # to avoid modifying the actual database
    return create_engine('sqlite:///:memory:')


@pytest.fixture(scope="function")
def setup_database():
    # Create a new engine instance for testing
    engine = get_test_engine()

    # Create tables
    Base.metadata.create_all(engine)

    # Create a new sessionmaker linked to the engine
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    connection = engine.connect()
    transaction = connection.begin()

    # Create a new session
    session = TestSession(bind=connection)

    # Begin a nested transaction to ensure that the session is rolled back
    #  after the test
    session.begin_nested()

    # This ensures that the session is rolled back at the end of the test
    @pytest.fixture(scope="function", autouse=True)
    def session_rollback():
        yield
        session.rollback()

    # Yield the session for the test to use
    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()

    # Drop all tables after the test run
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_manager(setup_database):
    # New DatabaseManager instance using the setup_database session
    from fftrack.database.db_manager import DatabaseManager
    return DatabaseManager(session=setup_database)


def test_add_song(db_manager):
    """
    test if the song is added correctly to the database
    """
    song_id = db_manager.add_song("Test Song (pt)", "Test Artist",
                                  "Test Album", "2020-01-01")
    assert song_id is not None


def test_add_fingerprint(db_manager):
    """
    Test if the fingerprint is added correctly to the database.
    """
    song_id = db_manager.add_song("Test Song 2 (pt)", "Test Artist", "Test Album", "2020-01-01")
    # Example hash data and offset for the test
    example_hash_data = '1234567890abcdefghij'
    example_offset = 42  # Example offset
    assert db_manager.add_fingerprint(song_id, example_hash_data, example_offset) is True


def test_get_song_by_id(db_manager):
    """
    Test if the song is retrieved correctly from the database.
    """
    song_id = db_manager.add_song("Test Song (pt)", "Test Artist",
                                  "Test Album", "2020-01-01")
    song = db_manager.get_song_by_id(song_id)
    assert song.title == "Test Song (pt)"
    assert song.artist == "Test Artist"
    assert song.album == "Test Album"
    assert song.release_date == datetime.strptime("2020-01-01", "%Y-%m-%d").date()


def test_get_fingerprint_by_hash(db_manager):
    """
    Test if fingerprints are retrieved correctly from the database by hash.
    """
    song_id = db_manager.add_song("Test Song 3 (pt)", "Test Artist", "Test Album", "2020-01-01")
    # Assuming the hash data and offset are the same as in the add fingerprint test
    example_hash_data = '1234567890abcdefghij'
    example_offset = 42
    db_manager.add_fingerprint(song_id, example_hash_data, example_offset)

    matching_fingerprints = db_manager.get_fingerprint_by_hash(example_hash_data)
    assert len(matching_fingerprints) == 1
    assert matching_fingerprints[0] == (song_id, example_offset)
