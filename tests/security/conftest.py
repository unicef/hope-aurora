from pathlib import Path

import pytest
from responses import _recorder


def get_markers_dict(request) -> dict[str, list]:
    return {x.name: x.args[0] for x in request.node.own_markers}


@pytest.fixture
def file_mocked_responses(request: pytest.FixtureRequest, mocked_responses):
    markers = get_markers_dict(request)
    file_path = markers.get("file_path", (Path(request.path.parent) / request.function.__name__).with_suffix(".yaml"))
    record = markers.get("record", False)
    if file_path:
        if record:
            _recorder.recorder.start()
        else:
            mocked_responses._add_from_file(file_path)
    yield
    if file_path and record:
        _recorder.recorder.dump_to_file(file_path)
        _recorder.recorder.stop()
        _recorder.recorder.reset()
