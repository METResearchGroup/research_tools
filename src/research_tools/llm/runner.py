"""Run LLM completions over items with filesystem-backed metadata and results."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable, Iterable
from typing import Any

from pydantic import BaseModel

from research_tools.lib.timestamp_utils import get_current_timestamp
from research_tools.llm_service import LLMService

_METADATA_FILENAME = "metadata.json"


def write_pre_run_metadata(
    full_output_folder: pathlib.Path,
    *,
    start_timestamp: str,
    total_items: int,
    run_metadata: dict[str, Any] | None = None,
) -> None:
    """Write initial run metadata under the output folder."""
    metadata = {
        "start_timestamp": start_timestamp,
        "total_items": total_items,
        "run_metadata": dict(run_metadata or {}),
    }
    path = full_output_folder / _METADATA_FILENAME
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def write_result(
    full_output_folder: pathlib.Path,
    out: dict[str, Any],
    *,
    index: int,
) -> pathlib.Path:
    """Write one result dict as a JSON file under the run folder."""
    current_ts = get_current_timestamp()
    path = full_output_folder / f"{index:05d}_{current_ts}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def write_post_run_metadata(
    full_output_folder: pathlib.Path,
    *,
    end_timestamp: str,
) -> None:
    """Merge end timestamp into the existing metadata file."""
    metadata_path = full_output_folder / _METADATA_FILENAME
    metadata: dict[str, Any] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["end_timestamp"] = end_timestamp
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def run[TResponse: BaseModel](
    items: Iterable[Any],
    *,
    prompt_fn: Callable[[Any], list[dict]],
    response_model: type[TResponse],
    model: str,
    output_base_path: str | pathlib.Path,
    writer_map_fn: Callable[[Any, TResponse], dict[str, Any]],
    run_metadata: dict[str, Any] | None = None,
    **llm_kwargs: Any,
) -> pathlib.Path:
    """
    Run structured completions over a sequence of items and persist results.

    For each item, the function:
        1. Uses `prompt_fn` to generate a prompt.
        2. Calls `LLMService.structured_completion` to produce a response.
        3. Maps the input and response using `writer_map_fn` to create an output dictionary.
        4. Saves each output as an individual JSON file in a newly created run folder.

    Output directory layout::

        {output_base_path}/outputs/{start_timestamp}/
            metadata.json
            00000_{ts}.json
            00001_{ts}.json
            ...

    Parameters
    ----------
    items : Iterable[Any]
        The sequence of input items to process.
    prompt_fn : Callable[[Any], list[dict]]
        Function to generate prompts for each item.
    response_model : type[TResponse]
        The Pydantic model describing the expected response schema.
    model : str
        Name of the language model to use for generation.
    output_base_path : str or pathlib.Path
        Base path for the output folders.
    writer_map_fn : Callable[[Any, TResponse], dict[str, Any]]
        Function mapping each item and model output to a dict to be written.
    run_metadata : dict[str, Any], optional
        Additional metadata for the run (default is None).
    **llm_kwargs : Any
        Additional keyword arguments passed to the LLM completion call.

    Returns
    -------
    pathlib.Path
        Path to the newly created output folder for this run.

    """
    item_list = list(items)
    start_timestamp = get_current_timestamp()
    full_output_folder = pathlib.Path(output_base_path) / "outputs" / start_timestamp
    full_output_folder.mkdir(parents=True, exist_ok=False)

    metadata = dict(run_metadata or {})
    metadata.setdefault("model", model)

    write_pre_run_metadata(
        full_output_folder,
        start_timestamp=start_timestamp,
        total_items=len(item_list),
        run_metadata=metadata,
    )

    llm = LLMService()
    for index, item in enumerate(item_list):
        messages = prompt_fn(item)
        result = llm.structured_completion(
            messages=messages,
            response_model=response_model,
            model=model,
            **llm_kwargs,
        )
        write_row_dict = writer_map_fn(item, result)
        write_result(full_output_folder, write_row_dict, index=index)

    write_post_run_metadata(
        full_output_folder,
        end_timestamp=get_current_timestamp(),
    )
    return full_output_folder
