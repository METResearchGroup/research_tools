import pathlib
from typing import Callable, Iterable

from src.research_tools.lib.timestamp_utils import get_current_timestamp


def write_pre_run_metadata(
    full_output_folder: pathlib.Path,
    start_timestamp: str
):
    metadata = {
        "start_timestamp": "",
        "total_items": 0,
        "run_metadata": {}
    }
    # write to storage

def write_post_run_metadata(
    full_output_folder: pathlib.Path,
    end_timestamp: str
):
    metadata = {"end_timestamp": end_timestamp}
    # write to storage

def run(
    items: Iterable,
    writer_map_fn: Callable,
    writer_map_kwargs: dict,
    output_base_path: str
):
    start_timestamp = get_current_timestamp()
    full_output_folder = output_base_path.rstrip('/') + '/outputs/' + start_timestamp
    full_output_folder = pathlib.Path(
        full_output_folder=full_output_folder,
        start_timestamp=start_timestamp
    )
    write_pre_run_metadata(full_output_folder)

    for item in items:
        prompt = build_prompt_with_stimuli()
        result: IsRemoveResult = LLMService(prompt)
        write_row_dict = map_fn(result, **map_kwargs)
        write_result(output_base_path)
    write_post_run_metadata(output_bash_path)
