#  Copyright (c) 2022. 3Docx.org, see the LICENSE.

from .context import validate3Docx
from click.testing import CliRunner

def test_model_version(capsys, example_fixture):
    # pylint: disable=W0612,W0613
    runner = CliRunner()
    result = runner.invoke(validate3Docx, ['models/NAPA-OHCM_MID-SHIP-V286.3docx'])
    #                                       '--print_source'])
    # assert result.exit_code == 0
    assert 'ERROR' not in result.output
    # assert 0
