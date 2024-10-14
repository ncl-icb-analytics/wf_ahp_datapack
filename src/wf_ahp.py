'''
Script to execute the pipelines involved in the AHP Workforce Report generation. 
'''
from utils.nhs_wf_stats import *

# Load runtime settings

# NHS Workforce Statistics Pipeline
if True:
    nhs_wf_stats()
