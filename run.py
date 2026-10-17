"""Convenience launcher:  python run.py demo   |   python run.py analyze --config configs/valparai.yaml"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))
from ffa.cli import main
main()
