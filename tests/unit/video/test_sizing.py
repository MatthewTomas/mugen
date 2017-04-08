import pytest

import mugen.video.sizing as v_sizing
from mugen.video.sizing import Dimensions


@pytest.fixture
def dimensions_16_9():
    return Dimensions(1920, 1080)


@pytest.fixture
def dimensions_4_3():
    return Dimensions(720, 540)


@pytest.fixture
def list_of_dimensions():
    return [dimensions_16_9(), dimensions_4_3()]


@pytest.mark.parametrize("dimensions, desired_aspect_ratio, expected", [
    (dimensions_16_9(), 16/9, (1920, 1080)),
    (dimensions_16_9(), 4/3, (1440, 1080)),
    (dimensions_4_3(), 16/9, (720, 405))
])
def test_crop_dimensions_to_aspect_ratio(dimensions, desired_aspect_ratio, expected):
    assert v_sizing.crop_dimensions_to_aspect_ratio(dimensions, desired_aspect_ratio) == expected


@pytest.mark.parametrize("dimensions, desired_aspect_ratio, expected", [
    (dimensions_16_9(), 16/9, (0, 0, 1920, 1080)),
    (dimensions_16_9(), 4/3, (240, 0, 1680, 1080)),
    (dimensions_4_3(), 16/9, (0, 67.5, 720, 472.5))
])
def test_crop_coordinates_for_aspect_ratio(dimensions, desired_aspect_ratio, expected):
    assert v_sizing.crop_coordinates_for_aspect_ratio(dimensions, desired_aspect_ratio) == expected


@pytest.mark.parametrize("dimensions_list, default, expected", [
    (list_of_dimensions(), None, (1920, 1080)),
    ([], "default", "default")
])
def test_largest_width_and_height_for_dimensions(dimensions_list, default, expected):
    assert v_sizing.largest_width_and_height_for_dimensions(dimensions_list, default) == expected


@pytest.mark.parametrize("dimensions_list, desired_aspect_ratio, default, expected", [
    (list_of_dimensions(), 4/3, None, (1440, 1080)),
    ([], 16/9, "default", "default")
])
def test_largest_dimensions_for_aspect_ratio(dimensions_list, desired_aspect_ratio, default, expected):
    assert v_sizing.largest_dimensions_for_aspect_ratio(dimensions_list, desired_aspect_ratio, default) == expected
