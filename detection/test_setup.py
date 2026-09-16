"""Tests use mocks and temporary files; no camera, weights or inference needed."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location("detector", Path(__file__).with_name("run.py"))
detector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(detector)


class SetupTests(unittest.TestCase):
    def test_gpu_operator_error_is_not_ignored(self):
        torch = Mock()
        torch.tensor.side_effect = RuntimeError("no kernel image")
        with self.assertRaisesRegex(RuntimeError, "no kernel image"):
            detector.check_gpu_ops(torch, Mock())

    def test_check_returns_before_camera_or_model_import(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "must-not-exist"
            with patch.object(sys, "argv", ["run.py", "--check", "--output", str(output)]), \
                    patch.object(detector, "preflight", return_value={"inference_tested": False}), \
                    patch.dict(sys.modules, {"cv2": None, "torch": None, "ultralytics": None}), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(detector.main(), 0)
            self.assertFalse(output.exists())

    def test_failed_preflight_stops_before_capture(self):
        with patch.object(sys, "argv", ["run.py"]), \
                patch.object(detector, "preflight", side_effect=RuntimeError("CUDA unavailable")), \
                patch.dict(sys.modules, {"cv2": None, "ultralytics": None}), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(detector.main(), 1)

    def test_invalid_runtime_parameters(self):
        for args in [["--seconds", "nan"], ["--seconds", "-1"], ["--seconds", "301"],
                     ["--conf", "-1"], ["--conf", "2"]]:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                detector.parse_args(args)

    def test_atomic_preview_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "latest.jpg"
            detector.atomic_write(path, b"old")
            detector.atomic_write(path, b"new")
            self.assertEqual(path.read_bytes(), b"new")
            self.assertEqual(list(Path(temp).iterdir()), [path])

    def test_launcher_no_arguments_and_check_do_not_add_empty_argument(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            ssh = temp / "ssh"
            log = temp / "ssh.log"
            ssh.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$SSH_TEST_LOG"\n')
            ssh.chmod(0o755)
            env = {**os.environ, "PATH": str(temp) + ":" + os.environ["PATH"], "SSH_TEST_LOG": str(log)}
            launcher = str(Path(__file__).with_name("launch.sh"))
            subprocess.run(["bash", launcher, "--check"], env=env, check=True, capture_output=True)
            lines = log.read_text().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertIn("start.sh --check", lines[0])
            log.unlink()
            subprocess.run(["bash", launcher], env=env, check=True, capture_output=True)
            lines = log.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertNotIn("''", lines[0])
            self.assertIn("-N", lines[1])


if __name__ == "__main__":
    unittest.main()
