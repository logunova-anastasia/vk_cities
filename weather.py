import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class WeatherData:
    city: str
    temperature: int
    country: str


def read_cities(filename: Path) -> list[str]:
    """Читает города, убирает пустые строки и повторы"""
    cities = []
    seen = set()

    with filename.open(encoding="utf-8-sig") as file:
        for line in file:
            city = line.strip()
            if city and city.casefold() not in seen:
                cities.append(city)
                seen.add(city.casefold())

    return cities


def get_weather(city: str) -> WeatherData:
    """Запрашивает текущую температуру и страну"""
    url = f"https://wttr.in/{quote(city, safe='')}?format=j1"
    request = Request(url, headers={"User-Agent": "Python-Weather-Homework/1.0"})

    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)

        temperature = int(data["current_condition"][0]["temp_C"])
        country = data["nearest_area"][0]["country"][0]["value"].strip()
        if not country:
            raise ValueError("В ответе API нет названия страны")

        return WeatherData(city=city, temperature=temperature, country=country)

    except (HTTPError, URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"не удалось получить данные: {error}") from error


def format_temperature(value: float) -> str:
    """Форматирует температуру со знаком"""
    if value == int(value):
        return f"{int(value):+d} °C"
    return f"{value:+.1f} °C"


def display_weather(data: list[WeatherData]) -> None:
    print("Погода по городам:")
    for item in data:
        print(f"{item.city}, {item.country} {format_temperature(item.temperature)}")


def display_country_stats(data: list[WeatherData]) -> None:
    countries = defaultdict(list)
    for item in data:
        countries[item.country].append(item.temperature)

    print("\nСтатистика по странам:")
    for country in sorted(countries):
        temperatures = countries[country]
        count = len(temperatures)
        average = sum(temperatures) / count
        minimum = min(temperatures)
        maximum = max(temperatures)

        print(
            f"{country} — {count} cities, "
            f"avg: {format_temperature(average)}, "
            f"min: {format_temperature(minimum)}, "
            f"max: {format_temperature(maximum)}"
        )


def main() -> int:
    filename = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("Cities.txt")

    try:
        cities = read_cities(filename)
    except OSError as error:
        print(f"Ошибка чтения файла {filename}: {error}", file=sys.stderr)
        return 1

    if not cities:
        print("Файл не содержит городов.", file=sys.stderr)
        return 1

    weather_data = []
    for city in cities:
        try:
            weather_data.append(get_weather(city))
        except RuntimeError as error:
            print(f"{city}: {error}", file=sys.stderr)

    if not weather_data:
        print("Не удалось получить данные ни для одного города.", file=sys.stderr)
        return 1

    display_weather(weather_data)
    display_country_stats(weather_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
