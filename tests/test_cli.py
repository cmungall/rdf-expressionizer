import pytest
from rdf_expressionizer.cli import main

from tests.test_main import INPUT_DIR, OUTPUT_DIR


def test_help(runner):
    """
    Tests help message

    :param runner:
    :return:
    """
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "replace" in result.output
    result = runner.invoke(main, ["replace", "--help"])
    assert result.exit_code == 0


DISPOSITION = "http://purl.obolibrary.org/obo/BFO_0000016"
X_DISPOSITION = "https://w3id.org/xbfo/0000016"
CONTINUANT = "http://purl.obolibrary.org/obo/BFO_0000002"
X_CONTINUANT = "https://w3id.org/xbfo/0000002"


@pytest.mark.parametrize(
    "input_name,mappings_path,subset,expected,unexpected",
    [
        ("ro.owl", "bfo_xbfo_mappings", None, [X_CONTINUANT, X_DISPOSITION], [CONTINUANT, DISPOSITION]),
        (
            "ro.owl",
            "bfo_xbfo_mappings",
            "COB",
            [X_CONTINUANT, DISPOSITION],
            [CONTINUANT, X_DISPOSITION],
        ),
    ],
)
def test_cli_replace(runner, input_name, mappings_path, subset, expected, unexpected):
    """
    Tests repair command

    :param runner:
    :return:
    """
    input_file = INPUT_DIR / input_name
    output_file = OUTPUT_DIR / "xro-cli.owl"
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    args = ["replace", "-m", mappings_path, str(input_file), "-o", str(output_file)]
    if subset:
        args.extend(["-x", subset])
    result = runner.invoke(main, args)
    if result.exit_code != 0:
        print(f"OUTPUT: {result.output}")
    assert result.exit_code == 0
    # test file contents
    for expected_str in expected:
        with open(output_file) as stream:
            assert expected_str in stream.read()
    for unexpected_str in unexpected:
        with open(output_file) as stream:
            assert unexpected_str not in stream.read()


@pytest.mark.parametrize(
    "input_name,mappings_path,subset,expected,unexpected",
    [
        ("cob.owl", "bfo_xbfo_mappings", None, [DISPOSITION, X_DISPOSITION], [CONTINUANT]),
    ],
)
def test_cli_augment(runner, input_name, mappings_path, subset, expected, unexpected):
    """
    Tests augment command

    :param runner:
    :return:
    """
    input_file = INPUT_DIR / input_name
    output_file = OUTPUT_DIR / "xcob-cli.owl"
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    args = ["augment", "-m", mappings_path, str(input_file), "-o", str(output_file)]
    result = runner.invoke(main, args)
    if result.exit_code != 0:
        print(f"OUTPUT: {result.output}")
    assert result.exit_code == 0
    # test file contents
    for expected_str in expected:
        with open(output_file) as stream:
            assert expected_str in stream.read()
    for unexpected_str in unexpected:
        with open(output_file) as stream:
            assert unexpected_str not in stream.read()
