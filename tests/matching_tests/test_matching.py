import pytest
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fftrack.database.models import Base


def get_test_engine():
    return create_engine('sqlite:///:memory:')


@pytest.fixture(scope="module")
def setup_database():
    from fftrack.database.models import create_database
    from fftrack.database.db_manager import DatabaseManager

    # Create a new engine instance for testing
    engine = get_test_engine()

    # Create tables
    Base.metadata.create_all(engine)

    # Create a new sessionmaker linked to the engine
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    connection = engine.connect()
    transaction = connection.begin()

    # Create new session
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


@pytest.fixture(scope="module")
def db_manager(setup_database):
    from fftrack.database.db_manager import DatabaseManager
    return DatabaseManager(session=setup_database)




@pytest.fixture(scope="module")
def matcher_instance(db_manager):
    # Initialising matcher and creates tables
    from fftrack.matching.matcher import Matcher
    matcher = Matcher(db_manager)
    create_test_database(db_manager)

    return matcher


def create_test_database(db_manager):
    # adds sample fingerprints to database
    db_manager.add_fingerprint("Test Song 1", '1234567890abcdefghij', 0)
    db_manager.add_fingerprint("Test Song 1", '1234567890abcdefghij', 1)
    db_manager.add_fingerprint("Test Song 1", '1234567890abcdefghij', 2)

    db_manager.add_fingerprint("Test Song 2", '1234567890abcdefghij', 4)
    db_manager.add_fingerprint("Test Song 2", '1234567890abcdefghij', 5)
    db_manager.add_fingerprint("Test Song 2", '1234567890abcdefghij', 6)


# Test find_matches function
def test_find_matches(matcher_instance):
    # Create some sample input data for testing
    sample_hashes = [('1234567890abcdefghij', 0), ('1234567890abcdefghij', 1), ('1234567890abcdefghij', 2)]

    # Call the function under test
    possible_matches, matches_per_song = matcher_instance.find_matches(sample_hashes)

    # Perform assertions to check if the function behaves as expected
    assert len(possible_matches) != 0  # Add expected length of possible matches
    assert len(matches_per_song) != 0  # Add expected length of matches per song


# Test align_matches function
def test_align_matches(matcher_instance):
    # Create some sample input data for testing
    matches = [('1234567890abcdefghij', 0),
               ('1234567890abcdefghij', 0),
               ('1234567890abcdefghij', 0),
               ('1234567890abcdefghij', 0),
               ('1234567890abcdefghij', 3),
               ('1234567890abcdefghij', 3)]

    # Call the function under test
    aligned_results = matcher_instance.align_matches(matches)

    # Perform assertions to check if the function behaves as expected
    assert len(aligned_results) != 0  # Add expected length of aligned results


# Test find_best_match function
def test_find_best_match(matcher_instance):
    # Create some sample input data for testing
    aligned_results = {"Test Song 1" : {'song_id' : "Test Song 1",
                                        'offset' : 0,
                                        'count': 3,
                                        'confidence': 0.19},
                       "Test Song 2": {'song_id': "Test Song 2",
                                       'offset': 3,
                                       'count': 10,
                                       'confidence': 0.77},
                       "Test Song 3": {'song_id': "Test Song 3",
                                       'offset': 0,
                                       'count': 15,
                                       'confidence': 0.83},
                       }

    # Call the function under test
    best_match = matcher_instance.find_best_match(aligned_results)

    # Perform assertions to check if the function behaves as expected
    assert isinstance(best_match, tuple)  # Ensure it returns a dictionary
    assert 'song_id' in best_match[1]  # Ensure it contains 'song_id' key
    assert 'offset' in best_match[1]  # Ensure it contains 'offset' key
    assert 'count' in best_match[1]  # Ensure it contains 'count' key
    assert 'confidence' in best_match[1]  # Ensure it contains 'confidence' key
