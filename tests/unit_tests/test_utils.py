"""Test the various utilities in :py:mod:`pyxboxtest._utils`"""
import time

from mock import Mock
import pytest

from pyxboxtest._utils import retry_every, UnusedPort


# Grouped into classes as a way to organise the tests
# pylint: disable=no-self-use


def _all_unique(elements) -> bool:
    """:returns: True exactly if all the elements are unique"""
    return len(elements) == len(set(elements))


@pytest.fixture(scope="function", autouse=True)
def mocked_time_sleep(mocker):
    """Don't make use wait for time.sleep"""
    mocker.patch("time.sleep")


@pytest.fixture(scope="function")
def mock_exception_with_call_count() -> Mock:
    """:returns: a mock function that raises an exception that includes the
    number of times is has been called
    """
    mock = Mock()

    def raise_count(mocked_function):
        """Raises an exception that includes the call count of mocked_function"""
        raise ValueError(f"Error ar try {mocked_function.call_count}")

    mock.side_effect = lambda m=mock: raise_count(m)
    return mock


class TestRetryEvery:
    """tests for :py:func:`~pyxboxtest.utils.retry_every`"""

    @pytest.mark.parametrize("max_tries", tuple(range(1, 4)))
    def test_max_retries_no_exception(self, max_tries: int):
        """Ensure that the function is called only once if it does not throw an exception"""
        callback = Mock()
        retry_every(callback, max_tries=max_tries)
        assert callback.call_count == 1, "callback called once if not throw exception"

    @pytest.mark.parametrize("max_tries", tuple(range(1, 4)))
    def test_max_retries_exception_every_time(
        self,
        max_tries: int,
        mock_exception_with_call_count,
    ):
        """Ensure that the funtion is called max_tries times if it always throws an exception"""
        with pytest.raises(Exception, match=f"Error ar try {max_tries}"):
            retry_every(mock_exception_with_call_count, max_tries=max_tries)
        assert (
            mock_exception_with_call_count.call_count == max_tries
        ), "callback called max_tries_times if it throws an exception every time"

    @pytest.mark.parametrize("delay_before_retry", tuple(range(1, 4)))
    def test_correct_delay(
        self,
        delay_before_retry: int,
        mock_exception_with_call_count,
    ):
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
            time.sleep.call_count  # pytype: disable=attribute-error # pylint: disable=no-member
            == 2
        ), "sleep called after each exception but the last"
        expected_args = (delay_before_retry,)
        assert all(
            call.args == expected_args
            for call in time.sleep.call_args_list  # pytype: disable=attribute-error # pylint: disable=no-member
        ), "sleep called with the correct delay"

    @pytest.mark.parametrize("throws_exception_for", tuple(range(1, 4)))
    def test_max_retries_exception_n_times(self, throws_exception_for: int):
        """Ensure that the funtion is called n+1 times if it throws an exception the first n times
        :param throws_exception_for: the number of calls for which it should throw an exception
        """
        callback = Mock()
        callback.side_effect = [
            Exception("Thrown an exception") for _ in range(throws_exception_for)
        ] + [None]
        retry_every(callback, max_tries=throws_exception_for + 3)
        assert callback.call_count == (
            throws_exception_for + 1
        ), "callback called until it does not throw an exception"


@pytest.mark.parametrize(
    "number_of_ports",
    tuple(range(1, 4000, 100)),
)
class TestUnusedPorts:
    """tests for :py:class:`~pyxboxtest.utils.UnusedPorts`
    There is no mocking here to be sure that it actually works.
    """

    def test_ports_unique(self, number_of_ports: int):
        """Ensures that no two ports that are returned are the same"""
        # For this test to work they must exist at the same time
        unused_ports = tuple(UnusedPort() for _ in range(number_of_ports))

        assert _all_unique(
            tuple(port.get_port_number() for port in unused_ports)
        ), "All the ports are unique"

    def test_ports_are_ints(self, number_of_ports):
        """Ensure that all the port numbers are integers"""
        unused_ports = tuple(UnusedPort() for _ in range(number_of_ports))

        assert all(
            isinstance(port.get_port_number(), int) for port in unused_ports
        ), "All the ports are integers"
