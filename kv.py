import os
import subprocess
import sys
import click

_CENTRAL_CONFIG = os.path.expanduser("~/.config/knowledge-vault/.env")

_ENV = os.environ.copy()
_ENV["PATH"] = os.path.expanduser("~/.local/bin") + ":" + _ENV.get("PATH", "")

# Auto-load central config into subprocess environment
if os.path.isfile(_CENTRAL_CONFIG):
    with open(_CENTRAL_CONFIG) as _f:
        for _line in _f:
            _line = _line.rstrip("\n")
            if "=" in _line and not _line.startswith("#"):
                _k, _, _v = _line.partition("=")
                _ENV.setdefault(_k.strip(), _v.strip())


def _call(cmd: list[str]) -> int:
    return subprocess.call(cmd, env=_ENV)


@click.group()
def cli():
    """Knowledge Vault — unified CLI for ingestion, indexing, search and Strava."""
    pass


_PASSTHROUGH = {"allow_extra_args": True, "ignore_unknown_options": True}


@cli.command(name="ingest", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def ingest_cmd(args):
    """Download and transcribe YouTube content (delegates to kb-ingest)."""
    sys.exit(_call(["kb-ingest"] + list(args)))


@cli.command(name="index", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def index_cmd(args):
    """Embed and index content into Qdrant (delegates to kb-indexer)."""
    sys.exit(_call(["kb-indexer"] + list(args)))


@cli.command(name="search", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def search_cmd(args):
    """Search the knowledge base (delegates to kb-search)."""
    sys.exit(_call(["kb-search"] + list(args)))


@cli.group(name="strava")
def strava_group():
    """Strava sync, webhook and query commands."""
    pass


@strava_group.command(name="sync", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def strava_sync(args):
    """Sync Strava activities to local SQLite (delegates to strava-sync)."""
    sys.exit(_call(["strava-sync"] + list(args)))


@strava_group.command(name="webhook", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def strava_webhook(args):
    """Run the Strava webhook server (delegates to strava-webhook)."""
    sys.exit(_call(["strava-webhook"] + list(args)))


@strava_group.command(name="auth", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def strava_auth(args):
    """Save Strava OAuth tokens to .env (delegates to strava-auth)."""
    sys.exit(_call(["strava-auth"] + list(args)))


@strava_group.command(name="check", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def strava_check(args):
    """Check Strava configuration (delegates to strava-check)."""
    sys.exit(_call(["strava-check"] + list(args)))


@strava_group.command(name="query", context_settings=_PASSTHROUGH, add_help_option=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def strava_query(args):
    """Query local Strava database (delegates to strava-query)."""
    sys.exit(_call(["strava-query"] + list(args)))


@cli.command(name="setup")
def setup_cmd():
    """Run setup wizards for all tools interactively."""
    click.echo("=== Knowledge Vault Setup ===\n")

    steps = [
        ("kb-ingest", ["setup"]),
        ("kb-indexer", ["setup"]),
        ("kb-search", ["setup"]),
        ("strava-auth", []),
    ]

    for tool, args in steps:
        click.echo(f"\n--- {tool} ---")
        rc = _call([tool] + args)
        if rc != 0:
            click.echo(f"Setup failed for {tool}. Fix the error and re-run `kv setup`.")
            sys.exit(1)

    click.echo("\nAll tools configured. Config saved to ~/.config/knowledge-vault/.env")


@cli.command(name="check")
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True, help="Qdrant server URL")
@click.option("--data-dir", default="./data", show_default=True, help="Data directory (for ingest check)")
@click.option("--cookies", default=None, help="Path to cookies.txt (for ingest check)")
def check_cmd(qdrant_url, data_dir, cookies):
    """Run health checks across all tools."""
    failures = 0

    checks = [
        ("kb-ingest", ["check", "--data-dir", data_dir] + (["--cookies", cookies] if cookies else [])),
        ("kb-indexer", ["check", "--qdrant-url", qdrant_url]),
        ("kb-search", ["check", "--qdrant-url", qdrant_url]),
        ("strava-check", []),
    ]

    for tool, args in checks:
        click.echo(f"\n=== {tool} ===")
        rc = _call([tool] + args)
        if rc != 0:
            failures += 1

    click.echo()
    if failures == 0:
        click.echo("All tools passed.")
    else:
        click.echo(f"{failures} tool(s) had failures.")
        sys.exit(1)
