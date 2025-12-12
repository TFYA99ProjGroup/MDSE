# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from unittest.mock import patch, MagicMock
from mdse.cli import create_parser, simulate_mpi


def test_simulate_calls_runmanager():
    parser = create_parser()
    args = parser.parse_args(["simulate", "-f", "config.yaml", "-c", "Ensamble=NVT"])

    with (
        patch("mdse.cli.main_read") as mock_main_read,
        patch("mdse.cli.RunManager") as mock_RunManager,
    ):
        mock_main_read.return_value = ["sim1", "sim2"]

        mock_rm_instance = MagicMock()
        mock_RunManager.return_value = mock_rm_instance

        args.func(args)

        mock_main_read.assert_called_once_with("config.yaml", {"Ensamble": "NVT"})
        mock_RunManager.assert_called_once_with(["sim1", "sim2"])


def test_simulate_mpi_calls_runmanager():
    class Args:
        filepath = "config.yaml"
        config = ["Ensamble=NVT"]
        mpi = True

    args = Args()

    with (
        patch("mpi4py.MPI") as mock_MPI,
        patch("mdse.cli.main_read") as mock_main_read,
        patch("mdse.cli.RunManager") as mock_RunManager,
    ):
        mock_comm = MagicMock()
        mock_comm.Get_rank.return_value = 0
        mock_comm.Get_size.return_value = 4
        mock_MPI.COMM_WORLD = mock_comm

        mock_main_read.return_value = ["sim1"]
        mock_rm_instance = MagicMock()
        mock_RunManager.return_value = mock_rm_instance

        simulate_mpi(args)

        mock_main_read.assert_called_once_with("config.yaml", {"Ensamble": "NVT"})
        mock_RunManager.assert_called_once_with(["sim1"])


def test_calc_msd_calls():
    parser = create_parser()
    args = parser.parse_args(["msd", "-f", "file1.traj", "file2.traj"])

    with patch("mdse.cli.ResultMD") as mock_ResultMD:
        mock_instance = assert_from_file(mock_ResultMD, args)

        assert mock_instance.visualize_msd.call_count == 2


def test_calc_lindemann_calls():
    parser = create_parser()
    args = parser.parse_args(["lindemann", "-f", "file1.traj", "file2.traj"])

    with patch("mdse.cli.ResultMD") as mock_ResultMD:
        assert_from_file(mock_ResultMD, args)


def test_calc_self_diff_calls():
    parser = create_parser()
    args = parser.parse_args(["self_diff", "-f", "file1.traj", "file2.traj"])

    with patch("mdse.cli.ResultMD") as mock_ResultMD:
        assert_from_file(mock_ResultMD, args)


def test_calc_ish_calls():
    parser = create_parser()
    args = parser.parse_args(["ish", "-f", "file1.traj", "file2.traj"])

    with patch("mdse.cli.ResultMD") as mock_ResultMD:
        assert_from_file(mock_ResultMD, args)


def test_write_to_database_calls_dbmanager_write():
    parser = create_parser()
    args = parser.parse_args(
        [
            "write_db",
            "-a",
            "mongodb://db/",
            "-f",
            "data1.json",
            "data2.json",
        ]
    )

    with patch("mdse.cli.DBManager") as mock_DBManager:
        mock_instance = MagicMock()
        mock_DBManager.return_value = mock_instance

        args.func(args)

        mock_DBManager.assert_called_once_with("mongodb://db/")

        mock_instance.write_jsonfiles_to_db.assert_any_call("data1.json")
        mock_instance.write_jsonfiles_to_db.assert_any_call("data2.json")
        assert mock_instance.write_jsonfiles_to_db.call_count == 2


def test_visualize_DB_calls_run_visualize_db():
    parser = create_parser()
    args = parser.parse_args(["visualize", "-f", "mongodb://db/"])

    with patch("mdse.cli.run_visualize_db") as mock_visualize:
        args.func(args)

        mock_visualize.assert_called_once_with("mongodb://db/")


def assert_from_file(mock_object, args):
    """From file function is used in multiple calculation tests"""
    mock_instance = MagicMock()
    mock_object.from_file.side_effect = [mock_instance, mock_instance]
    args.func(args)

    mock_object.from_file.assert_any_call("file1.traj")
    mock_object.from_file.assert_any_call("file2.traj")
    assert mock_object.from_file.call_count == 2
    return mock_instance
