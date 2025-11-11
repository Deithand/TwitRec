"""
Красивый CLI интерфейс с использованием rich
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
from typing import List, Dict, Optional
import time


class CLIInterface:
    """Класс для красивого отображения CLI интерфейса"""

    def __init__(self):
        self.console = Console()

    def print_banner(self):
        """Показать стартовый баннер"""
        banner = """
╔════════════════════════════════════════════╗
║                                            ║
║         ████████╗██╗    ██╗██╗████████╗   ║
║         ╚══██╔══╝██║    ██║██║╚══██╔══╝   ║
║            ██║   ██║ █╗ ██║██║   ██║      ║
║            ██║   ██║███╗██║██║   ██║      ║
║            ██║   ╚███╔███╔╝██║   ██║      ║
║            ╚═╝    ╚══╝╚══╝ ╚═╝   ╚═╝      ║
║                                            ║
║            ██████╗ ███████╗ ██████╗       ║
║            ██╔══██╗██╔════╝██╔════╝       ║
║            ██████╔╝█████╗  ██║            ║
║            ██╔══██╗██╔══╝  ██║            ║
║            ██║  ██║███████╗╚██████╗       ║
║            ╚═╝  ╚═╝╚══════╝ ╚═════╝       ║
║                                            ║
║     Twitch Stream Recorder v1.0.0         ║
║                                            ║
╚════════════════════════════════════════════╝
"""
        self.console.print(banner, style="bold cyan", justify="center")

    def show_menu(self) -> str:
        """Показать главное меню"""
        self.console.print()
        menu = Table(show_header=False, box=box.ROUNDED, border_style="cyan")

        menu.add_row("[bold cyan]1.[/] 📹 Начать запись стрима")
        menu.add_row("[bold cyan]2.[/] ⏹️  Остановить запись")
        menu.add_row("[bold cyan]3.[/] 📊 Показать активные записи")
        menu.add_row("[bold cyan]4.[/] 🔍 Поиск каналов")
        menu.add_row("[bold cyan]5.[/] ℹ️  Информация о канале")
        menu.add_row("[bold cyan]6.[/] ⚙️  Настройки")
        menu.add_row("[bold cyan]7.[/] 🚀 Фоновый режим")
        menu.add_row("[bold cyan]8.[/] ❌ Выход")

        self.console.print(
            Panel(menu, title="[bold]Главное меню[/]", border_style="cyan")
        )

        choice = Prompt.ask(
            "\n[bold cyan]Выберите действие[/]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8"],
            default="1"
        )

        return choice

    def get_streamer_name(self) -> Optional[str]:
        """Получить имя стримера от пользователя"""
        streamer = Prompt.ask("\n[bold cyan]Введите имя стримера[/]")
        return streamer.strip() if streamer else None

    def select_quality(self, available_qualities: List[str]) -> str:
        """Выбрать качество записи"""
        self.console.print("\n[bold cyan]Доступные качества:[/]")

        quality_table = Table(show_header=False, box=box.SIMPLE)
        for i, quality in enumerate(available_qualities, 1):
            quality_table.add_row(f"[cyan]{i}.[/]", quality)

        self.console.print(quality_table)

        choice = Prompt.ask(
            "\n[bold cyan]Выберите качество[/]",
            choices=[str(i) for i in range(1, len(available_qualities) + 1)],
            default="1"
        )

        return available_qualities[int(choice) - 1]

    def show_stream_info(self, stream_info: Dict):
        """Показать информацию о стриме"""
        info_table = Table(box=box.ROUNDED, border_style="green", show_header=False)

        info_table.add_row("[bold cyan]Стример:[/]", stream_info.get('user_name', 'N/A'))
        info_table.add_row("[bold cyan]Название:[/]", stream_info.get('title', 'N/A'))
        info_table.add_row("[bold cyan]Игра:[/]", stream_info.get('game_name', 'N/A'))
        info_table.add_row("[bold cyan]Зрители:[/]", str(stream_info.get('viewer_count', 0)))
        info_table.add_row("[bold cyan]Язык:[/]", stream_info.get('language', 'N/A'))

        self.console.print(
            Panel(info_table, title="[bold green]📺 Информация о стриме[/]", border_style="green")
        )

    def show_channel_info(self, channel_info: Dict):
        """Показать информацию о канале"""
        info_table = Table(box=box.ROUNDED, border_style="blue", show_header=False)

        info_table.add_row("[bold cyan]Канал:[/]", channel_info.get('broadcaster_name', 'N/A'))
        info_table.add_row("[bold cyan]Игра:[/]", channel_info.get('game_name', 'N/A'))
        info_table.add_row("[bold cyan]Название:[/]", channel_info.get('title', 'N/A'))

        self.console.print(
            Panel(info_table, title="[bold blue]ℹ️  Информация о канале[/]", border_style="blue")
        )

    def show_active_recordings(self, recordings: Dict[str, Dict]):
        """Показать активные записи"""
        if not recordings:
            self.console.print("\n[yellow]Нет активных записей[/]")
            return

        table = Table(
            title="[bold]📹 Активные записи[/]",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("Стример", style="green", no_wrap=True)
        table.add_column("Качество", style="blue")
        table.add_column("Время", style="yellow")
        table.add_column("Размер", style="magenta")
        table.add_column("Старт", style="cyan")

        for streamer, info in recordings.items():
            file_size_mb = info['file_size'] / (1024 * 1024)
            table.add_row(
                streamer,
                info['quality'],
                info['duration'],
                f"{file_size_mb:.2f} MB",
                info['start_time']
            )

        self.console.print("\n", table)

    def show_search_results(self, channels: List[Dict]):
        """Показать результаты поиска каналов"""
        if not channels:
            self.console.print("\n[yellow]Каналы не найдены[/]")
            return

        table = Table(
            title="[bold]🔍 Результаты поиска[/]",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            header_style="bold cyan"
        )

        table.add_column("#", style="dim", width=4)
        table.add_column("Канал", style="green")
        table.add_column("Игра", style="blue")
        table.add_column("Онлайн", style="yellow", justify="center")

        for i, channel in enumerate(channels, 1):
            is_live = "🔴 LIVE" if channel.get('is_live') else "⚫ Offline"
            table.add_row(
                str(i),
                channel.get('display_name', 'N/A'),
                channel.get('game_name', 'N/A'),
                is_live
            )

        self.console.print("\n", table)

    def show_success(self, message: str):
        """Показать сообщение об успехе"""
        self.console.print(f"\n[bold green]✓ {message}[/]")

    def show_error(self, message: str):
        """Показать сообщение об ошибке"""
        self.console.print(f"\n[bold red]✗ {message}[/]")

    def show_warning(self, message: str):
        """Показать предупреждение"""
        self.console.print(f"\n[bold yellow]⚠ {message}[/]")

    def show_info(self, message: str):
        """Показать информационное сообщение"""
        self.console.print(f"\n[bold blue]ℹ {message}[/]")

    def confirm(self, message: str) -> bool:
        """Запросить подтверждение"""
        return Confirm.ask(f"\n[bold cyan]{message}[/]")

    def show_loading(self, message: str):
        """Показать индикатор загрузки"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"[cyan]{message}...", total=None)
            time.sleep(1)

    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Получить ввод пользователя"""
        if default:
            return Prompt.ask(f"\n[bold cyan]{prompt}[/]", default=default)
        return Prompt.ask(f"\n[bold cyan]{prompt}[/]")

    def clear_screen(self):
        """Очистить экран"""
        self.console.clear()

    def pause(self):
        """Пауза - ждать нажатия клавиши"""
        self.console.print("\n[dim]Нажмите Enter для продолжения...[/]", end="")
        input()
