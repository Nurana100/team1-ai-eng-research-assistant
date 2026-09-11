import argparse

def main():
    parser = argparse.ArgumentParser(prog="researcher")
    parser.add_argument("command", choices=["ask"])
    parser.add_argument("question")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--sources", default="wiki,arxiv,web")
    args = parser.parse_args()

    print(f"Question: {args.question}")
    print("(pipeline not wired yet — placeholder)")

if __name__ == "__main__":
    main()
