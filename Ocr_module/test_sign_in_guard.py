"""Too many wrong passwords closes an account for a while
(sign_in_guard.py).

Five wrong passwords close it for a minute, five more for five minutes,
five more for ten, and ten is the longest it gets. A correct password
clears the count. Counting is per account, so one account being guessed
at cannot lock the rest of the clinic out.

No database and no clock-watching: the waiting time is moved on by
hand rather than by sleeping, so the tests stay fast.
"""
import unittest

import sign_in_guard


class SignInGuardTests(unittest.TestCase):
    def setUp(self):
        sign_in_guard.reset_all()
        self.email = "staff@clinic.test"

    def tearDown(self):
        sign_in_guard.reset_all()

    def _serve_the_wait(self, email):
        """Pretend the lock's time has passed."""
        with sign_in_guard._lock:
            sign_in_guard._state[email]["until"] = 0.0

    def _wrong(self, times, email=None):
        last = 0
        for _ in range(times):
            last = sign_in_guard.record_failure(email or self.email)
        return last

    def test_four_wrong_passwords_do_not_close_the_account(self):
        self.assertEqual(self._wrong(4), 0)
        self.assertEqual(sign_in_guard.seconds_locked(self.email), 0)

    def test_fifth_wrong_password_closes_it_for_a_minute(self):
        self.assertEqual(self._wrong(5), 60)
        self.assertGreater(sign_in_guard.seconds_locked(self.email), 0)

    def test_the_wait_grows_each_time(self):
        self.assertEqual(self._wrong(5), 60)
        self._serve_the_wait(self.email)
        self.assertEqual(self._wrong(5), 300)
        self._serve_the_wait(self.email)
        self.assertEqual(self._wrong(5), 600)

    def test_ten_minutes_is_as_long_as_it_gets(self):
        for expected in (60, 300, 600, 600, 600):
            self.assertEqual(self._wrong(5), expected)
            self._serve_the_wait(self.email)

    def test_the_right_password_clears_the_count(self):
        self._wrong(4)
        sign_in_guard.record_success(self.email)
        # The count started again, so four more are still allowed.
        self.assertEqual(self._wrong(4), 0)

    def test_one_account_being_guessed_does_not_lock_another(self):
        self._wrong(5)
        self.assertGreater(sign_in_guard.seconds_locked(self.email), 0)
        self.assertEqual(sign_in_guard.seconds_locked("someone.else@clinic.test"), 0)

    def test_the_same_account_in_any_case_is_the_same_account(self):
        self._wrong(5, "Staff@Clinic.Test")
        self.assertGreater(sign_in_guard.seconds_locked("staff@clinic.test"), 0)

    def test_an_empty_address_is_not_counted(self):
        self.assertEqual(sign_in_guard.record_failure(""), 0)
        self.assertEqual(sign_in_guard.seconds_locked(""), 0)

    def test_the_wait_is_said_in_words(self):
        self.assertEqual(sign_in_guard.describe_wait(60), "1 minute")
        self.assertEqual(sign_in_guard.describe_wait(300), "5 minutes")
        self.assertEqual(sign_in_guard.describe_wait(600), "10 minutes")


if __name__ == "__main__":
    unittest.main()
