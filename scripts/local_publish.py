"""
Local blog publisher - run the full pipeline from your computer.

Reads credentials from:
  - ../blogger_tokens.json  (Blogger OAuth credentials)
  - ../.env.local           (DEEPSEEK_API_KEY, PEXELS_API_KEY)

Usage:
  python local_publish.py              # publish 1 article
  python local_publish.py 3            # publish 3 articles
  python local_publish.py 1 --draft    # save as draft only
  python local_publish.py --trending   # fetch & publish trending repo articles
  python local_publish.py --trending --list  # list trending repos (no publish)
  python local_publish.py --setup      # first-time OAuth setup

No GitHub Actions needed - everything runs locally.
"""

import os
import sys
import json
import time
import random


def load_credentials():
    """Load credentials from local config files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)

    # Load Blogger tokens
    tokens_path = os.path.join(project_dir, "blogger_tokens.json")
    if not os.path.exists(tokens_path):
        print(f"ERROR: {tokens_path} not found!")
        print("Run: python local_publish.py --setup")
        sys.exit(1)

    with open(tokens_path, "r") as f:
        tokens = json.load(f)

    # Load .env.local
    env_path = os.path.join(project_dir, ".env.local")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

    # Set Blogger credentials as env vars
    for key in ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN", "BLOGGER_BLOG_ID"]:
        if key in tokens:
            os.environ[key] = tokens[key]

    missing = []
    for key in ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN", "BLOGGER_BLOG_ID", "DEEPSEEK_API_KEY"]:
        if not os.environ.get(key):
            missing.append(key)

    if missing:
        print(f"ERROR: Missing credentials: {', '.join(missing)}")
        print("\nBlogger tokens should be in blogger_tokens.json")
        print("DEEPSEEK_API_KEY should be in .env.local")
        sys.exit(1)

    print("Credentials loaded successfully.")
    print(f"  Blog ID: {os.environ['BLOGGER_BLOG_ID']}")
    print(f"  DeepSeek key: ****{os.environ['DEEPSEEK_API_KEY'][-4:]}")
    if os.environ.get("PEXELS_API_KEY"):
        print(f"  Pexels key: ****{os.environ['PEXELS_API_KEY'][-4:]}")
    else:
        print(f"  Pexels key: NOT SET (articles will be text-only)")
    print()
    return tokens


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        from publish_to_blogger import setup_oauth
        result = setup_oauth()
        # Save tokens
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(base_dir)
        tokens_path = os.path.join(project_dir, "blogger_tokens.json")
        save_data = {
            "BLOGGER_CLIENT_ID": result["client_id"],
            "BLOGGER_CLIENT_SECRET": result["client_secret"],
            "BLOGGER_REFRESH_TOKEN": result["refresh_token"],
            "BLOGGER_BLOG_ID": result["blog_id"],
            "BLOG_NAME": "aitoolshub",
        }
        with open(tokens_path, "w") as f:
            json.dump(save_data, f, indent=2)
        print(f"\nCredentials saved to: {tokens_path}")
        return

    # Load credentials
    load_credentials()

    # Parse args
    count = 1
    is_draft = False
    skip_images = False
    no_wait = False
    trending = False
    list_only = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--draft":
            is_draft = True
        elif args[i] == "--no-images":
            skip_images = True
        elif args[i] == "--now":
            no_wait = True
        elif args[i] == "--trending":
            trending = True
        elif args[i] == "--list":
            list_only = True
        elif args[i].isdigit():
            count = int(args[i])
        i += 1

    # Handle trending mode
    if trending:
        from publish_trending import run_trending_pipeline, list_trending
        if list_only:
            list_trending()
            return
        results = run_trending_pipeline(count=count, is_draft=is_draft, force_refresh=True)
        return results

    # Optional random delay before starting (like the CI does)
    if not no_wait:
        delay_min = random.randint(1, 15)
        print(f"Naturalizing timing: waiting {delay_min} minutes before starting...")
        print(f"  (use --now to skip this delay)")
        for remaining in range(delay_min * 60, 0, -1):
            if remaining % 30 == 0:
                print(f"  {remaining // 60}m {remaining % 60}s remaining...")
            time.sleep(1)
        print()

    # Skip images if requested (useful for quick testing)
    if skip_images and "PEXELS_API_KEY" in os.environ:
        print("--no-images flag set, skipping image fetch")
        del os.environ["PEXELS_API_KEY"]

    # Run the pipeline
    from publish_to_blogger import run_pipeline
    results = run_pipeline(count=count, is_draft=is_draft)

    # Final summary
    success = sum(1 for r in results if r["success"])
    print(f"\nDone: {success}/{count} articles {'saved as draft' if is_draft else 'published'}.")
    if success < count:
        print("Check errors above for details.")

    return results


if __name__ == "__main__":
    main()
