"""CLI module for nex-collector."""
import click
import asyncio
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import TeacherRun
from app.distill.pipeline import DistillationPipeline
from app.workers.jobs import enqueue_teacher_run_job


@click.group()
def cli():
    """NEX Collector CLI."""
    pass


@cli.command()
@click.argument("example_id")
def enqueue_example_runs(example_id: str):
    """Enqueue all runs for a specific example."""
    db: Session = SessionLocal()
    try:
        runs = db.query(TeacherRun).filter(TeacherRun.example_id == example_id).all()
        if not runs:
            click.echo(f"No runs found for example {example_id}")
            return
        
        for run in runs:
            enqueue_teacher_run_job(run.id)
            click.echo(f"Enqueued run {run.id}")
        
        click.echo(f"Enqueued {len(runs)} runs")
    finally:
        db.close()


@cli.command()
@click.option("--name", required=True)
@click.option("--version", required=True)
@click.option("--kind", type=click.Choice(["train", "eval", "synthetic", "finetune_pack"]), required=True)
@click.option("--variant-ids", multiple=True, required=True)
@click.option("--min-length", type=int)
@click.option("--max-length", type=int)
def distill_build(name: str, version: str, kind: str, variant_ids: tuple, min_length: int, max_length: int):
    """Build a distilled dataset."""
    db: Session = SessionLocal()
    try:
        filters = {}
        if min_length:
            filters["min_length"] = min_length
        if max_length:
            filters["max_length"] = max_length
        
        import uuid
        dataset_id = f"ds-{uuid.uuid4().hex[:12]}"
        
        pipeline = DistillationPipeline(db)
        manifest = pipeline.build_dataset(
            dataset_id=dataset_id,
            name=name,
            version=version,
            kind=kind,
            variant_ids=list(variant_ids),
            filters=filters
        )
        
        click.echo(f"Built dataset {dataset_id}")
        click.echo(f"Files: {[f['name'] for f in manifest['files']]}")
        click.echo(f"Examples: {manifest['num_examples']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
    finally:
        db.close()


if __name__ == "__main__":
    cli()

