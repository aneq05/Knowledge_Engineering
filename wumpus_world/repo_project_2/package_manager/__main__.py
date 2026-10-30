import argparse
import sys

from .installer import install
from .loaders import load_repository, load_requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Instalacja pakietów do pustego środowiska")
    parser.add_argument("repository", help="ścieżka do repozytorium JSON")
    parser.add_argument("requests", help="ścieżka do pliku żądań")
    args = parser.parse_args()

    try:
        result = install(load_repository(args.repository), load_requests(args.requests))
    except (ValueError, RuntimeError) as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 2
    if result is None:
        print("Brak rozwiązania dla podanych żądań.")
        return 1

    print("Zainstalowane pakiety:")
    for item in result.state.installed.values():
        print(f"  {item.package} {item.version}{' manual' if item.manual else ''}")
    print("Stan przeszedł niezależną weryfikację.")
    print(f"Przestarzałość żądanych: {result.requested_staleness}")
    print(f"Liczba pakietów: {result.package_count}")
    print(f"Przestarzałość pozostałych: {result.dependency_staleness}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
