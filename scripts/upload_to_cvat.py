#!/usr/bin/env python3
"""Upload crops to CVAT for color annotation.

Creates a CVAT project and task with color labels, then uploads cropped images.

Usage:
    python scripts/upload_to_cvat.py --manifest data/manifests/manifest_raw.jsonl
    python scripts/upload_to_cvat.py --crops-dir data/crops --project-name "VCR Colors"
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.manifest_io import read_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default color labels for VCR
DEFAULT_COLOR_LABELS = [
    "white",
    "black",
    "silver",
    "gray",
    "red",
    "blue",
    "green",
    "yellow",
    "orange",
    "brown",
    "beige",
    "gold",
    "purple",
    "pink",
    "navy",
    "maroon",
    "cyan",
    "other",
]


def get_crop_paths_from_manifest(manifest_path: Path) -> list[Path]:
    """Extract crop paths from manifest."""
    records = read_manifest(manifest_path)
    crop_paths = []
    for record in records:
        if "crop_path" in record:
            crop_paths.append(Path(record["crop_path"]))
    return crop_paths


def get_crop_paths_from_dir(crops_dir: Path) -> list[Path]:
    """Get all image files from crops directory."""
    extensions = (".jpg", ".jpeg", ".png")
    crop_paths = []
    for ext in extensions:
        crop_paths.extend(crops_dir.glob(f"*{ext}"))
        crop_paths.extend(crops_dir.glob(f"*{ext.upper()}"))
    return sorted(crop_paths)


def create_project_with_labels(
    client,
    project_name: str,
    labels: list[str],
) -> int:
    """Create a CVAT project with color labels.

    Returns:
        Project ID.
    """
    # Build label specifications for classification
    label_specs = []
    for label_name in labels:
        label_specs.append({
            "name": label_name,
            "type": "tag",  # Tag type for classification
        })

    project = client.projects.create(
        spec={
            "name": project_name,
            "labels": label_specs,
        }
    )

    logger.info(f"Created project '{project_name}' with ID {project.id}")
    return project.id


def create_task_and_upload(
    client,
    project_id: int,
    task_name: str,
    image_paths: list[Path],
) -> int:
    """Create a task and upload images.

    Returns:
        Task ID.
    """
    # Create task
    task = client.tasks.create_from_data(
        spec={
            "name": task_name,
            "project_id": project_id,
        },
        resource_type=ResourceType.LOCAL,
        resources=[str(p) for p in image_paths],
    )

    logger.info(f"Created task '{task_name}' with ID {task.id}, uploaded {len(image_paths)} images")
    return task.id


def upload_to_cvat(
    host: str,
    username: str,
    password: str,
    project_name: str,
    task_name: str,
    image_paths: list[Path],
    labels: list[str],
) -> dict:
    """Upload images to CVAT.

    Returns:
        Dict with project_id and task_id.
    """
    logger.info(f"Connecting to CVAT at {host}...")

    with make_client(host=host, credentials=(username, password)) as client:
        # Create project
        project_id = create_project_with_labels(client, project_name, labels)

        # Create task and upload
        task_id = create_task_and_upload(client, project_id, task_name, image_paths)

    return {
        "project_id": project_id,
        "task_id": task_id,
        "url": f"{host}/projects/{project_id}",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload crops to CVAT for color annotation.",
    )

    parser.add_argument(
        "--manifest",
        type=str,
        help="Path to manifest file (extracts crop_path from each record)",
    )
    parser.add_argument(
        "--crops-dir",
        type=str,
        help="Directory with crop images (alternative to --manifest)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("CVAT_HOST", "http://localhost:8080"),
        help="CVAT host URL (default: $CVAT_HOST or http://localhost:8080)",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=os.environ.get("CVAT_USERNAME", "admin"),
        help="CVAT username (default: $CVAT_USERNAME or admin)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=os.environ.get("CVAT_PASSWORD"),
        help="CVAT password (default: $CVAT_PASSWORD)",
    )
    parser.add_argument(
        "--project-name",
        type=str,
        help="CVAT project name (default: auto-generated)",
    )
    parser.add_argument(
        "--task-name",
        type=str,
        help="CVAT task name (default: auto-generated)",
    )
    parser.add_argument(
        "--labels",
        type=str,
        nargs="+",
        default=DEFAULT_COLOR_LABELS,
        help="Color labels to create in CVAT",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Get image paths
    if args.manifest:
        image_paths = get_crop_paths_from_manifest(Path(args.manifest))
    elif args.crops_dir:
        image_paths = get_crop_paths_from_dir(Path(args.crops_dir))
    else:
        logger.error("Either --manifest or --crops-dir is required")
        return 1

    if not image_paths:
        logger.error("No images found")
        return 1

    logger.info(f"Found {len(image_paths)} images to upload")

    # Validate credentials
    if not args.password:
        logger.error("CVAT password required. Set $CVAT_PASSWORD or use --password")
        return 1

    # Generate names if not provided
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = args.project_name or f"VCR_Colors_{timestamp}"
    task_name = args.task_name or f"crops_{timestamp}"

    # Upload
    result = upload_to_cvat(
        host=args.host,
        username=args.username,
        password=args.password,
        project_name=project_name,
        task_name=task_name,
        image_paths=image_paths,
        labels=args.labels,
    )

    logger.info(f"Done! Project URL: {result['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
