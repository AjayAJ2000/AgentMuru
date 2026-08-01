from scripts.generate_component_reference import sample_arg


def test_sample_arg_uses_fallback_data_for_unknown_component() -> None:
    assert sample_arg("UnknownComponent", "data") == (
        'data=[{"label": "Item", "value": 1}]'
    )
