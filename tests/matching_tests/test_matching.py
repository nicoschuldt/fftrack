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
    matcher = Matcher(db_manager, confidence_threshold=0.5, match_count_benchmark=0)
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
    matches = [('Test Song 1', 0),
               ('Test Song 3', 0),
               ('Test Song 1', 0),
               ('Test Song 2', 0),
               ('Test Song 1', 3),
               ('Test Song 2', 3)]
    matches_per_song = {'Test Song 1': 10,
                        'Test Song 2': 19,
                        'Test Song 3': 23}

    # Call the function under test
    aligned_results = matcher_instance.align_matches(matches, matches_per_song)

    # Perform assertions to check if the function behaves as expected
    assert aligned_results is not None  # Add expected length of aligned results


def test_confidence_by_score(matcher_instance):
    # Create some sample input data for testing
    aligned_results = {"Test Song 1": {'song_id': "Test Song 1",
                                       'offset': 0,
                                       'count': 3,
                                       'confidence': 0},
                       "Test Song 2": {'song_id': "Test Song 2",
                                       'offset': 3,
                                       'count': 10,
                                       'confidence': 0},
                       "Test Song 3": {'song_id': "Test Song 3",
                                       'offset': 0,
                                       'count': 15,
                                       'confidence': 0},
                       }
    matches_per_song = {'Test Song 1': 10,
                        'Test Song 2': 19,
                        'Test Song 3': 23}

    aligned_results = matcher_instance.confidence_by_score(aligned_results, matches_per_song)

    # Perform assertions to check if the function behaves as expected
    assert aligned_results['Test Song 1']['confidence'] != 0, "Calculating confidence failed for Test Song 1"
    assert aligned_results['Test Song 2']['confidence'] != 0, "Calculating confidence failed for Test Song 1"
    assert aligned_results['Test Song 3']['confidence'] != 0, "Calculating confidence failed for Test Song 1"


def test_confidence_by_matches(matcher_instance):
    # Create some sample input data for testing
    aligned_results = {"Test Song 1": {'song_id': "Test Song 1",
                                       'offset': 0,
                                       'count': 3,
                                       'confidence': 0},
                       "Test Song 2": {'song_id': "Test Song 2",
                                       'offset': 3,
                                       'count': 10,
                                       'confidence': 0},
                       "Test Song 3": {'song_id': "Test Song 3",
                                       'offset': 0,
                                       'count': 15,
                                       'confidence': 0},
                       }
    sum_matches = 35

    aligned_results = matcher_instance.confidence_by_matches(aligned_results, sum_matches)

    # Perform assertions to check if the function behaves as expected
    assert aligned_results['Test Song 1']['confidence'] >= 0, "Calculating confidence failed for Test Song 1"
    assert aligned_results['Test Song 2']['confidence'] >= 0, "Calculating confidence failed for Test Song 1"
    assert aligned_results['Test Song 3']['confidence'] >= 0, "Calculating confidence failed for Test Song 1"


# Test find_top_n_match function
def test_find_top_n_matches(matcher_instance):
    # Create some sample input data for testing
    aligned_results = {"Test Song 1": {'song_id': "Test Song 1",
                                       'offset': 0,
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
    top_matches = matcher_instance.find_top_n_matches(aligned_results, 2)

    # Perform assertions to check if the function behaves as expected
    assert len(top_matches) == 2, "Failed to retrieve top matches"


# Test find_best_match function
def test_find_best_match(matcher_instance):
    # Create some sample input data for testing
    top_matches = [("Test Song 3", {'song_id': "Test Song 3",
                                    'offset': 0,
                                    'count': 15,
                                    'confidence': 0.83}),
                   ("Test Song 2", {'song_id': "Test Song 2",
                                    'offset': 3,
                                    'count': 10,
                                    'confidence': 0.77})]

    # Call the function under test
    best_match = matcher_instance.find_best_match(top_matches)

    # Perform assertions to check if the function behaves as expected
    assert best_match is not None, "Failed to retrieve best match"


def test_get_best_match(matcher_instance):
    # Create some sample input data for testing
    sample_hashes = [('1234567890abcdefghij', 0), ('1234567890abcdefghij', 1), ('1234567890abcdefghij', 2)]

    # Call the function under test
    top_matches, best_match = matcher_instance.get_best_match(sample_hashes)

    # Perform assertions to check if the function behaves as expected
    assert len(top_matches) != 0, "No top matches found"
    assert best_match is not None, "No best match found"



