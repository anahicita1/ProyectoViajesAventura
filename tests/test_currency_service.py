from unittest.mock import Mock, patch

from services.currency_service import CurrencyService


def test_convertir_clp_a_usd_divide_por_clp_por_dolar():
    response = Mock()
    response.json.return_value = {'rates': {'CLP': 950}}

    with patch('services.currency_service.requests.get', return_value=response):
        assert CurrencyService.convertir_clp_a_usd(100_000) == 105.26