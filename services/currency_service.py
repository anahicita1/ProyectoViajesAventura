from __future__ import annotations

import requests


class CurrencyService:
    """Servicio para convertir pesos chilenos a dólares estadounidenses."""

    @staticmethod
    def convertir_clp_a_usd(clp: int) -> float:
        if clp <= 0:
            return 0.0
        try:
            response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
            response.raise_for_status()
            payload = response.json()
            rates = payload.get('rates') or {}
            clp_to_usd = rates.get('CLP')
            if clp_to_usd is None:
                return round(clp / 900, 2)
            usd = clp / (1 / clp_to_usd)
            return round(usd, 2)
        except Exception:
            return round(clp / 900, 2)
