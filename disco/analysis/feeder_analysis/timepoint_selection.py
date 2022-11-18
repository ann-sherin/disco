"""Logic to determine snapshot time point by mode"""

import logging
import enum
import os
from pathlib import Path
import numpy as np
import pandas as pd
import opendssdirect as dss
from datetime import datetime, timedelta
from jade.utils.utils import dump_data

# from PyDSS.common import SnapshotTimePointSelectionMode
# from PyDSS.utils.simulation_utils import create_loadshape_pmult_dataframe_for_simulation
# from PyDSS.utils.utils import dump_data
# from PyDSS.reports.reports import logger
# from PyDSS.simulation_input_models import SimulationSettingsModel


logger = logging.getLogger(__name__)


class SnapshotTimePointSelectionMode(enum.Enum):
    """Defines methods by which snapshot time points can be calculated."""

    MAX_PV_LOAD_RATIO = "max_pv_load_ratio"
    MAX_LOAD = "max_load"
    DAYTIME_MIN_LOAD = "daytime_min_load"
    MAX_PV_MINUS_LOAD = "pv_minus_load"
    NONE = "none"
    
    

def create_loadshape_pmult_dataframe(settings):
    """Return a loadshape dataframe representing all available data, with datetimeindex.
    This assumes that a loadshape has been selected in OpenDSS.
    
    Parameters
    ----------
    settings
    Returns
    -------
    pd.DataFrame
    """
    start_time = settings.loadshape_start_time
    data = dss.LoadShape.PMult()
    interval = timedelta(seconds=dss.LoadShape.SInterval())
    # interval = settings["loadshape_step_time"]
    npts = dss.LoadShape.Npts()

    indices = []
    cur_time = start_time
    for _ in range(npts):
    # or while cur_time < end_time: (where end_time=settings["loadshape_end_time"])
        indices.append(cur_time)
        cur_time += interval

    return pd.DataFrame(data, index=pd.DatetimeIndex(indices))
    

def get_snapshot_timepoint(mode: SnapshotTimePointSelectionMode, output_filename):
    pv_systems = dss.PVsystems.AllNames()
    if not pv_systems:
        logger.info("No PVSystems are present.")
        if mode != SnapshotTimePointSelectionMode.MAX_LOAD:
            mode = SnapshotTimePointSelectionMode.MAX_LOAD
            logger.info("Changed mode to %s", SnapshotTimePointSelectionMode.MAX_LOAD.value)
    if mode == SnapshotTimePointSelectionMode.MAX_LOAD:
        column = "Max Load"
    elif mode == SnapshotTimePointSelectionMode.MAX_PV_LOAD_RATIO:
        column = "Max PV to Load Ratio"
    elif mode == SnapshotTimePointSelectionMode.DAYTIME_MIN_LOAD:
        column = "Min Daytime Load"
    elif mode == SnapshotTimePointSelectionMode.MAX_PV_MINUS_LOAD:
        column = "Max PV minus Load"
    else:
        assert False, f"{mode} is not supported"

    pv_generation_hours = {'start_time': '8:00', 'end_time': '17:00'}
    aggregate_profiles = pd.DataFrame(columns=['Load', 'PV'])
    pv_shapes = {}
    for pv_name in pv_systems:
        dss.PVsystems.Name(pv_name)
        pmpp = float(dss.Properties.Value('Pmpp'))
        profile_name = dss.Properties.Value('yearly')
        dss.LoadShape.Name(profile_name)
        if profile_name not in pv_shapes.keys():
            pv_shapes[profile_name] = create_loadshape_pmult_dataframe(INPUT_SETTINGS)
        if len(aggregate_profiles) == 0:
            aggregate_profiles['PV'] = (pv_shapes[profile_name] * pmpp)[0]
            aggregate_profiles = aggregate_profiles.replace(np.nan, 0)
        else:
            aggregate_profiles['PV'] = aggregate_profiles['PV'] + (pv_shapes[profile_name] * pmpp)[0]
    del pv_shapes
    loads = dss.Loads.AllNames()
    if not loads:
        logger.info("No Loads are present")
    load_shapes = {}
    for load_name in loads:
        dss.Loads.Name(load_name)
        kw = float(dss.Properties.Value('kW'))
        profile_name = dss.Properties.Value('yearly')
        dss.LoadShape.Name(profile_name)
        if profile_name not in load_shapes.keys():
            load_shapes[profile_name] = create_loadshape_pmult_dataframe(INPUT_SETTINGS)
        if len(aggregate_profiles) == 0:
            aggregate_profiles['Load'] = (load_shapes[profile_name] * kw)[0]
        else:
            aggregate_profiles['Load'] = aggregate_profiles['Load'] + (load_shapes[profile_name] * kw)[0]
    del load_shapes
    if pv_systems:
        aggregate_profiles['PV to Load Ratio'] = aggregate_profiles['PV'] / aggregate_profiles['Load']
        aggregate_profiles['PV minus Load'] = aggregate_profiles['PV'] - aggregate_profiles['Load']

    timepoints = pd.DataFrame(columns=['Timepoints'])
    timepoints.loc['Max Load'] = aggregate_profiles['Load'].idxmax()
    if pv_systems:
        timepoints.loc['Max PV to Load Ratio'] = aggregate_profiles.between_time(pv_generation_hours['start_time'],
                                                                                 pv_generation_hours['end_time'])['PV to Load Ratio'].idxmax()
        timepoints.loc['Max PV minus Load'] = aggregate_profiles.between_time(pv_generation_hours['start_time'],
                                                                              pv_generation_hours['end_time'])['PV minus Load'].idxmax()
        timepoints.loc['Max PV'] = aggregate_profiles.between_time(pv_generation_hours['start_time'],
                                                                   pv_generation_hours['end_time'])['PV'].idxmax()
    timepoints.loc['Min Load'] = aggregate_profiles['Load'].idxmin()
    timepoints.loc['Min Daytime Load'] = aggregate_profiles.between_time(pv_generation_hours['start_time'],
                                                                         pv_generation_hours['end_time'])['Load'].idxmin()
    logger.info("Time points: %s", {k: str(v) for k, v in timepoints.to_records()})
    dump_data(timepoints.astype(str).to_dict(orient='index'), output_filename, indent=2)
    return timepoints.loc[column][0].to_pydatetime()



if __name__ == '__main__':
    input_dss_filename = "Master.dss"
    output_filename = "snapshot_time_points.json"

    INPUT_SETTINGS = {"loadshape_start_time": 123, "loadshape_end_time": 123, "loadshape_step_time": 123, "simulation_duration_mins": 123}

    end_time = INPUT_SETTINGS["loadshape_start_time"] + timedelta(minutes=INPUT_SETTINGS.simulation_duration_mins)


    get_snapshot_timepoint(SnapshotTimePointSelectionMode.MAX_PV_LOAD_RATIO, output_filename)
    
    
    