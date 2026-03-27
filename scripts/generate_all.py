"""Entry point: generate all profile README assets."""

from generate_dashboard import main as dashboard
from generate_tech_stack import main as tech_stack


if __name__ == "__main__":
    dashboard()
    tech_stack()
