# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from mdse.visualizeDB.run_visDB import run_visualize_db
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_config_data():
    """Create mock dictionary of data in config .yaml file
    """
    data = {"data" : {"data_source" : "json", "path" : "temp_path"},
            "plots" : {"plot_1" : {"type" : "doping", "average" : True, "fix_y" : True},
                       "plot_2" : {"type" : "scatter", "x" : "temperature", "y" : "MSD",
                                   "z" : "Lindeman"},
                        "plot_3" : {"type" : "ALL_PLOT", "x" : "temperature",
                                    "y" : "MSD",
                                    "z" : "Lindeman"},
                        "plot_4" : {"type" : "scatter", "x" : "speed_per_kelvin",
                                    "y" : "MSD", "z" : "Lindeman"},
                        "plot_5" : {"type" : "heatmap", "x" : "substitution",
                                    "y" : "interstitial"},
                        "plot_6" : {"type" : "single"}
                        }}

    return data


@pytest.fixture
def mock_sim_data():
    """Create mock .json data"""
    data = [
        {"doping": "H",  "avg_a": 1.01, "formation_energy": 1.01,
         "temperature": 300, "MSD": 0.01, "Lindeman": 0.05,
         "DefectInfo": {"defect_type": "Int_C:Int_Rb", "defect_size": 2,
                "vacancy": 0, "substitutional": 0, "interstitial": 1}},

        {"doping": "H",  "avg_a": 1.05, "formation_energy": 1.03,
         "temperature": 310, "MSD": 0.02, "Lindeman": 0.06,
         "DefectInfo": {"defect_type": "Int_C:Int_Rb", "defect_size": 2,
                "vacancy": 0, "substitutional": 0, "interstitial": 1}},

        {"doping": "He", "avg_a": 0.99, "formation_energy": 1.80,
         "temperature": 300, "MSD": 0.015, "Lindeman": 0.055,
         "DefectInfo": {"defect_type": "Int_C:Int_Rb", "defect_size": 2,
                "vacancy": 0, "substitutional": 0, "interstitial": 1}},

        {"doping": "Li", "avg_a": 0.92, "formation_energy": 1.11,
         "temperature": 305, "MSD": 0.012, "Lindeman": 0.052,
         "DefectInfo": {"defect_type": "Int_C:Rb_C", "defect_size": 2,
                "vacancy": 0, "substitutional": 1, "interstitial": 1}},

        {"doping": "Cu", "avg_a": 1.02, "formation_energy": 1.02,
         "temperature": 300, "MSD": 0.02, "Lindeman": 0.05,
         "DefectInfo": {"defect_type": "Int_C:Int_Rb", "defect_size": 2,
                "vacancy": 0, "substitutional": 0, "interstitial": 1}}
    ]

    return data


def test_run_visualize(monkeypatch, mock_config_data, mock_sim_data):
    """Test that above configurations/structure is valid.
    And generates plots.
    Data had 6 plots, 2 which are invalid format. Check so only 4 gets created.
    """

    #Patch read_yaml and read_data in run_vis to use above data.
    monkeypatch.setattr("mdse.visualizeDB.run_visDB.read_yaml_simulations",
                        lambda path: mock_config_data)
    monkeypatch.setattr("mdse.visualizeDB.run_visDB.read_data",
                        lambda data_info: mock_sim_data)

    #Patch so dont greate and save figures.
    dummy_savefig = MagicMock()
    monkeypatch.setattr("matplotlib.pyplot.Figure.savefig", dummy_savefig)
    monkeypatch.setattr("matplotlib.pyplot.close", lambda *args, **kwargs: None)

    run_visualize_db("dummy")

    assert(dummy_savefig.call_count == 4)

    saved_files = [call.args[0] for call in dummy_savefig.call_args_list]

    assert "plot_1.png" in saved_files
    assert "plot_2.png" in saved_files
    assert "plot_3.png" not in saved_files
    assert "plot_4.png" not in saved_files
    assert "plot_5.png" in saved_files
    assert "plot_6.png" in saved_files
