"""Comprehensive seeding for all ML Model Development components."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from datetime import datetime, timedelta
from uuid import uuid4
import random

from core.config import settings
from db.models import (
    ml_recipe, ml_recipe_version, ml_model, ml_run, ml_monitor_snapshot,
    evaluation_pack, evaluation_pack_version, recipe_evaluation_pack,
    evaluation_result, monitor_evaluation_snapshot
)

# Create engine
engine = create_engine(settings.database_url)


def seed_complete_ml_data():
    """Seed all ML development components with interconnected data."""
    
    with engine.connect() as conn:
        print("🌱 Starting comprehensive ML Model Development seeding...\n")
        
        # Step 1: Check existing recipes and packs
        print("📋 Step 1: Checking existing recipes and evaluation packs...")
        recipes_result = conn.execute(select(ml_recipe)).fetchall()
        recipes = [dict(row._mapping) for row in recipes_result]
        
        packs_result = conn.execute(select(evaluation_pack)).fetchall()
        packs = [dict(row._mapping) for row in packs_result]
        
        if not recipes:
            print("❌ No recipes found! Please run seed_ml_recipes.py first.")
            return
        
        if not packs:
            print("❌ No evaluation packs found! Please run seed_evaluation_packs.py first.")
            return
        
        print(f"   ✓ Found {len(recipes)} recipes")
        print(f"   ✓ Found {len(packs)} evaluation packs\n")
        
        # Step 2: Attach evaluation packs to recipes
        print("📎 Step 2: Attaching evaluation packs to recipes...")
        attachments_created = 0
        
        for recipe in recipes:
            # Find matching pack by model_family
            matching_pack = next(
                (p for p in packs if p['model_family'] == recipe['model_family']),
                None
            )
            
            if matching_pack:
                try:
                    conn.execute(
                        recipe_evaluation_pack.insert().values(
                            recipe_id=recipe['id'],
                            pack_id=matching_pack['id'],
                            created_at=datetime.utcnow()
                        )
                    )
                    attachments_created += 1
                    print(f"   ✓ Attached {matching_pack['name']} to {recipe['name']}")
                except Exception as e:
                    # Skip if already attached
                    pass
        
        conn.commit()
        print(f"   ✓ Created {attachments_created} recipe-pack attachments\n")
        
        # Step 3: Create ML Models from recipes
        print("🤖 Step 3: Creating ML models from recipes...")
        models_data = []
        
        for recipe in recipes:
            if recipe['status'] == 'approved':
                # Create 1-2 models per approved recipe
                num_models = random.randint(1, 2)
                
                for i in range(num_models):
                    model_id = f"model_{recipe['model_family']}_{uuid4().hex[:8]}"
                    
                    # Get recipe version
                    recipe_versions = conn.execute(
                        select(ml_recipe_version)
                        .where(ml_recipe_version.c.recipe_id == recipe['id'])
                        .order_by(ml_recipe_version.c.created_at.desc())
                    ).fetchall()
                    
                    if recipe_versions:
                        latest_version = dict(recipe_versions[0]._mapping)
                        
                        statuses = ['draft', 'staging', 'production', 'retired']
                        weights = [0.1, 0.2, 0.6, 0.1]  # Favor production models
                        
                        model_data = {
                            'id': model_id,
                            'name': f"{recipe['name']} Model v{i+1}",
                            'model_family': recipe['model_family'],
                            'recipe_id': recipe['id'],
                            'recipe_version_id': latest_version['version_id'],
                            'status': random.choices(statuses, weights)[0],
                            'owner': random.choice(['data-science-team', 'ml-ops', 'analytics', 'product-team']),
                            'created_at': datetime.utcnow() - timedelta(days=random.randint(10, 90)),
                            'updated_at': datetime.utcnow() - timedelta(days=random.randint(0, 10))
                        }
                        
                        models_data.append(model_data)
                        print(f"   ✓ Created {model_data['name']} ({model_data['status']})")
        
        if models_data:
            conn.execute(ml_model.insert(), models_data)
            conn.commit()
        
        print(f"   ✓ Created {len(models_data)} ML models\n")
        
        # Step 4: Create runs for models
        print("🏃 Step 4: Creating training and evaluation runs...")
        runs_data = []
        
        for model_data in models_data:
            # Create 2-4 runs per model
            num_runs = random.randint(2, 4)
            
            for i in range(num_runs):
                run_id = f"run_{model_data['model_family']}_{uuid4().hex[:8]}"
                
                run_types = ['train', 'eval', 'backtest']
                run_statuses = ['succeeded', 'succeeded', 'succeeded', 'failed']  # Favor success
                run_type = random.choice(run_types)
                run_status = random.choice(run_statuses)
                
                # Generate realistic metrics based on model family
                metrics_json = generate_metrics_for_family(model_data['model_family'])
                
                started = datetime.utcnow() - timedelta(days=random.randint(1, 60))
                finished = started + timedelta(minutes=random.randint(5, 120)) if run_status == 'succeeded' else None
                
                run_data = {
                    'id': run_id,
                    'model_id': model_data['id'],
                    'recipe_id': model_data['recipe_id'],
                    'recipe_version_id': model_data['recipe_version_id'],
                    'run_type': run_type,
                    'status': run_status,
                    'started_at': started,
                    'finished_at': finished,
                    'metrics_json': metrics_json,
                    'artifacts_json': {
                        'model_artifact': f"s3://ml-artifacts/{run_id}/model.pkl",
                        'training_data': f"s3://ml-artifacts/{run_id}/train_data.parquet",
                        'plots': [f"plot_{j}.png" for j in range(3)]
                    },
                    'logs_text': f"Run {run_type} completed {'successfully' if run_status == 'succeeded' else 'with errors'}"
                }
                
                runs_data.append(run_data)
                print(f"   ✓ Created {run_type} run for {model_data['name']} ({run_status})")
        
        if runs_data:
            conn.execute(ml_run.insert(), runs_data)
            conn.commit()
        
        print(f"   ✓ Created {len(runs_data)} runs\n")
        
        # Step 5: Create monitoring snapshots for production models
        print("📊 Step 5: Creating monitoring snapshots...")
        monitor_snapshots_data = []
        
        production_models = [m for m in models_data if m['status'] == 'production']
        
        for model_data in production_models:
            # Create 5-10 snapshots over time
            num_snapshots = random.randint(5, 10)
            
            for i in range(num_snapshots):
                snapshot_id = f"mon_{model_data['id']}_{uuid4().hex[:8]}"
                
                # Generate monitoring metrics with some drift over time
                performance_metrics = generate_metrics_for_family(model_data['model_family'])
                
                # Add some degradation over time
                drift_factor = 1 + (i * 0.02)  # 2% degradation per snapshot
                for key in performance_metrics:
                    if 'error' in key.lower() or 'mape' in key.lower():
                        performance_metrics[key] *= drift_factor
                    elif 'accuracy' in key.lower() or 'r2' in key.lower():
                        performance_metrics[key] /= drift_factor
                
                snapshot_data = {
                    'id': snapshot_id,
                    'model_id': model_data['id'],
                    'captured_at': datetime.utcnow() - timedelta(days=num_snapshots - i),
                    'performance_metrics_json': performance_metrics,
                    'drift_metrics_json': {
                        'psi': random.uniform(0.05, 0.25),
                        'ks_stat': random.uniform(0.02, 0.15),
                        'feature_drift_count': random.randint(0, 5)
                    },
                    'data_freshness_json': {
                        'last_update': (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
                        'records_processed': random.randint(10000, 100000),
                        'data_quality_score': random.uniform(0.85, 0.99)
                    },
                    'alerts_json': {
                        'triggered_alerts': random.randint(0, 2),
                        'alert_types': ['drift_warning'] if random.random() > 0.7 else []
                    }
                }
                
                monitor_snapshots_data.append(snapshot_data)
            
            print(f"   ✓ Created {num_snapshots} snapshots for {model_data['name']}")
        
        if monitor_snapshots_data:
            conn.execute(ml_monitor_snapshot.insert(), monitor_snapshots_data)
            conn.commit()
        
        print(f"   ✓ Created {len(monitor_snapshots_data)} monitoring snapshots\n")
        
        # Step 6: Execute evaluation packs on runs
        print("✅ Step 6: Creating evaluation results for runs...")
        eval_results_data = []
        
        # Get successful runs
        successful_runs = [r for r in runs_data if r['status'] == 'succeeded']
        
        for run_data in successful_runs[:10]:  # Limit to 10 for demo
            # Find matching pack
            recipe = next((r for r in recipes if r['id'] == run_data['recipe_id']), None)
            if not recipe:
                continue
            
            matching_pack = next(
                (p for p in packs if p['model_family'] == recipe['model_family']),
                None
            )
            
            if matching_pack:
                # Get pack version
                pack_versions = conn.execute(
                    select(evaluation_pack_version)
                    .where(evaluation_pack_version.c.pack_id == matching_pack['id'])
                    .order_by(evaluation_pack_version.c.created_at.desc())
                ).fetchall()
                
                if pack_versions:
                    pack_version = dict(pack_versions[0]._mapping)
                    
                    result_id = f"eval_{run_data['id']}_{uuid4().hex[:8]}"
                    
                    # Generate evaluation results
                    metrics = run_data['metrics_json']
                    pack_json = pack_version['pack_json']
                    
                    results_json, status = evaluate_run(metrics, pack_json)
                    
                    eval_result = {
                        'id': result_id,
                        'run_id': run_data['id'],
                        'pack_id': matching_pack['id'],
                        'pack_version_id': pack_version['version_id'],
                        'executed_at': run_data['finished_at'] or datetime.utcnow(),
                        'status': status,
                        'results_json': results_json,
                        'summary_text': generate_summary(results_json, status)
                    }
                    
                    eval_results_data.append(eval_result)
                    print(f"   ✓ Evaluated run {run_data['id'][:20]}... → {status.upper()}")
        
        if eval_results_data:
            conn.execute(evaluation_result.insert(), eval_results_data)
            conn.commit()
        
        print(f"   ✓ Created {len(eval_results_data)} evaluation results\n")
        
        # Step 7: Create monitoring evaluation snapshots
        print("📈 Step 7: Creating monitoring evaluation snapshots...")
        monitor_eval_snapshots_data = []
        
        for model_data in production_models[:5]:  # Limit to 5 for demo
            matching_pack = next(
                (p for p in packs if p['model_family'] == model_data['model_family']),
                None
            )
            
            if matching_pack:
                pack_versions = conn.execute(
                    select(evaluation_pack_version)
                    .where(evaluation_pack_version.c.pack_id == matching_pack['id'])
                    .order_by(evaluation_pack_version.c.created_at.desc())
                ).fetchall()
                
                if pack_versions:
                    pack_version = dict(pack_versions[0]._mapping)
                    
                    # Create 3-5 monitoring snapshots
                    for i in range(random.randint(3, 5)):
                        snapshot_id = f"mon_eval_{model_data['id']}_{uuid4().hex[:8]}"
                        
                        metrics = generate_metrics_for_family(model_data['model_family'])
                        results_json, status = evaluate_run(metrics, pack_version['pack_json'])
                        
                        monitor_eval_snapshot = {
                            'id': snapshot_id,
                            'model_id': model_data['id'],
                            'captured_at': datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                            'pack_id': matching_pack['id'],
                            'pack_version_id': pack_version['version_id'],
                            'status': status,
                            'results_json': results_json
                        }
                        
                        monitor_eval_snapshots_data.append(monitor_eval_snapshot)
                    
                    print(f"   ✓ Created monitoring evals for {model_data['name']}")
        
        if monitor_eval_snapshots_data:
            conn.execute(monitor_evaluation_snapshot.insert(), monitor_eval_snapshots_data)
            conn.commit()
        
        print(f"   ✓ Created {len(monitor_eval_snapshots_data)} monitoring evaluation snapshots\n")
        
        # Summary
        print("=" * 70)
        print("✨ Seeding Complete! Summary:")
        print("=" * 70)
        print(f"✓ {len(recipes)} ML Recipes (baseline)")
        print(f"✓ {len(packs)} Evaluation Packs (baseline)")
        print(f"✓ {attachments_created} Recipe-Pack Attachments")
        print(f"✓ {len(models_data)} ML Models")
        print(f"✓ {len(runs_data)} Runs (train/eval/backtest)")
        print(f"✓ {len(monitor_snapshots_data)} Monitoring Snapshots")
        print(f"✓ {len(eval_results_data)} Evaluation Results")
        print(f"✓ {len(monitor_eval_snapshots_data)} Monitoring Evaluation Snapshots")
        print("=" * 70)
        print("\n🎉 All ML Model Development components are now seeded!")
        print("   Open http://localhost:3000/model-development to explore!")


def generate_metrics_for_family(model_family: str) -> dict:
    """Generate realistic metrics based on model family."""
    if model_family == 'forecasting':
        return {
            'MAPE': random.uniform(0.10, 0.30),
            'RMSE': random.uniform(30, 120),
            'MAE': random.uniform(20, 80),
            'forecast_bias': random.uniform(-0.1, 0.1),
            'coverage_80': random.uniform(0.70, 0.90)
        }
    elif model_family == 'pricing':
        return {
            'revenue_lift': random.uniform(0.01, 0.08),
            'margin_impact': random.uniform(0.02, 0.10),
            'elasticity_accuracy': random.uniform(0.10, 0.40),
            'calibration': random.uniform(0.80, 0.98),
            'constraint_violations': random.uniform(0.0, 0.05)
        }
    elif model_family == 'next_best_action':
        return {
            'uplift': random.uniform(0.05, 0.18),
            'precision_at_10': random.uniform(0.15, 0.40),
            'qini_coefficient': random.uniform(0.08, 0.20),
            'incremental_revenue': random.uniform(50000, 150000),
            'action_distribution': random.uniform(0.60, 0.85)
        }
    elif model_family == 'location_scoring':
        return {
            'rank_correlation': random.uniform(0.60, 0.85),
            'calibration': random.uniform(0.75, 0.95),
            'hit_rate_at_10': random.uniform(0.30, 0.60),
            'lift_top_decile': random.uniform(1.5, 3.0),
            'geographic_coverage': random.uniform(0.80, 0.95)
        }
    else:
        return {}


def evaluate_run(metrics: dict, pack_json: dict) -> tuple[dict, str]:
    """Evaluate metrics against pack thresholds."""
    results = {
        'metrics': [],
        'slices': [],
        'comparators': []
    }
    
    overall_status = 'pass'
    
    for metric_def in pack_json.get('metrics', []):
        metric_key = metric_def['key']
        actual_value = metrics.get(metric_key, 0)
        
        thresholds = metric_def.get('thresholds', {})
        direction = metric_def.get('direction', 'higher_is_better')
        
        # Check thresholds
        metric_status = check_threshold(actual_value, thresholds, direction)
        
        results['metrics'].append({
            'key': metric_key,
            'display_name': metric_def.get('display_name', metric_key),
            'actual_value': actual_value,
            'thresholds': thresholds,
            'status': metric_status,
            'direction': direction
        })
        
        # Update overall status
        if metric_status == 'fail':
            overall_status = 'fail'
        elif metric_status == 'warn' and overall_status != 'fail':
            overall_status = 'warn'
    
    return results, overall_status


def check_threshold(value: float, thresholds: dict, direction: str) -> str:
    """Check if a value passes thresholds."""
    promote = thresholds.get('promote')
    warn = thresholds.get('warn')
    fail = thresholds.get('fail')
    
    if direction == 'lower_is_better':
        if fail and value >= fail:
            return 'fail'
        elif warn and value >= warn:
            return 'warn'
        elif promote and value <= promote:
            return 'pass'
        else:
            return 'pass'
    else:  # higher_is_better
        if fail and value <= fail:
            return 'fail'
        elif warn and value <= warn:
            return 'warn'
        elif promote and value >= promote:
            return 'pass'
        else:
            return 'pass'


def generate_summary(results_json: dict, status: str) -> str:
    """Generate human-readable summary."""
    metrics = results_json.get('metrics', [])
    total = len(metrics)
    passed = sum(1 for m in metrics if m['status'] == 'pass')
    warned = sum(1 for m in metrics if m['status'] == 'warn')
    failed = sum(1 for m in metrics if m['status'] == 'fail')
    
    return f"Evaluation {status.upper()}: {passed}/{total} metrics passed, {warned} warnings, {failed} failures"


if __name__ == "__main__":
    seed_complete_ml_data()

