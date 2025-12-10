from unittest.mock import patch

from core.utils import calculate_delay


class TestCalculateDelay:
    def test_calculate_delay_structure(self):
        delay_1 = calculate_delay(1)
        assert delay_1 >= 4.0
        assert delay_1 < 5.0

        delay_3 = calculate_delay(3)
        assert delay_3 >= 16.0
        assert delay_3 < 17.0

    @patch("core.utils.random")
    def test_calculate_delay_fixed_jitter(self, mock_random):
        mock_random.uniform.return_value = 0.5
        delay = calculate_delay(2)
        assert delay == 8.5
