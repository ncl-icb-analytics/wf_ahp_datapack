# Workforce AHP Datapack

<!-- About the project -->
## About the project

This git repository is used to generate visuals used in a quarterly AHP Workforce report using data from NHSD.
Currently the code is only capable of creating the visuals to use in the slide pack but further development is planned to have the code generate the .pptx file as well.

## First Time Installation

Follow the NCL scripting onboarding document for guidance on installing python, and setting up a virtual environment.
The onboarding document can be found [here]([https://nhs-my.sharepoint.com/:w:/r/personal/emily_baldwin20_nhs_net/Documents/Documents/Infrastructure/Skills%20Development/Onboarding%20resources/Scripting_Onboarding.docx?d=w7ff7aa3bbbea4dab90a85f1dd5e468ee&csf=1&web=1&e=BPdIKw]).

Copy the .env into the WF_AHP_DATAPACK folder. The .env file can be found at N:\Performance&Transformation\Performance\NELCSUNCLMTFS\_DATA\UEC and Productivity Team\Ad Hocs\WF_0006 - AHP Data Pack.

## Sourcing the NHSD Data
This repo uses data from NHSD to generate the report. Some visuals only use the most recent data to report on the current workforce but some files require annual files to create a trend. As a default, if the latest data is Jun 24, you should source the data files for Jun 20, Jun 21, Jun 22, Jun 23, Jun 24 before runnign the code.

The data is sourced from the [NHS Workforce Statistics]([https://digital.nhs.uk/data-and-information/publications/statistical/nhs-workforce-statistics]) page on NHS Digital. The relevant data file is found in the "NHS Workforce Statistics, MMM YYYY csv files" zip file with the name "NHS Workforce Statistics, June 2024 staff excluding medical.csv". You need to copy this csv file into the "WF_AHP_DATAPACK/data/nhs workforce statistics/" directory.

Using Jun 2024 being the latest data as an example, your data/nhs workforce statistics folder should contain the following files:

* NHS Workforce Statistics, June 2020 staff excluding medical.csv
* NHS Workforce Statistics, June 2021 staff excluding medical.csv
* NHS Workforce Statistics, June 2022 staff excluding medical.csv
* NHS Workforce Statistics, June 2023 staff excluding medical.csv
* NHS Workforce Statistics, June 2024 staff excluding medical.csv

NOTE: The code in it's current state will process all files in the data/nhs workforce statistics folder. This means if you include non-June data (following the example before) in the folder, that non-June data will appear in the generated output.

## Usage
Provided the data is prepared as outlined in the previous section:

* Enable the virtual environment, this can be done using the following commands in your terminal (Ctrl + Shift + '):
    * Set-ExecutionPolicy Unrestricted -Scope Process
    * venv/Scripts/activate
    * pip install -r requirements.txt
* Execute the main script file (src/wf_ahp.py).
* The terminal will announce the status of the current execution.
* After execution, the generated output can be found in the output folder.

## Licence
This repository is dual licensed under the [Open Government v3]([https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) & MIT. All code can outputs are subject to Crown Copyright.

## Contact
Jake Kealey - jake.kealey@nhs.net

Project Link: https://github.com/ncl-icb-analytics/wf_ahp_datapack