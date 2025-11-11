"""
Модуль для записи Twitch стримов
"""
import subprocess
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import logging


class StreamRecorder:
    """Класс для записи стримов через streamlink"""

    # Доступные качества
    QUALITY_OPTIONS = [
        "best",
        "1080p60",
        "1080p",
        "720p60",
        "720p",
        "480p",
        "360p",
        "160p",
        "worst",
        "audio_only"
    ]

    def __init__(self, recordings_dir: str, logs_dir: str):
        self.recordings_dir = Path(recordings_dir)
        self.logs_dir = Path(logs_dir)
        self.active_recordings: Dict[str, subprocess.Popen] = {}

        # Настройка логирования
        self.logger = logging.getLogger(__name__)

    def _generate_filename(self, streamer: str, template: str) -> str:
        """Генерировать имя файла для записи"""
        now = datetime.now()

        replacements = {
            '{streamer}': streamer,
            '{date}': now.strftime('%Y-%m-%d'),
            '{time}': now.strftime('%H-%M-%S'),
            '{timestamp}': str(int(now.timestamp()))
        }

        filename = template
        for key, value in replacements.items():
            filename = filename.replace(key, value)

        return filename

    def start_recording(
        self,
        streamer: str,
        quality: str = "best",
        filename_template: str = "{streamer}_{date}_{time}.mp4"
    ) -> bool:
        """Начать запись стрима"""
        # Проверка что запись уже не идет
        if streamer in self.active_recordings:
            self.logger.warning(f"Запись {streamer} уже активна")
            return False

        # Генерация имени файла
        filename = self._generate_filename(streamer, filename_template)
        output_path = self.recordings_dir / filename

        # Создание URL
        stream_url = f"https://www.twitch.tv/{streamer}"

        # Команда streamlink
        cmd = [
            "streamlink",
            "--twitch-disable-ads",
            "--twitch-low-latency",
            stream_url,
            quality,
            "-o", str(output_path),
            "--retry-streams", "5",
            "--retry-max", "10"
        ]

        # Путь к лог файлу
        log_file_path = self.logs_dir / f"{streamer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        try:
            # Запуск процесса
            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )

            self.active_recordings[streamer] = {
                'process': process,
                'output_path': output_path,
                'log_path': log_file_path,
                'start_time': datetime.now(),
                'quality': quality
            }

            self.logger.info(f"Начата запись {streamer} в {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при запуске записи {streamer}: {e}")
            return False

    def stop_recording(self, streamer: str) -> bool:
        """Остановить запись стрима"""
        if streamer not in self.active_recordings:
            self.logger.warning(f"Активной записи {streamer} не найдено")
            return False

        recording = self.active_recordings[streamer]
        process = recording['process']

        try:
            # Корректная остановка процесса
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()

            # Ожидание завершения
            process.wait(timeout=10)

            self.logger.info(f"Запись {streamer} остановлена")
            del self.active_recordings[streamer]
            return True

        except subprocess.TimeoutExpired:
            # Принудительное завершение
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                process.kill()

            del self.active_recordings[streamer]
            self.logger.warning(f"Запись {streamer} принудительно остановлена")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при остановке записи {streamer}: {e}")
            return False

    def is_recording(self, streamer: str) -> bool:
        """Проверить идет ли запись"""
        if streamer not in self.active_recordings:
            return False

        recording = self.active_recordings[streamer]
        process = recording['process']

        # Проверка статуса процесса
        if process.poll() is not None:
            # Процесс завершен
            del self.active_recordings[streamer]
            return False

        return True

    def get_active_recordings(self) -> Dict[str, Dict]:
        """Получить список активных записей"""
        # Очистить завершенные записи
        finished = []
        for streamer, recording in self.active_recordings.items():
            if recording['process'].poll() is not None:
                finished.append(streamer)

        for streamer in finished:
            del self.active_recordings[streamer]

        return self.active_recordings.copy()

    def stop_all_recordings(self):
        """Остановить все активные записи"""
        streamers = list(self.active_recordings.keys())
        for streamer in streamers:
            self.stop_recording(streamer)

    def get_recording_info(self, streamer: str) -> Optional[Dict]:
        """Получить информацию о записи"""
        if streamer not in self.active_recordings:
            return None

        recording = self.active_recordings[streamer]

        # Получить размер файла
        file_size = 0
        if recording['output_path'].exists():
            file_size = recording['output_path'].stat().st_size

        # Время записи
        duration = datetime.now() - recording['start_time']

        return {
            'streamer': streamer,
            'quality': recording['quality'],
            'output_path': str(recording['output_path']),
            'log_path': str(recording['log_path']),
            'file_size': file_size,
            'duration': str(duration).split('.')[0],  # Убрать микросекунды
            'start_time': recording['start_time'].strftime('%Y-%m-%d %H:%M:%S')
        }
