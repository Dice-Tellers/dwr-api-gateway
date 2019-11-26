import datetime

import flask_testing

from monolith.app import create_app
from monolith.database import User, db, Story
from monolith.urls import TEST_DB


class TestReaction(flask_testing.TestCase):
    app = None

    def create_app(self):
        global app
        app = create_app(TEST_DB)
        return app

    def setUp(self) -> None:
        with app.app_context():
            # user for login
            example = User()
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.email = 'example@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = True
            example.set_password('admin')
            db.session.add(example)
            db.session.commit()

            # user for login
            example = User()
            example.firstname = 'First'
            example.lastname = 'Exe'
            example.email = 'first@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = False
            example.set_password('first')
            db.session.add(example)
            db.session.commit()

            # user for login
            example = User()
            example.firstname = 'Second'
            example.lastname = 'Exe'
            example.email = 'second@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = False
            example.set_password('second')
            db.session.add(example)
            db.session.commit()

            # user for login
            example = User()
            example.firstname = 'First'
            example.lastname = 'What'
            example.email = 'what@example.com'
            example.dateofbirth = datetime.datetime(2020, 10, 5)
            example.is_admin = False
            example.set_password('what')
            db.session.add(example)
            db.session.commit()

            # reacted story
            test_story = Story()
            test_story.text = "Test story from admin user"
            test_story.author_id = 1
            test_story.is_draft = 0
            test_story.figures = "#admin#from#"
            db.session.add(test_story)
            db.session.commit()

            test_story = Story()
            test_story.text = "Test story from bubble sort"
            test_story.author_id = 1
            test_story.is_draft = 0
            test_story.figures = "#bubble#from#"
            db.session.add(test_story)
            db.session.commit()

    def test_search(self):
        # Search for an existing story
        self.client.get('http://127.0.0.1:5000/search?query=bubble')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 1)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)

        # Search for an existing story and an existing user
        self.client.get('http://127.0.0.1:5000/search?query=admin')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 1)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 1)

        # Search for two existing story
        self.client.get('http://127.0.0.1:5000/search?query=from')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 2)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)

        # Search for two users with same firstname
        self.client.get('http://127.0.0.1:5000/search?query=first')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 2)

        # Search for two users with same lastname
        self.client.get('http://127.0.0.1:5000/search?query=exe')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 2)

        # Search for not existing result
        self.client.get('http://127.0.0.1:5000/search?query=nowords')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)

        # Search malformed
        self.client.get('http://127.0.0.1:5000/search?=nowords')

        self.assert_template_used('search.html')
        self.assertEqual(len(self.get_context_variable('list_of_stories')), 0)
        self.assertEqual(len(self.get_context_variable('list_of_users')), 0)