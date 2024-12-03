from utils import get_antenna_IGS_code


def test_get_antenna_IGS_code():
    assert get_antenna_IGS_code('LEIAR20 NONE') == 'LEIAR20         NONE'
