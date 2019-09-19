import pytest


class BaseDB(object):
    @pytest.fixture(autouse=True)
    def _prepare(self, session_fixture):
        self.session = session_fixture

    def teardown_method(self):
        self.session.rollback()
