from conlog.elegant import AtLeast, AtMost, Unknown


def test_bounds():
    assert Unknown() + 1 == Unknown()
    assert Unknown() + AtMost(0) == Unknown()
    assert Unknown() + AtLeast(0) == Unknown()
    assert AtMost(0) + Unknown() == Unknown()
    assert AtLeast(0) + Unknown() == Unknown()

    assert Unknown() - 1 == Unknown()
    assert Unknown() - AtMost(0) == Unknown()
    assert Unknown() - AtLeast(0) == Unknown()
    assert AtMost(0) - Unknown() == Unknown()
    assert AtLeast(0) - Unknown() == Unknown()

    assert AtMost(1) + AtMost(2) == AtMost(3)
    assert AtMost(1) + AtLeast(2) == Unknown()
    assert AtMost(1) + 2 == AtMost(3)
    assert AtMost(1) - AtMost(2) == Unknown()
    assert AtMost(1) - AtLeast(2) == AtMost(-1)
    assert AtMost(1) - 2 == AtMost(-1)

    assert AtMost(2) + AtMost(1) == AtMost(3)
    assert AtLeast(2) + AtMost(1) == Unknown()
    assert 2 + AtMost(1) == AtMost(3)
    assert AtMost(2) - AtMost(1) == Unknown()
    assert AtLeast(2) - AtMost(1) == AtLeast(1)
    assert 2 - AtMost(1) == AtLeast(1)

    assert AtLeast(1) + AtLeast(2) == AtLeast(3)
    assert AtLeast(1) + AtMost(2) == Unknown()
    assert AtLeast(1) + 2 == AtLeast(3)
    assert AtLeast(1) - AtLeast(2) == Unknown()
    assert AtLeast(1) - AtMost(2) == AtLeast(-1)
    assert AtLeast(1) - 2 == AtLeast(-1)

    assert AtLeast(2) + AtLeast(1) == AtLeast(3)
    assert AtMost(2) + AtLeast(1) == Unknown()
    assert 2 + AtLeast(1) == AtLeast(3)
    assert AtLeast(2) - AtLeast(1) == Unknown()
    assert AtMost(2) - AtLeast(1) == AtMost(1)
    assert 2 - AtLeast(1) == AtMost(1)
