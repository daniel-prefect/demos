from pathlib import Path
from prefect import flow, task
from prefect_aws import S3Bucket
from typing import Optional
from datetime import datetime
from prefect.artifacts import create_markdown_artifact

@task
def train_model(path: Path) -> object:
    with open(path, 'r') as file:
        contents = file.read()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "contents": contents
    }
    
    return results

@task
def save_results(results: object):
    markdown_content = f"""
## Model Training Results

{results['timestamp']}

{results['contents']}
    """
    create_markdown_artifact(
        key="model-metrics",
        markdown=markdown_content,
        description="Training metrics for the linear regression model"
    )

@task(log_prints=True)
def fetch_updated_data(path: Path):
    s3_bucket = S3Bucket.load("s3-bucket-block")
    try:
        filepath = s3_bucket.download_object_to_path(path, path)
        print(f"File downloaded to: {filepath}")
    except Exception as e:
        raise Exception(f"Failed to fetch {path} from S3: {e}")

@flow(log_prints=True)
def update_model(path: Path):
    path = Path("test.txt")
    fetch_updated_data(path)
    results = train_model(path)
    save_results(results)

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/prefecthq/demos.git",
        entrypoint="train_model.py:update_model",
    ).deploy(
        name="webhook-test",
        work_pool_name="my-managed-pool",
    )