import logging
import os
from typing import List, Tuple

import pytest

import core.config as cfg
import core.config_builders as cfgb
import helpers.git as git
import helpers.system_interaction as si
import helpers.unit_test as hut

_LOG = logging.getLogger(__name__)


@pytest.mark.slow
class TestRunNotebook(hut.TestCase):

    def _get_files(self) -> Tuple[str, str]:
        amp_path = git.get_amp_abs_path()
        exec_file = os.path.join(amp_path,
                                 'dev_scripts/notebooks/run_notebook.py')
        notebook_file = os.path.join(amp_path,
                                     'dev_scripts/notebooks/test/test_run_notebook.ipynb')
        return exec_file, notebook_file

    def test_main1(self) -> None:
        dst_dir = self.get_scratch_space()
        exec_file, notebook_file = self._get_files()
        cmd = (
            f"{exec_file} "
            f"--dst_dir {dst_dir} "
            f"--notebook {notebook_file} "
            "--function 'dev_scripts.test.test_run_notebook.build_configs()' "
            "--skip_on_error "
            "--num_threads 1"
        )
        si.system(cmd)

    def test_main2(self) -> None:
        dst_dir = self.get_scratch_space()
        exec_file, notebook_file = self._get_files()
        cmd = (
            f"{exec_file} "
            f"--dst_dir {dst_dir} "
            f"--notebook {notebook_file} "
            "--function 'dev_scripts.test.test_run_notebook.build_configs()' "
            "--skip_on_error "
            "--num_threads 3"
        )
        si.system(cmd)

    def test_main3(self) -> None:
        dst_dir = self.get_scratch_space()
        exec_file, notebook_file = self._get_files()
        cmd = (
            f"{exec_file} "
            f"--dst_dir {dst_dir} "
            f"--notebook {notebook_file} "
            "--function 'dev_scripts.test.test_run_notebook.build_configs()' "
            "--num_threads 3"
        )
        cmd += " 2>&1 >/dev/null"
        _LOG.warning("This command is supposed to fail")
        rc = si.system(cmd, abort_on_error=False)
        self.assertNotEqual(rc, 0)


def build_configs() -> List[cfg.Config]:
    config_template = cfg.Config()
    config_template["fail"] = None
    configs = cfgb.build_multiple_configs(
        config_template, {("fail",): (False, False, True, False, False)}
    )
    # Duplicate configs are not allowed, so we need to add identifiers for
    # them.
    for i, config in enumerate(configs):
        config["id"] = i
    return configs
