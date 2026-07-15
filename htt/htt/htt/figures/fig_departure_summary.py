"""Quarantined historical channel-c departure-summary producer."""
from htt.core.cf4_observational_input import require_cf4_observational_input


def main() -> None:
    require_cf4_observational_input(consumer=__name__)


if __name__ == "__main__":
    main()
