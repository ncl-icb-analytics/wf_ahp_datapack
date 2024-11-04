import datetime
import json
import toml
from os import getenv
from dotenv import load_dotenv

def load_runtime_settings():

    #Load env settings
    load_dotenv(override=True)

    #Load toml settings from config
    config = toml.load("./config.toml")

    #Base settings
    #These settings should remain unchanged and are combined with toml and env
    #settings to build the settings dict.
    base_path = "data/"
    base_scope = "scope"
    base_pipeline_nwfs = "nhs_workforce_statistics"
    base_pipeline_pwr = "pwr_trends"

    #Store both the config and env settings in a dict
    settings = {
        "pipeline_nwfs": getenv("PIPELINE_NWFS") in ["True", "true", 1],
        "pipeline_pwr": getenv("PIPELINE_PWR") in ["True", "true", 1],

        "org_codes": config[base_scope]["org_codes"],
        "org_shorts": config[base_scope]["org_shorts"],
        "sql_address": getenv("SQL_ADDRESS"),

        "nwfs_path": base_path + config[base_pipeline_nwfs]["rel_path"],
        "nwfs_colahp": config[base_pipeline_nwfs]["colname_ahp"],
        "nwfs_colrole": config[base_pipeline_nwfs]["colname_role"],
        "nwfs_colband": config[base_pipeline_nwfs]["colname_band"],

        "pwr_database": config[base_pipeline_pwr]["database"]
    }

    return settings