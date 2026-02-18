import subprocess
import sys
import click


@click.group()
def cli():
    """Knowledge Vault — unified CLI for ingestion, indexing and search."""
    pass


@cli.command(name="ingest", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def ingest_cmd(args):
    """Download and transcribe YouTube content (delegates to kb-ingest)."""
    sys.exit(subprocess.call(["kb-ingest"] + list(args)))


@cli.command(name="index", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def index_cmd(args):
    """Embed and index content into Qdrant (delegates to kb-indexer)."""
    sys.exit(subprocess.call(["kb-indexer"] + list(args)))


@cli.command(name="search", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def search_cmd(args):
    """Search the knowledge base (delegates to kb-search)."""
    sys.exit(subprocess.call(["kb-search"] + list(args)))


@cli.command(name="check")
@click.option("--qdrant-url", default="http://localhost:6333", show_default=True, help="Qdrant server URL")
@click.option("--data-dir", default="./data", show_default=True, help="Data directory (for ingest check)")
@click.option("--cookies", default=None, help="Path to cookies.txt (for ingest check)")
def check_cmd(qdrant_url, data_dir, cookies):
    """Run health checks across all kb tools."""
    failures = 0

    checks = [
        ("kb-ingest", ["check", "--data-dir", data_dir] + (["--cookies", cookies] if cookies else [])),
        ("kb-indexer", ["check", "--qdrant-url", qdrant_url]),
        ("kb-search", ["check", "--qdrant-url", qdrant_url]),
    ]

    for tool, args in checks:
        click.echo(f"\n=== {tool} ===")
        rc = subprocess.call([tool] + args)
        if rc != 0:
            failures += 1

    click.echo()
    if failures == 0:
        click.echo("All tools passed.")
    else:
        click.echo(f"{failures} tool(s) had failures.")
        sys.exit(1)
