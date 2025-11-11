#!/usr/bin/env python3
"""
Тестовый скрипт для проверки streamlink и записи
"""
import subprocess
import sys
import time
import os

def test_streamlink_installed():
    """Проверить установлен ли streamlink"""
    print("🔍 Проверка установки streamlink...")
    try:
        result = subprocess.run(
            ["streamlink", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Streamlink установлен: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Ошибка при запуске streamlink")
            return False
    except FileNotFoundError:
        print("✗ Streamlink не найден!")
        print("  Установите: pip install streamlink")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False

def test_stream_available(streamer):
    """Проверить доступен ли стрим"""
    print(f"\n🔍 Проверка доступности стрима {streamer}...")
    try:
        result = subprocess.run(
            ["streamlink", f"https://www.twitch.tv/{streamer}", "--stream-url"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            print(f"✓ Стрим {streamer} доступен!")
            return True
        else:
            print(f"✗ Стрим {streamer} недоступен или оффлайн")
            if result.stderr:
                print(f"  Ошибка: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  Таймаут при проверке стрима")
        return False
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False

def test_recording(streamer, duration=10):
    """Тест записи стрима"""
    print(f"\n📹 Тест записи стрима {streamer} ({duration} секунд)...")

    output_file = f"test_{streamer}.mp4"

    try:
        print(f"  Запуск записи в {output_file}...")
        process = subprocess.Popen(
            [
                "streamlink",
                f"https://www.twitch.tv/{streamer}",
                "best",
                "-o", output_file,
                "--twitch-disable-ads"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Даем процессу время на запуск
        time.sleep(3)

        # Проверяем что процесс не упал
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"✗ Процесс завершился с кодом {process.returncode}")
            print(f"  Вывод: {stderr.decode()[:500]}")
            return False

        print(f"  Процесс запущен (PID: {process.pid})")
        print(f"  Запись {duration} секунд...")

        # Записываем несколько секунд
        time.sleep(duration)

        # Останавливаем запись
        print("  Остановка записи...")
        process.terminate()
        process.wait(timeout=5)

        # Проверяем файл
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ Запись успешна! Файл: {output_file} ({file_size} байт)")

            # Удаляем тестовый файл
            os.remove(output_file)
            print(f"  Тестовый файл удален")
            return True
        else:
            print(f"✗ Файл записи не создан")
            return False

    except Exception as e:
        print(f"✗ Ошибка: {e}")
        if process:
            try:
                process.kill()
            except:
                pass
        return False

def main():
    print("=" * 60)
    print("TwitRec - Тест записи стримов")
    print("=" * 60)

    # Проверка streamlink
    if not test_streamlink_installed():
        sys.exit(1)

    # Получить имя стримера
    if len(sys.argv) > 1:
        streamer = sys.argv[1]
    else:
        streamer = input("\nВведите имя стримера для теста: ").strip()

    if not streamer:
        print("✗ Имя стримера не указано")
        sys.exit(1)

    # Проверка доступности стрима
    if not test_stream_available(streamer):
        print("\n⚠️  Стрим недоступен, но можно попробовать записать...")
        response = input("Продолжить тест записи? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Тест записи
    success = test_recording(streamer, duration=10)

    print("\n" + "=" * 60)
    if success:
        print("✓ Все тесты пройдены успешно!")
        print("TwitRec готов к работе!")
    else:
        print("✗ Тесты не прошли")
        print("Проверьте:")
        print("  1. Установлен ли streamlink: pip install streamlink")
        print("  2. Онлайн ли стрим")
        print("  3. Есть ли доступ к интернету")
    print("=" * 60)

if __name__ == "__main__":
    main()
