import argparse
from .config import load_config


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ffa", description="Forest fragmentation analyzer")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="run on real satellite data (downloads open data, no account needed)")
    a.add_argument("--config", required=True)
    a.add_argument("--start", type=int); a.add_argument("--end", type=int)
    a.add_argument("--res", type=int, help="pixel size in metres (use 60 for a quick trial)")
    a.add_argument("--out")
    d = sub.add_parser("demo", help="offline synthetic demo to verify the install")
    d.add_argument("--out", default="outputs/demo")
    args = ap.parse_args(argv)
    if args.cmd == "demo":
        from .demo import run_demo
        run_demo(args.out)
    else:
        from .pipeline import run
        run(load_config(args.config, start_year=args.start, end_year=args.end, res=args.res, out_dir=args.out))


if __name__ == "__main__":
    main()
