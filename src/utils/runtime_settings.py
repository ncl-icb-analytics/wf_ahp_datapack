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
    base_pipeline_nwfs = "nhs_workforce_statistics"

    #Store both the config and env settings in a dict
    settings = {
        "nwfs_path": base_path + config[base_pipeline_nwfs]["rel_path"]
    }

    return settings