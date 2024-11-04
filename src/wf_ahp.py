'''
Script to execute the pipelines involved in the AHP Workforce Report generation. 
'''
from utils.runtime_settings import load_runtime_settings

from utils.nhs_wf_stats import *
from utils.pwr_trends import *

# Load runtime settings
settings = load_runtime_settings()

# NHS Workforce Statistics Pipeline
if settings["pipeline_nwfs"]:
    print("\nExecuting NHS Workforce Statistics Pipeline.")
    nhs_wf_stats(settings=settings)

# NHS Workforce Statistics Pipeline
if settings["pipeline_pwr"]:
    print("\nExecuting PWR Pipeline.")
    pwr_trends(settings=settings)

print("\nFinished executing pipelines.\n")

