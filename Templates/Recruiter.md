---
type: recruiter
recruitment_company:
recruiter_name:
email:
phone:
linkedin:
website:
last_verified:
---

# Recruitment company — Recruiter name

## Contact details

<!-- Record the person's published business contacts in the properties above.
Keep general agency contact details here, clearly labelled as general. -->

## Applications

```dataview
TABLE WITHOUT ID
  file.link AS Position,
  company AS Employer,
  status AS Status,
  date_applied AS Applied
FROM "Applications"
WHERE type = "application" AND recruiter = this.file.link
SORT (substring(date_found,6) + substring(date_found,3,5) + substring(date_found,0,2)) DESC
```

## Sources

<!-- Link the advert or official profile supporting the identity and contacts. -->

## Notes
