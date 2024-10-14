'''
Script to execute the pipelines involved in the AHP Workforce Report generation. 
'''
from utils.runtime_settings import load_runtime_settings

from utils.nhs_wf_stats import *

# Load runtime settings
settings = load_runtime_settings()

# NHS Workforce Statistics Pipeline
if True:
    nhs_wf_stats(settings=settings)
