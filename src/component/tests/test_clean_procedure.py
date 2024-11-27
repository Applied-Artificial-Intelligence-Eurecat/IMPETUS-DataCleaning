from procedures.clean_procedure import ZScoreOutlierMask, ZeroMaskImputation, DataCleaner
import numpy as np
import pandas as pd



def test_ZScoreOutlierMask():
    fake_timeseries = np.concatenate((np.random.randint(1,10,20), np.array([98,95,93]),np.random.randint(1,10,20)))
    series = pd.DataFrame( {"avg_speed": fake_timeseries} )['avg_speed']
    mask_object = ZScoreOutlierMask(threshold=2)
    mask = mask_object.generate_mask(series)
    assert (len(mask) == len(series))
    assert mask.dtype == np.bool_


def test_ZeroMaskImputation():
    fake_timeseries = np.arange(10)
    mask= [True]*2 + [False]*5 + [True]*3
    expected_array = np.concatenate(([0, 0], np.arange(2,7) , [0, 0, 0]))
    masked_values = ZeroMaskImputation().clean(fake_timeseries, mask)
    assert (expected_array == masked_values).all()

def test_configuration_mask_cleaning():
    fake_avg_speed = np.concatenate((np.random.randint(1,10,20), np.array([98,95,93]),np.random.randint(1,10,20)))
    expected_avg_speed = np.concatenate((fake_avg_speed[:20], np.array([0,0,0]),fake_avg_speed[23:]))
    fake_max_wind_gust = np.arange(len(fake_avg_speed))

    fake_df = pd.DataFrame( {"avg_speed": fake_avg_speed, "max_wind_gust": fake_max_wind_gust} )

    config = {"api_additional_info":None,"methods": {"avg_speed": [["ZScoreOutlierMask", 1], ["ZeroMaskImputation"]],"max_wind_gust":[]}}
    cleaner = DataCleaner(None, None, config)
    cleaner.data = fake_df.copy()
    cleaner.clean_data(config["methods"])
    clean_df = cleaner.data
    assert (clean_df["max_wind_gust"] == fake_df["max_wind_gust"]).all()
    assert not (clean_df["avg_speed"] == fake_df["avg_speed"]).all()
    assert (expected_avg_speed == clean_df["avg_speed"].values).all()