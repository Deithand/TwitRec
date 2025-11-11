"""
Клиент для работы с Twitch API
"""
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class TwitchAPIClient:
    """Клиент для взаимодействия с Twitch API"""

    API_BASE_URL = "https://api.twitch.tv/helix"
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None

    def _get_access_token(self) -> str:
        """Получить access token"""
        # Проверить существующий токен
        if self.access_token and self.token_expires:
            if datetime.now() < self.token_expires:
                return self.access_token

        # Получить новый токен
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        response = requests.post(self.TOKEN_URL, params=params)
        response.raise_for_status()

        data = response.json()
        self.access_token = data['access_token']

        # Установить время истечения (с запасом в 60 секунд)
        expires_in = data.get('expires_in', 3600)
        self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

        return self.access_token

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API запросов"""
        return {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self._get_access_token()}'
        }

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        url = f"{self.API_BASE_URL}/users"
        params = {'login': username}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            if data['data']:
                return data['data'][0]
            return None
        except requests.RequestException as e:
            print(f"Ошибка получения информации о пользователе: {e}")
            return None

    def is_stream_live(self, username: str) -> bool:
        """Проверить идет ли стрим"""
        stream_info = self.get_stream_info(username)
        return stream_info is not None

    def get_stream_info(self, username: str) -> Optional[Dict]:
        """Получить информацию о стриме"""
        url = f"{self.API_BASE_URL}/streams"
        params = {'user_login': username}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            if data['data']:
                return data['data'][0]
            return None
        except requests.RequestException as e:
            print(f"Ошибка получения информации о стриме: {e}")
            return None

    def get_channel_info(self, username: str) -> Optional[Dict]:
        """Получить информацию о канале"""
        user_info = self.get_user_info(username)
        if not user_info:
            return None

        url = f"{self.API_BASE_URL}/channels"
        params = {'broadcaster_id': user_info['id']}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            if data['data']:
                return data['data'][0]
            return None
        except requests.RequestException as e:
            print(f"Ошибка получения информации о канале: {e}")
            return None

    def search_channels(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск каналов по запросу"""
        url = f"{self.API_BASE_URL}/search/channels"
        params = {'query': query, 'first': limit}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])
        except requests.RequestException as e:
            print(f"Ошибка поиска каналов: {e}")
            return []
