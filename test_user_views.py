"""User view tests."""

# run these tests like:
#
# python -m unittest test_user_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

app.config['WTF_CSRF_ENABLED'] = False
# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


class UserViewsTests(TestCase):
    """Test all routes and user views"""

    def setUp(self):
        """Set up context and user for logged in tests"""
        self.app_context = app.app_context()
        self.app_context.push()

        Likes.query.delete()
        Follows.query.delete()
        Message.query.delete()
        User.query.delete()

        # Set up 3 users
        self.u1 = User.signup(
            username="testcaseuser",
            password="just_a_test",
            email="testcase@test.com",
            image_url=None
        )

        db.session.commit()

        self.u2 = User.signup(
            username="anothertester",
            password="testing!!",
            email="testcase1@test.com",
            image_url=None
        )

        self.u3 = User.signup(
            username="yetanothertester",
            password="testing!!",
            email="testcase2@test.com",
            image_url=None
        )

        db.session.commit()

        # Create a message for user 1
        self.msg = Message(
            text="A message from user 1",
            user_id=self.u1.id
        )

        db.session.add(self.msg)
        db.session.commit()

        # Set up a liked message for user1
        u2_like = Likes(
            user_id=self.u2.id,
            message_id=self.msg.id
        )
        db.session.add(u2_like)
        db.session.commit()

        # Set up u2 Following u1
        u2_Follow = Follows(
            user_being_followed_id=self.u1.id,
            user_following_id=self.u2.id
        )
        db.session.add(u2_Follow)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        with self.client:
            with self.client.session_transaction() as ses:
                if CURR_USER_KEY in ses:
                    del ses[CURR_USER_KEY]

        self.app_context.pop()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_signup(self):
        """Test sign up page"""
        with self.client as c:
            resp = c.get('/signup', follow_redirects=True)
            html = resp.get_data(as_text=True)
            # verify sign up form displays
            input = '<input class="form-control" id="username" name="username" placeholder="Username" required type="text" value="">'
            self.assertEqual(resp.status_code, 200)
            self.assertIn(input, html)

            # Submit a form to add a user and verify the redirect to / displays the new user
            data = {'username': 'newtestuser5', 'email': 'pytest@test.com',
                    'password': 'password', 'image_url': ''}
            post = c.post('/signup', data=data, follow_redirects=True)
            html = post.get_data(as_text=True)
            self.assertEqual(post.status_code, 200)
            self.assertIn('<p>@newtestuser5</p>', html)

    def test_login(self):
        """Test log in page"""
        with self.client as c:
            # verify log in form
            resp = c.get('/login', follow_redirects=True)
            html = resp.get_data(as_text=True)
            input = '<input class="form-control" id="username" name="username" placeholder="Username" required type="text" value="">'
            self.assertEqual(resp.status_code, 200)
            self.assertIn(input, html)

            # submit log in form, validate redirect with logged in user.
            post = dict(username=self.u1.username, password='just_a_test')
            resp1 = c.post('/login', data=post, follow_redirects=True)
            html1 = resp1.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 200)
            self.assertIn("Hello, testcaseuser", html1)

    def test_logout(self):
        """Test log out"""
        with self.client as c:
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u1.id

        resp = c.get('/logout', follow_redirects=True)
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Logout successful", html)

    def test_users(self):
        """Test app.route('/users')"""
        # User not logged in
        with self.client as c:
            resp = c.get('/users')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testcaseuser", html)
            self.assertIn('@anothertester', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)
            self.assertNotIn('Follow', html)

        # User logged in
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u2.id
            resp1 = c.get('/users')
            html1 = resp1.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 200)
            self.assertIn('Follow', html1)
            self.assertIn('New Message', html1)
            self.assertIn('Log out', html1)

    def test_user_detail(self):
        """Test app.route('/users/<int:user_id>')"""
        # User not logged in
        with self.client as c:
            resp = c.get(f'/users/{self.u3.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'@{self.u3.username}', html)
            self.assertNotIn(
                '<button class="btn btn-outline-primary">Follow</button>', html)
            self.assertNotIn('New Message', html)

        # User logged in
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u1.id

            resp1 = c.get(f'/users/{self.u3.id}')
            html1 = resp1.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 200)
            self.assertIn(f'@{self.u3.username}', html1)
            self.assertIn(
                '<button class="btn btn-outline-primary">Follow</button>', html1)
            self.assertIn('New Message', html1)

    def test_users_following(self):
        """Test app.route('/users/<int:user_id>/following')"""

        # no user logged in
        with self.client as c:
            resp = c.get(f'/users/{self.u2.id}/following',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f'@{self.u1.username}', html)
            self.assertNotIn('Unfollow', html)
            self.assertIn('Access unauthorized', html)

        # u2 logged in following u1
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u2.id

            resp = c.get(f'/users/{self.u2.id}/following')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'@{self.u1.username}', html)
            self.assertIn('Unfollow', html)

    def test_users_followers(self):
        """Test app.route('/users/<int:user_id>/followers')"""

        # no user logged in
        with self.client as c:
            resp = c.get(f'/users/{self.u1.id}/followers',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f'@{self.u2.username}', html)
            self.assertIn('Access unauthorized', html)

        # u1 logged with u2 following
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u1.id

            resp = c.get(f'/users/{self.u1.id}/followers')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'@{self.u2.username}', html)

    def test_add_followers(self):
        """Test app.route('/users/follow/<int:follow_id>', methods=['POST'])"""

        # no user logged in
        with self.client as c:
            resp = c.post(f'/users/follow/{self.u1.id}',
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u3 logged in to follow u2
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u3.id

            resp = c.post(f'/users/follow/{self.u2.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'@{self.u2.username}', html)
            self.assertIn('Unfollow', html)

    def test_stop_following(self):
        """Test app.route('/users/stop-following/<int:follow_id>', methods=['POST'])"""

        # no user logged in
        with self.client as c:
            resp = c.post(f'/users/stop-following/{self.u1.id}',
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u2 logged in, stops following u1
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u2.id

            resp = c.post(
                f'/users/stop-following/{self.u1.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f'@{self.u1.username}', html)

    def test_like_message(self):
        """Test app.route('/users/add_like/<int:message_id>', methods=['POST'])"""

        # no user logged in
        with self.client as c:
            resp = c.post(f'/users/add_like/{self.msg.id}',
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # establish follow for redirect
            fol = Follows(user_being_followed_id=self.u1.id,
                          user_following_id=self.u3.id)
            db.session.add(fol)
            db.session.commit()

        # u3 logged in to like msg1
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u3.id
            headers = {'Referer': '/'}
            resp = c.post(
                f'/users/add_like/{self.msg.id}', headers=headers, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<i class="fas fa-star" style="color: #ffff00;"></i>', html)

    def test_remove_like(self):
        """Test app.route('/users/remove_like/<int:message_id>', methods=['POST'])"""

        # no user logged in
        with self.client as c:
            resp = c.post(f'/users/remove_like/{self.msg.id}',
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u2 logged in to remove like for u1 msg
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u2.id

            headers = {'Referer': '/'}
            resp = c.post(f'/users/remove_like/{self.msg.id}', headers=headers,
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            page_html = '''<p>A message from user 1</p>\n        </div>\n        \n        <form method="POST" action="/users/add_like/9" id="messages-form">\n'''
            self.assertIn(page_html, html)

    def test_likes_detail(self):
        """Test app.route('/users/<int:user_id>/likes')"""

        # no user logged in
        with self.client as c:
            resp = c.get(f'/users/{self.u2.id}/likes',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u2 logged in
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u2.id

            resp = c.get(f'/users/{self.u2.id}/likes',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<i class="fas fa-star" style="color: #ffff00;"></i>', html)

    def test_profile(self):
        """Test app.route('/users/profile', methods=["GET", "POST"])"""

        # user not logged in get request
        with self.client as c:
            resp = c.get('/users/profile',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # user not logged in post request
            form_data = dict(username=self.u2.username, password='testing!!', image_url=None,
                             header_image_url=None, bio='Hey its me', email='testfail@test.com')
            resp = c.post('/users/profile', data=form_data,
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u1 logged in get request
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u1.id
            resp = c.get('/users/profile',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                '<h2 class="join-message">Edit Your Profile.</h2>', html)
            self.assertIn(
                '<input class="form-control" id="username" name="username" placeholder="Username:" required type="text" value="">', html)

        # u1 logged in post request with incorrect password submitted
            form_data = dict(
                username=self.u1.username,
                password='wrongpw',
                image_url=None,
                header_image_url=None,
                bio=None,
                email='tester1@test.com'
            )
            resp = c.post('/users/profile', data=form_data,
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'Invalid password for {self.u1.username}.', html)

        # u1 logged in, post request with correct password
            form_data.update({
                'password': 'just_a_test',
                'bio': 'Just a tester updating their bio'
            })
            resp = c.post('/users/profile', data=form_data,
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Just a tester updating their bio', html)

    def test_delete_user(self):
        """Test app.route('/users/delete', methods=["POST"])"""

        # no user logged in
        with self.client as c:
            resp = c.post('/users/delete',
                          follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<li><a href="/login">Log in</a></li>', html)

        # u3 logged in
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u3.id
            resp = c.post('users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(User.query.get(self.u3.id), None)
            self.assertIn(
                '<h2 class="join-message">Join Warbler today.</h2>', html)

    def test_home(self):
        """Test home page views for both logged out and logged in user"""

        # user not logged in
        with self.client as c:
            resp = c.get('/', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<li><a href="/signup">Sign up</a></li>', html)
            self.assertIn('<h4>New to Warbler?</h4>', html)

        # user logged in
            with c.session_transaction() as ses:
                ses[CURR_USER_KEY] = self.u1.id

            resp1 = c.get('/', follow_redirects=True)
            html = resp1.get_data(as_text=True)
            self.assertEqual(resp1.status_code, 200)
            self.assertIn("@testcaseuser", html)
