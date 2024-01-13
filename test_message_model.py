"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follows

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


class MessageModelTests(TestCase):

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

    def test_create_message(self):
        """Does message model create messages"""
        u = User.query.filter_by(username="testuser").first()

        msg = Message(text="test message", user_id=u.id)
        db.session.add(msg)
        db.session.commit()

        self.assertIsInstance(msg, Message)
        self.assertEqual("test message", msg.text)

    def test_message_user_relationship(self):
        """Does the db model work to associate messages to users"""
        u = User.query.filter_by(username="testuser").first()

        msg = Message(text="test message", user_id=u.id)
        db.session.add(msg)
        db.session.commit()

        update_u = User.query.get(u.id)
        self.assertIsInstance(update_u.messages[0], Message)
        self.assertEqual(u.messages[0].text, "test message")
