# Recruiter directory

One note per recruitment company and named recruiter, using
[[Templates/Recruiter|Recruiter template]]. If no person is named, use one
agency contact note with recruiter_name left blank until identified. Recruiter
records live inside this vault's `Recruiters/` folder.

```dataview
TABLE WITHOUT ID
  file.link AS Contact,
  recruitment_company AS Agency,
  recruiter_name AS Recruiter,
  email AS Email,
  phone AS Phone,
  linkedin AS LinkedIn,
  website AS Website,
  last_verified AS Verified
FROM "Recruiters"
WHERE type = "recruiter"
SORT recruitment_company ASC, recruiter_name ASC
```
