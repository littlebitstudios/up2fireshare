import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import xxhash

from up2fireshare import _media_id, load_config, main, upload_file


class Up2FireshareTest(unittest.TestCase):
    def test_main_uploads_files_from_folder_using_folder_name_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "match"
            folder.mkdir()
            (folder / "clip.mp4").touch()
            nested_folder = folder / "nested"
            nested_folder.mkdir()
            (nested_folder / "nested-clip.mp4").touch()

            with (
                patch.object(sys, "argv", ["up2fireshare", str(folder)]),
                patch(
                    "up2fireshare.load_config",
                    return_value={"server": "https://fireshare.example.com", "token": "secret"},
                ),
                patch("up2fireshare.get_user_data", return_value=None),
                patch("up2fireshare.upload_file", return_value={"status": "accepted"}) as upload,
            ):
                self.assertEqual(main(), 0)

        self.assertEqual(upload.call_count, 1)
        self.assertEqual(upload.call_args.args[0], str(folder / "clip.mp4"))
        self.assertEqual(upload.call_args.kwargs["folder"], "match")

    def test_main_recursively_uploads_files_using_each_parent_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "match"
            nested_folder = folder / "round-1"
            nested_folder.mkdir(parents=True)
            (folder / "clip.mp4").touch()
            (nested_folder / "nested-clip.mp4").touch()

            with (
                patch.object(sys, "argv", ["up2fireshare", "-r", str(folder)]),
                patch(
                    "up2fireshare.load_config",
                    return_value={"server": "https://fireshare.example.com", "token": "secret"},
                ),
                patch("up2fireshare.get_user_data", return_value=None),
                patch("up2fireshare.upload_file", return_value={"status": "accepted"}) as upload,
            ):
                self.assertEqual(main(), 0)

        self.assertEqual(
            [
                (Path(call.args[0]).name, call.kwargs["folder"])
                for call in upload.call_args_list
            ],
            [("clip.mp4", "match"), ("nested-clip.mp4", "round-1")],
        )

    def test_main_explicit_folder_overrides_folder_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "match"
            folder.mkdir()
            (folder / "clip.mp4").touch()

            with (
                patch.object(
                    sys, "argv", ["up2fireshare", str(folder), "-f", "manual-folder"]
                ),
                patch(
                    "up2fireshare.load_config",
                    return_value={"server": "https://fireshare.example.com", "token": "secret"},
                ),
                patch("up2fireshare.get_user_data", return_value=None),
                patch("up2fireshare.upload_file", return_value={"status": "accepted"}) as upload,
            ):
                self.assertEqual(main(), 0)

        self.assertEqual(upload.call_args.kwargs["folder"], "manual-folder")

    def test_main_rejects_title_for_folder_with_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "match"
            folder.mkdir()
            (folder / "first.mp4").touch()
            (folder / "second.mp4").touch()

            with (
                patch.object(
                    sys, "argv", ["up2fireshare", str(folder), "--name", "Title"]
                ),
                patch("up2fireshare.load_config") as load_config_mock,
            ):
                with self.assertRaises(SystemExit) as exit_context:
                    main()

        self.assertEqual(exit_context.exception.code, 2)
        load_config_mock.assert_not_called()

    def test_main_rejects_title_option_with_multiple_files(self):
        for title_option in ("-n", "--name"):
            with self.subTest(title_option=title_option):
                with (
                    patch.object(
                        sys,
                        "argv",
                        ["up2fireshare", "first.mp4", "second.mp4", title_option, "Title"],
                    ),
                    patch("up2fireshare.load_config") as load_config_mock,
                ):
                    with self.assertRaises(SystemExit) as exit_context:
                        main()

                self.assertEqual(exit_context.exception.code, 2)
                load_config_mock.assert_not_called()

    def test_media_id_hashes_only_the_first_16_mib(self):
        prefix = b"a" * (16 * 1024 * 1024)
        with tempfile.NamedTemporaryFile("wb", suffix=".mp4") as tmp:
            tmp.write(prefix + b"not part of the id")
            tmp.flush()

            self.assertEqual(
                _media_id(tmp.name),
                ("video_id", xxhash.xxh3_128(prefix).hexdigest()),
            )

    def test_load_config_reads_server_and_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            config_dir = home / ".littlebitstudios" / "up2fireshare"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                "server: https://fireshare.example.com\n"
                "token: fsk_secret\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                self.assertEqual(
                    load_config(),
                    {"server": "https://fireshare.example.com", "token": "fsk_secret"},
                )

    def test_upload_file_uses_bearer_token_and_upload_endpoint(self):
        with tempfile.NamedTemporaryFile("wb", suffix=".mp4", delete=False) as tmp:
            tmp.write(b"video")
            tmp_path = tmp.name

        response = MagicMock(status_code=201)
        response.json.return_value = {"status": "accepted"}
        exists_response = MagicMock()
        exists_response.json.return_value = {"exists": False}

        try:
            with (
                patch("up2fireshare.requests.get", return_value=exists_response) as get,
                patch("up2fireshare.requests.post", return_value=response) as post,
            ):
                result = upload_file(
                    tmp_path,
                    "https://fireshare.example.com",
                    "fsk_secret",
                    title="Title",
                    folder="uploads",
                    game="VALORANT",
                    tags="1,2",
                )

                self.assertEqual(result["status"], "accepted")
                get.assert_called_once_with(
                    "https://fireshare.example.com/api/upload/token/exists",
                    params={"video_id": xxhash.xxh3_128(b"video").hexdigest()},
                    headers={"Authorization": "Bearer fsk_secret"},
                    timeout=60,
                )
                post.assert_called_once()
                self.assertEqual(
                    post.call_args.args[0],
                    "https://fireshare.example.com/api/upload/token",
                )
                self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer fsk_secret")
                self.assertEqual(post.call_args.kwargs["data"]["title"], "Title")
                self.assertEqual(post.call_args.kwargs["data"]["folder"], "uploads")
                self.assertEqual(post.call_args.kwargs["data"]["game"], "VALORANT")
                self.assertEqual(post.call_args.kwargs["data"]["tag_ids"], "1,2")
                self.assertIn("file", post.call_args.kwargs["files"])
        finally:
            os.unlink(tmp_path)

    def test_upload_file_skips_upload_when_image_already_exists(self):
        with tempfile.NamedTemporaryFile("wb", suffix=".png", delete=False) as tmp:
            tmp.write(b"image")
            tmp_path = tmp.name

        exists_result = {
            "exists": True,
            "image_id": xxhash.xxh3_128(b"image").hexdigest(),
            "title": "Existing image",
            "url": "/i/existing",
        }
        exists_response = MagicMock()
        exists_response.json.return_value = exists_result

        try:
            with (
                patch("up2fireshare.requests.get", return_value=exists_response) as get,
                patch("up2fireshare.requests.post") as post,
            ):
                result = upload_file(
                    tmp_path,
                    "https://fireshare.example.com",
                    "fsk_secret",
                )

                self.assertEqual(result, exists_result)
                get.assert_called_once_with(
                    "https://fireshare.example.com/api/upload/token/exists",
                    params={"image_id": exists_result["image_id"]},
                    headers={"Authorization": "Bearer fsk_secret"},
                    timeout=60,
                )
                post.assert_not_called()
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
