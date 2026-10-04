from __future__ import annotations

import requests


class WeatherService:
    """Servicio para obtener el clima del destino seleccionado."""

    @staticmethod
    def obtener_clima_por_destino(latitud: float, longitud: float):
        url = (
            'https://api.open-meteo.com/v1/forecast'
            f'?latitude={latitud}&longitude={longitud}'
            '&current=temperature_2m,weather_code&timezone=auto'
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        current = payload.get('current', {})
        return {
            'temperatura_c': current.get('temperature_2m'),
            'codigo': current.get('weather_code'),
            'unidad': payload.get('current_units', {}).get('temperature_2m', '°C'),
        }
