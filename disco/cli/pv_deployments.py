import json
import logging
import sys
from types import SimpleNamespace

import click

from jade.loggers import setup_logging
from disco.enums import Placement
from disco.sources.source_tree_1.pv_deployments import (
    DeploymentHierarchy,
    DeploymentCategory,
    PVDataStorage,
    PVDeploymentManager,
    PVConfigManager
)

HIERARCHY_CHOICE = [item.value for item in DeploymentHierarchy]
CATEGORY_CHOICE = [item.value for item in DeploymentCategory]
PLACEMENT_CHOICE = [item.value for item in Placement]


def create_pv_deployments(input_path: str, hierarchy: str, config: dict):
    """A method for generating pv deployments"""
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    if not config.placement:
        print(f"'-p' or '--placement' should not be None for this action, choose from {PLACEMENT_CHOICE}")
        sys.exit()
    manager = PVDeploymentManager(input_path, hierarchy, config)
    summary = manager.generate_pv_deployments()
    print(json.dumps(summary, indent=2))


def create_pv_configs(input_path: str, hierarchy: str, config: dict):
    """A method for generating pv config JSON files """
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    if not config.placement:
        print(f"'-p' or '--placement' should not be None for this action, choose from {PLACEMENT_CHOICE}")
        sys.exit()
    manager = PVConfigManager(input_path, hierarchy, config)
    config_files = manager.generate_pv_configs()
    print(f"PV configs created! Total: {len(config_files)}")


def remove_pv_deployments(input_path: str, hierarchy: str, config: dict):
    """A method for removing deployed pv systems"""
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    manager = PVDeploymentManager(input_path, hierarchy, config)
    if config.placement:
        placement = Placement(config.placement)
    else:
        placement = config.placement
    result = manager.remove_pv_deployments(placement=placement)
    print(f"=========\nTotal removed deployments: {len(result)}")


def check_pv_deployments(input_path: str, hierarchy: str, config: dict):
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    manager = PVDeploymentManager(input_path, hierarchy, config)
    if config.placement:
        placement = Placement(config.placement)
    else:
        placement = config.placement
    result = manager.check_pv_deployments(placement=placement)
    print(json.dumps(result.__dict__, indent=2))


def remove_pv_configs(input_path: str, hierarchy: str, config: dict):
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    manager = PVConfigManager(input_path, hierarchy, config)
    if config.placement:
        placement = Placement(config.placement)
    else:
        placement = config.placement
    config_files = manager.remove_pv_configs(placement=placement)
    print(f"PV configs created! Total: {len(config_files)}")


def check_pv_configs(input_path: str, hierarchy: str, config: dict):
    hierarchy = DeploymentHierarchy(hierarchy)
    config = SimpleNamespace(**config)
    manager = PVConfigManager(input_path, hierarchy, config)
    if config.placement:
        placement = Placement(config.placement)
    else:
        placement = config.placement
    total_missing = manager.check_pv_configs(placement=placement)
    print(json.dumps(total_missing, indent=2))


def list_feeder_paths(input_path: str, hierarchy: str, config: dict):
    hierarchy = DeploymentHierarchy(hierarchy)
    storage = PVDataStorage(input_path, hierarchy)
    result = storage.get_feeder_paths()
    for feeder_path in result:
        print(feeder_path)
    print(f"=========\nTotal feeders: {len(result)}")



ACTION_MAPPING = {
    "create-pv": create_pv_deployments,
    "remove-pv": remove_pv_deployments,
    "check-pv": check_pv_deployments,
    "create-configs": create_pv_configs,
    "remove-configs": remove_pv_configs,
    "check-configs": check_pv_configs,
    "list-feeders": list_feeder_paths
}

@click.group()
def pv_deployments():
    """Generate PV deployments from raw OpenDSS models"""


@click.command()
@click.argument("input_path")
@click.option(
    "-a", "--action",
    type=click.Choice(list(ACTION_MAPPING.keys()), case_sensitive=False),
    required=True,
    help="Choose the action related to pv deployments"
)
@click.option(
    "-h", "--hierarchy",
    type=click.Choice(HIERARCHY_CHOICE, case_sensitive=False),
    required=True,
    help="Choose the deployment hierarchy."
)
@click.option(
    "-p", "--placement",
    type=click.Choice(PLACEMENT_CHOICE, case_sensitive=False),
    required=False,
    default=None,
    show_default=True,
    help="Choose the placement type"
)
@click.option(
    "-c", "--category",
    type=click.Choice(CATEGORY_CHOICE, case_sensitive=False),
    default=DeploymentCategory.SMALL.value,
    show_default=True,
    help="The PV size pdf value"
)
@click.option(
    "-f", "--master-filename",
    type=click.STRING,
    required=False,
    default="Master.dss",
    show_default=True,
    help="The filename of master dss"
)
@click.option(
  "-m", "--min-penetration",
    type=click.INT,
    default=5,
    show_default=True,
    help="The minimum level of PV penetration."
)
@click.option(
    "-M", "--max-penetration",
    type=click.INT,
    default=200,
    show_default=True,
    help="The maximum level of PV penetration."
)
@click.option(
   "-s", "--penetration-step",
    type=click.INT,
    default=5,
    show_default=5,
    help="The step of penetration level."
)
@click.option(
    "-n", "--sample-number",
    type=click.INT,
    default=10,
    show_default=True,
    help="The number of deployments"
)
@click.option(
    "-S", "--proximity-step",
    type=click.INT,
    default=10,
    show_default=True,
    help="The proximity step in PV deployments."
)
@click.option(
    "-P", "--percent-shares",
    default=[100, 0],
    show_default=True,
    help="The share pair - [share of residential PVs, share of utility scale PVs]"
)
@click.option(
    "-x", "--pv-size-pdf",
    type=click.INT,
    default=None,
    show_default=True,
    help="The PV size pdf value"
)
@click.option(
    "--pv-upscale/--no-pv-upscale",
    is_flag=True,
    default=True,
    show_default=True,
    help="Upscale PV in deployments."
)
@click.option(
    "--verbose",
    type=click.BOOL,
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable to show overbose information."
)
def source_tree_1(
    input_path,
    action,
    hierarchy,
    placement,
    category,
    master_filename,
    min_penetration,
    max_penetration,
    penetration_step,
    sample_number,
    proximity_step,
    percent_shares,
    pv_size_pdf,
    pv_upscale,
    verbose
):
    """Generate PV deployments for source tree 1."""
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging("pv_deployments", None, console_level=level)
    config = {
        "placement": placement,
        "category": category,
        "master_filename": master_filename,
        "pv_upscale": pv_upscale,
        "min_penetration": min_penetration,
        "max_penetration": max_penetration,
        "penetration_step": penetration_step,
        "sample_number": sample_number,
        "proximity_step": proximity_step,
        "percent_shares": [100, 0],
        "pv_size_pdf": pv_size_pdf
    }
    action_function = ACTION_MAPPING[action]
    action_function(input_path, hierarchy, config)


pv_deployments.add_command(source_tree_1)