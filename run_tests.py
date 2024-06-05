import pytest
import sys


def plain_pytest():
    pytest_args = ["-v", "raatests"]
    extra_args = sys.argv[1:]
    args = pytest_args + extra_args
    try:
        pytest.main(args)
    except Exception as e:
        print(f"Error: {e}")


def main():
    plain_pytest()


if __name__ == "__main__":
    main()
