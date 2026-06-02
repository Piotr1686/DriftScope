"""Typer CLI entrypoint — stub (W1).

Implementacja: W1 (run command) + W6 (--resume checkpointing).
"""
import typer

app = typer.Typer(help="DriftScope — stationarity audit for discrete streams.")


@app.command()
def run(
    resume: bool = typer.Option(
        False, "--resume", help="Pominij konfiguracje z istniejacymi shardami"
    ),
) -> None:
    """Uruchom pelny pipeline DriftScope."""
    raise NotImplementedError("CLI run — implementacja w W1")


if __name__ == "__main__":
    app()
