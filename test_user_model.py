"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows
import psycopg2.errors as psy2_E

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Test represent self function"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        user = User.query.filter_by(username="testuser").first()
        self.assertEqual(
            repr(user), f'<User #{user.id}: testuser, test@test.com>')

    def test_isfollowing(self):
        """Test is following function, does it work to identify whether or not a user is following
            another user"""

        u1 = User(
            email="test@test.com",
            username="testuser1",
            password="u1_PASSWORD"
        )

        u2 = User(
            email="test1@test.com",
            username="testuser2",
            password="u2_PASSWORD"
        )

        users = [u1, u2]
        db.session.add_all(users)
        db.session.commit()

        self.assertEqual(len(u1.following), 0)
        self.assertEqual(len(u2.followers), 0)

        follow = Follows(user_following_id=u1.id, user_being_followed_id=u2.id)
        db.session.add(follow)
        db.session.commit()
        self.assertEqual(u1.following[0].id, u2.id)
        self.assertEqual(u2.followers[0].id, u1.id)

    def test_signup(self):

        u = "newtestuser"
        em = "newuser@test.com"
        pw = "newuserPassword"
        img = "/static/images/default-pic.png"

        user = User.signup(username=u, email=em, password=pw, image_url=img)
        db.session.commit()

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "newtestuser")

    # def test_signup_fail(self):

    #     # No email
    #     with self.assertRaises(psy2_E.NotNullViolation):
    #         User.signup(username='testusr', email=None,
    #                     password='password', image_url=None)

    # def test_fail1(self):
    #     # Not unique email
    #     User.signup('testuser1', 'test@test.com', 'password', None)
    #     db.session.commit()

    # def test_fail2(self):
    #     with self.assertRaises(IntegrityError):
    #         User.signup('testusr2', 'test@test.com', 'password', None)
    #         db.session.commit()

    #     db.session.rollback()

    # def test_fail3(self):
    #     # Null username
    #     with self.assertRaises(psy2_E.NotNullViolation):
    #         User.signup(username=None, email='testing@test.com',
    #                     password='password', image_url=None)

    #     db.session.rollback()

    # def test_fail4(self):
    #     # Not unique username
    #     with self.assertRaises(IntegrityError):
    #         User.signup('testuser1', 'testing@test.com', 'password', None)

    def test_authenticate(self):
        """Testing User.authenticate"""
        u = "newtestuser"
        em = "newuser@test.com"
        pw = "newuserPassword"
        img = "/static/images/default-pic.png"

        user = User.signup(username=u, email=em, password=pw, image_url=img)
        db.session.commit()

        # Does it successfully return a user when given a valid username and password?
        auth_user = User.authenticate(username=u, password=pw)
        self.assertIsInstance(auth_user, User)

        # Does it return False if given an invalid password
        auth_user = User.authenticate(username=u, password="wrongpassword")
        self.assertEqual(auth_user, False)

        # Does it return False if given a wrong username
        auth_user = User.authenticate(username="not_a_valid_user", password=pw)
        self.assertEqual(auth_user, False)
