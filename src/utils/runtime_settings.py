import datetime
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

    #Store both the config and env settings in a dict
    settings = {
        "org_codes": config[base_scope]["org_codes"],
        "org_shorts": config[base_scope]["org_shorts"],

        "nwfs_path": base_path + config[base_pipeline_nwfs]["rel_path"],
        "nwfs_sg2code": config[base_pipeline_nwfs]["sg2_code"],
        "nwfs_colahp": config[base_pipeline_nwfs]["colname_ahp"],
        "nwfs_colrole": config[base_pipeline_nwfs]["colname_role"],
        "nwfs_colband": config[base_pipeline_nwfs]["colname_band"]
    }

    return settings