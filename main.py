#!/usr/bin/env python3
"""
TwitRec - Twitch Stream Recorder
Главный файл приложения
"""
import sys
import time
import signal
import logging
import json
import threading
from pathlib import Path
from datetime import datetime

from twitrec.utils.config import Config
from twitrec.api.twitch_client import TwitchAPIClient
from twitrec.recorder.stream_recorder import StreamRecorder
from twitrec.ui.cli_interface import CLIInterface


class TwitRec:
    """Основной класс приложения TwitRec"""

    def __init__(self):
        self.config = Config()
        self.ui = CLIInterface()
        self.recorder: StreamRecorder = None
        self.twitch_client: TwitchAPIClient = None
        self.background_thread = None
        self.running = False
        self.watched_streamers = []

        # Настройка логирования
        self._setup_logging()

        # Обработка сигналов для корректного завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self):
        """Настройка логирования"""
        log_dir = Path(self.config.get("logs_dir"))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"twitrec_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.ui.show_warning("Получен сигнал завершения, останавливаю записи...")
        self.running = False
        if self.recorder:
            self.recorder.stop_all_recordings()
        sys.exit(0)

    def _initialize_api_client(self) -> bool:
        """Инициализация API клиента"""
        client_id, client_secret = self.config.get_twitch_credentials()

        if not client_id or not client_secret:
            self.ui.show_warning("Twitch API креденшалы не настроены!")
            self.ui.show_info("Для работы приложения нужны Client ID и Client Secret")
            self.ui.show_info("Получить их можно на https://dev.twitch.tv/console/apps")

            if self.ui.confirm("Хотите настроить сейчас?"):
                client_id = self.ui.get_input("Client ID")
                client_secret = self.ui.get_input("Client Secret")

                self.config.set_twitch_credentials(client_id, client_secret)
                self.ui.show_success("Креденшалы сохранены!")
            else:
                return False

        try:
            self.twitch_client = TwitchAPIClient(client_id, client_secret)
            # Тест соединения
            self.twitch_client._get_access_token()
            return True
        except Exception as e:
            self.ui.show_error(f"Ошибка инициализации API клиента: {e}")
            return False

    def _initialize_recorder(self):
        """Инициализация рекордера"""
        self.config.ensure_directories()

        self.recorder = StreamRecorder(
            recordings_dir=self.config.get("recordings_dir"),
            logs_dir=self.config.get("logs_dir")
        )

    def start_recording_action(self):
        """Действие: начать запись"""
        streamer = self.ui.get_streamer_name()
        if not streamer:
            self.ui.show_error("Имя стримера не может быть пустым")
            return

        # Проверить что стрим онлайн
        self.ui.show_loading("Проверка статуса стрима")

        if not self.twitch_client.is_stream_live(streamer):
            self.ui.show_warning(f"Стрим {streamer} сейчас не онлайн")
            if not self.ui.confirm("Начать запись при появлении онлайн?"):
                return

            # Добавить в список отслеживаемых
            if streamer not in self.watched_streamers:
                self.watched_streamers.append(streamer)
                self._save_watched_streamers()
                self.ui.show_success(f"Стример {streamer} добавлен в список отслеживания")
            return

        # Получить информацию о стриме
        stream_info = self.twitch_client.get_stream_info(streamer)
        if stream_info:
            self.ui.show_stream_info(stream_info)

        # Выбор качества
        quality = self.ui.select_quality(StreamRecorder.QUALITY_OPTIONS)

        # Начать запись
        success = self.recorder.start_recording(
            streamer=streamer,
            quality=quality,
            filename_template=self.config.get("filename_template")
        )

        if success:
            self.ui.show_success(f"Запись {streamer} начата! Качество: {quality}")
        else:
            self.ui.show_error(f"Не удалось начать запись {streamer}")

    def stop_recording_action(self):
        """Действие: остановить запись"""
        active = self.recorder.get_active_recordings()

        if not active:
            self.ui.show_warning("Нет активных записей")
            return

        self.ui.show_active_recordings({
            streamer: self.recorder.get_recording_info(streamer)
            for streamer in active.keys()
        })

        streamer = self.ui.get_streamer_name()
        if not streamer:
            return

        if self.recorder.stop_recording(streamer):
            self.ui.show_success(f"Запись {streamer} остановлена")
        else:
            self.ui.show_error(f"Не удалось остановить запись {streamer}")

    def show_active_recordings_action(self):
        """Действие: показать активные записи"""
        active = self.recorder.get_active_recordings()

        if not active:
            self.ui.show_info("Нет активных записей")
            return

        recordings_info = {
            streamer: self.recorder.get_recording_info(streamer)
            for streamer in active.keys()
        }

        self.ui.show_active_recordings(recordings_info)

    def search_channels_action(self):
        """Действие: поиск каналов"""
        query = self.ui.get_input("Введите запрос для поиска")

        if not query:
            return

        self.ui.show_loading("Поиск каналов")
        channels = self.twitch_client.search_channels(query, limit=20)

        self.ui.show_search_results(channels)

    def show_channel_info_action(self):
        """Действие: показать информацию о канале"""
        streamer = self.ui.get_streamer_name()
        if not streamer:
            return

        self.ui.show_loading("Получение информации")

        # Информация о канале
        channel_info = self.twitch_client.get_channel_info(streamer)
        if channel_info:
            self.ui.show_channel_info(channel_info)

        # Проверка статуса стрима
        stream_info = self.twitch_client.get_stream_info(streamer)
        if stream_info:
            self.ui.show_info("🔴 Стрим сейчас ОНЛАЙН")
            self.ui.show_stream_info(stream_info)
        else:
            self.ui.show_info("⚫ Стрим сейчас ОФФЛАЙН")

    def settings_action(self):
        """Действие: настройки"""
        while True:
            self.ui.console.print("\n[bold cyan]⚙️  Настройки:[/]")
            self.ui.console.print(f"1. Директория записей: [yellow]{self.config.get('recordings_dir')}[/]")
            self.ui.console.print(f"2. Качество по умолчанию: [yellow]{self.config.get('default_quality')}[/]")
            self.ui.console.print(f"3. Интервал проверки: [yellow]{self.config.get('check_interval')}с[/]")
            self.ui.console.print(f"4. Шаблон имени файла: [yellow]{self.config.get('filename_template')}[/]")
            self.ui.console.print("5. Изменить Twitch API креденшалы")
            self.ui.console.print("6. Вернуться в главное меню")

            choice = self.ui.get_input("Выберите пункт", "6")

            if choice == "1":
                new_dir = self.ui.get_input("Новая директория", self.config.get('recordings_dir'))
                self.config.set('recordings_dir', new_dir)
                self.ui.show_success("Настройка сохранена")

            elif choice == "2":
                quality = self.ui.select_quality(StreamRecorder.QUALITY_OPTIONS)
                self.config.set('default_quality', quality)
                self.ui.show_success("Настройка сохранена")

            elif choice == "3":
                interval = self.ui.get_input("Интервал проверки (секунды)", str(self.config.get('check_interval')))
                try:
                    self.config.set('check_interval', int(interval))
                    self.ui.show_success("Настройка сохранена")
                except ValueError:
                    self.ui.show_error("Неверное значение")

            elif choice == "4":
                template = self.ui.get_input("Шаблон", self.config.get('filename_template'))
                self.config.set('filename_template', template)
                self.ui.show_success("Настройка сохранена")

            elif choice == "5":
                client_id = self.ui.get_input("Client ID")
                client_secret = self.ui.get_input("Client Secret")
                self.config.set_twitch_credentials(client_id, client_secret)
                self._initialize_api_client()
                self.ui.show_success("Креденшалы обновлены")

            elif choice == "6":
                break

    def _save_watched_streamers(self):
        """Сохранить список отслеживаемых стримеров"""
        watched_file = self.config.config_dir / "watched.json"
        with open(watched_file, 'w', encoding='utf-8') as f:
            json.dump(self.watched_streamers, f)

    def _load_watched_streamers(self):
        """Загрузить список отслеживаемых стримеров"""
        watched_file = self.config.config_dir / "watched.json"
        if watched_file.exists():
            with open(watched_file, 'r', encoding='utf-8') as f:
                self.watched_streamers = json.load(f)

    def _background_monitor(self):
        """Фоновый мониторинг стримеров"""
        self.ui.show_info("Фоновый режим активирован")
        check_interval = self.config.get('check_interval', 60)

        while self.running:
            for streamer in self.watched_streamers[:]:  # Копия списка
                try:
                    if self.twitch_client.is_stream_live(streamer):
                        if not self.recorder.is_recording(streamer):
                            # Стрим онлайн, но не записывается
                            quality = self.config.get('default_quality', 'best')
                            success = self.recorder.start_recording(
                                streamer=streamer,
                                quality=quality,
                                filename_template=self.config.get("filename_template")
                            )
                            if success:
                                self.logger.info(f"Автоматически начата запись {streamer}")
                    else:
                        # Стрим оффлайн
                        if self.recorder.is_recording(streamer):
                            # Останавливаем запись
                            self.recorder.stop_recording(streamer)
                            self.logger.info(f"Стрим {streamer} завершен, запись остановлена")

                except Exception as e:
                    self.logger.error(f"Ошибка мониторинга {streamer}: {e}")

            # Ждем перед следующей проверкой
            time.sleep(check_interval)

    def background_mode_action(self):
        """Действие: фоновый режим"""
        if not self.watched_streamers:
            self.ui.show_warning("Список отслеживаемых стримеров пуст")

            if self.ui.confirm("Добавить стримеров для отслеживания?"):
                while True:
                    streamer = self.ui.get_streamer_name()
                    if streamer and streamer not in self.watched_streamers:
                        self.watched_streamers.append(streamer)
                        self.ui.show_success(f"Добавлен {streamer}")

                    if not self.ui.confirm("Добавить еще?"):
                        break

                self._save_watched_streamers()

        if not self.watched_streamers:
            return

        self.ui.show_info(f"Отслеживаемые стримеры: {', '.join(self.watched_streamers)}")

        if self.ui.confirm("Запустить фоновый мониторинг?"):
            self.running = True
            self.background_thread = threading.Thread(target=self._background_monitor, daemon=True)
            self.background_thread.start()

            self.ui.show_success("Фоновый режим запущен!")
            self.ui.show_info("Приложение будет автоматически записывать стримы при их появлении")
            self.ui.show_info("Нажмите Ctrl+C для остановки")

            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                self.ui.show_info("Остановка фонового режима...")

    def run(self):
        """Запуск приложения"""
        self.ui.clear_screen()
        self.ui.print_banner()

        # Инициализация
        if not self._initialize_api_client():
            self.ui.show_error("Не удалось инициализировать API клиент")
            return

        self._initialize_recorder()
        self._load_watched_streamers()

        self.ui.show_success("Приложение успешно запущено!")

        # Главный цикл
        while True:
            try:
                choice = self.ui.show_menu()

                if choice == "1":
                    self.start_recording_action()
                elif choice == "2":
                    self.stop_recording_action()
                elif choice == "3":
                    self.show_active_recordings_action()
                elif choice == "4":
                    self.search_channels_action()
                elif choice == "5":
                    self.show_channel_info_action()
                elif choice == "6":
                    self.settings_action()
                elif choice == "7":
                    self.background_mode_action()
                elif choice == "8":
                    if self.ui.confirm("Вы уверены что хотите выйти?"):
                        self.recorder.stop_all_recordings()
                        self.ui.show_success("До свидания!")
                        break

                self.ui.pause()
                self.ui.clear_screen()
                self.ui.print_banner()

            except KeyboardInterrupt:
                self.ui.show_warning("\nПрервано пользователем")
                if self.ui.confirm("Выйти из приложения?"):
                    self.recorder.stop_all_recordings()
                    break
            except Exception as e:
                self.ui.show_error(f"Ошибка: {e}")
                self.logger.exception("Необработанная ошибка")
                self.ui.pause()


def main():
    """Точка входа в приложение"""
    app = TwitRec()
    app.run()


if __name__ == "__main__":
    main()
