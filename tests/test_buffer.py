import pytest

from ODEAudio.utility.buffer import Buffer


def test_init():
    buffer = Buffer(30)
    assert len(buffer) == 0


def test_resize():
    buffer = Buffer(30)

    for i in range(50):
        buffer.append(i)

    assert len(buffer) <= (30 * buffer.append_threshold), "Buffer oversize"

    assert buffer[-1] == 49, "Last element index incorrect"
    assert buffer[40] == 40, "Indexing not updated by resize"

    buffer.extend(list(range(50)))

    assert len(buffer) <= 30, "Buffer oversize"

    assert buffer[-1] == 49, "Last element index incorrect"
    assert buffer[90] == 40, "Indexing not updated by resize"


def test_slize():
    buffer = Buffer(30)

    buffer.extend(list(range(50)))

    assert buffer[30:35] == [30, 31, 32, 33, 34]


def test_index_dropped():
    buffer = Buffer(30)

    buffer.extend(list(range(50)))

    with pytest.raises(IndexError):
        x = buffer[5]