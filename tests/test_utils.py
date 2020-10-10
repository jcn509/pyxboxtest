"""Test the various utilities in :py:mod:`pyxboxtest._utils`"""
import time

import pytest
from pyxboxtest._utils import get_unused_ports, retry_every
from mock import Mock


def _all_unique(elements) -> bool:
    return len(elements) == len(set(elements))


@pytest.fixture(scope="function", autouse=True)
def mocked_time_sleep(mocker):
    """Don't make use wait for time.sleep"""
    mocker.patch("time.sleep")


@pytest.fixture(scope="function")
def mock_exception_with_call_count():
    mock = Mock()

    def raise_count(m):
        raise ValueError(f"Error ar try {m.call_count}")

    mock.side_effect = lambda m=mock: raise_count(m)
    return mock


class TestRetryEvery:
    """tests for :py:func:`~pyxboxtest.utils.retry_every`"""

    @pytest.mark.parametrize("max_tries", tuple(range(1, 4)))
    def test_max_retries_no_exception(self, max_tries):
        """Ensure that the function is called only once if it does not throw an exception"""
        callback = Mock()
        retry_every(callback, max_tries=max_tries)
        assert callback.call_count == 1, "callback called once if not throw exception"

    @pytest.mark.parametrize("max_tries", tuple(range(1, 4)))
    def test_max_retries_exception_every_time(
        self, max_tries, mock_exception_with_call_count
    ):
        """Ensure that the funtion is called max_tries times if it always throws an exception"""
        with pytest.raises(Exception, match=f"Error ar try {max_tries}"):
            retry_every(mock_exception_with_call_count, max_tries=max_tries)
        assert (
            mock_exception_with_call_count.call_count == max_tries
        ), "callback called max_tries_times if it throws an exception every time"

    @pytest.mark.parametrize("delay_before_retry", tuple(range(1, 4)))
    def test_correct_delay(self, delay_before_retry, mock_exception_with_call_count):
        """Ensure that sleep is called correctly when the callback throws an exception"""
        try:
            retry_every(
                mock_exception_with_call_count,
                max_tries=3,
                delay_before_retry=delay_before_retry,
            )
        except:
            pass  # Don't care about whether it really raises an exception or not here
        assert (
            time.sleep.call_count == 2
        ), "sleep called after each exception but the last"
        expected_args = (delay_before_retry,)
        assert all(
            call.args == expected_args for call in time.sleep.call_args_list
        ), "sleep called with the correct delay"

    @pytest.mark.parametrize("throws_exception_for", tuple(range(1, 4)))
    def test_max_retries_exception_n_times(self, throws_exception_for):
        """Ensure that the funtion is called n+1 times if it throws an exception the first n times"""
        callback = Mock()
        callback.side_effect = [
            Exception("Thrown an exception") for _ in range(throws_exception_for)
        ] + [None]
        retry_every(callback, max_tries=throws_exception_for + 3)
        assert callback.call_count == (
            throws_exception_for + 1
        ), "callback called until it does not throw an exception"


@pytest.mark.parametrize("number_of_ports", tuple(range(1, 4)))
class TestGetUnusedPorts:
    """tests for :py:func:`~pyxboxtest.utils.get_unused_ports`
    There is no mocking here to be sure that it actually works.
    """

    def test_num_ports(self, number_of_ports):
        """Ensures that the correct number of ports are returned"""
        ports = tuple(get_unused_ports(number_of_ports))
        assert len(ports) == number_of_ports, "correct number of ports"

    def test_ports_unique(self, number_of_ports):
        """Ensures that no two ports that are returned are the same"""
        ports = tuple(get_unused_ports(number_of_ports))
        assert _all_unique(ports), "All the ports are unique"

    def test_ports_are_ints(self, number_of_ports):
        """Ensure that all the ports are integers"""
        ports = tuple(get_unused_ports(number_of_ports))
        assert all(type(port) == int for port in ports), "All the ports are integers"
