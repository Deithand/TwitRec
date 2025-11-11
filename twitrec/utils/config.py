"""
Модуль управления конфигурацией TwitRec
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class Config:
    """Класс для управления конфигурацией приложения"""

    def __init__(self):
        self.config_dir = Path.home() / ".twitrec"
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"

        # Создаем директорию если не существует
        self.config_dir.mkdir(exist_ok=True)

        # Загружаем переменные окружения
        if self.env_file.exists():
            load_dotenv(self.env_file)

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Загрузить конфигурацию из файла"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Дефолтная конфигурация
        return {
            "recordings_dir": str(Path.cwd() / "recordings"),
            "logs_dir": str(Path.cwd() / "logs"),
            "default_quality": "best",
            "check_interval": 60,  # секунды
            "filename_template": "{streamer}_{date}_{time}.mp4"
        }

    def save_config(self):
        """Сохранить конфигурацию в файл"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_twitch_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Получить Twitch API креденшалы"""
        client_id = os.getenv("TWITCH_CLIENT_ID")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        return client_id, client_secret

    def set_twitch_credentials(self, client_id: str, client_secret: str):
        """Установить Twitch API креденшалы"""
        env_content = f"""# Twitch API Credentials
TWITCH_CLIENT_ID={client_id}
TWITCH_CLIENT_SECRET={client_secret}
"""
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)

        # Перезагрузить переменные окружения
        load_dotenv(self.env_file, override=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение из конфигурации"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Установить значение в конфигурации"""
        self.config[key] = value
        self.save_config()

    def ensure_directories(self):
        """Убедиться что все необходимые директории существуют"""
        recordings_dir = Path(self.get("recordings_dir"))
        logs_dir = Path(self.get("logs_dir"))

        recordings_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
