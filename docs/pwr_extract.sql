--Script to load the PWR data for WTE and Vacancy
SELECT
	wte.[fyear] AS [fin_year],
	wte.[month] AS [fin_month],
	--wte.[org_code],
	--wte.[org_name],
	wte.[contract],
	wte.[shorthand],
	wte.[subprofession] AS [staff_role],
    COALESCE(wte.[count], 0) AS [wte],
	kpi.vacancy

FROM [Data_Lab_NCL_Dev].[JakeK].[wf_pwr_wte_vw] wte

LEFT JOIN [Data_Lab_NCL_Dev].[JakeK].[wf_pwr_kpi_vw] kpi
ON kpi.profession = 'Allied Health Professionals'
AND kpi.type = 'Subprofession'
AND wte.subprofession = kpi.subprofession
AND wte.contract = 'Substantive'
AND wte.fyear = kpi.fyear
AND wte.month = kpi.month
AND wte.org_code = kpi.org_code

WHERE wte.[Profession] = 'Allied Health Professionals'
AND wte.type = 'Subprofession'
AND wte.contract IS NOT NULL

ORDER BY wte.fyear, wte.month, shorthand, contract DESC, wte.subprofession