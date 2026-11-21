import argparse
import sys

from .explanations import explain_requests
from .loaders import load_names, load_repository, load_requests, load_state
from .models import EnvironmentState
from .operations import install_with_state, remove_packages
from .plan import save_state


def _show(result, output) -> int:
    if result is None:
        print("Brak rozwiązania dla podanych żądań.")
        return 1
    if output:
        save_state(result.state, output)
    print("Plan zmian:")
    for change in result.changes or ["(brak zmian)"]:
        print(f"  {change}")
    print("Stan końcowy:")
    for item in sorted(result.state.installed.values(), key=lambda i: i.package):
        print(f"  {item.package} {item.version}{' manual' if item.manual else ''}")
    print(f"Wartości kryteriów: {result.costs}")
    print("Stan przeszedł niezależną weryfikację.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="package_manager")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "remove", "update", "explain"):
        p = sub.add_parser(name)
        p.add_argument("repository")
        p.add_argument("items", help="plik żądań (install, explain) lub nazw pakietów (remove)")
        if name != "explain":
            p.add_argument("--state", help="plik stanu (domyślnie pusty)")
            p.add_argument("--output", help="gdzie zapisać nowy stan")
        if name == "remove":
            p.add_argument("--autoremove", action="store_true")
    args = parser.parse_args()
    try:
        repository = load_repository(args.repository)
        if args.command == "explain":
            core = explain_requests(repository, load_requests(args.items))
            print("Żądania da się spełnić." if core is None else "Sprzeczny podzbiór:\n  " + "\n  ".join(core))
            return 0
        state = load_state(args.state) if args.state else EnvironmentState()
        if args.command == "install":
            result = install_with_state(repository, load_requests(args.items), state)
        else:
            result = remove_packages(repository, load_names(args.items), state, args.autoremove)
        return _show(result, args.output)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())