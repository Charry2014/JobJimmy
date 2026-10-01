---
include_closed_applications: false
cssclasses: dashboard-table
---

# Job-search dashboard

Obsidian is the authoritative record. The tables below require the Dataview
community plugin.

Set the Dashboard property `include_closed_applications` to `true` in Properties
when you need to include rejected, withdrawn or closed applications in the main
pipeline. It defaults to `false`, so the main table shows active applications only.

## Application pipeline

```dataview
TABLE WITHOUT ID
  file.link AS Position,
  company AS Company,
  date_found AS "Date Added",
  date_applied AS "Applied",
  status AS Status,
  priority AS Priority,
  fit AS Fit,
  next_action AS "Next Action",
  next_action_date AS "Due"
FROM "Applications"
WHERE type = "application" AND (this.include_closed_applications = true OR !contains(list("rejected", "withdrawn", "closed"), status))
SORT (substring(date_found,6) + substring(date_found,3,5) + substring(date_found,0,2)) DESC, (substring(date_applied,6) + substring(date_applied,3,5) + substring(date_applied,0,2)) DESC
```

## Applications by status

```dataview
TABLE WITHOUT ID
  length(rows) AS Count
FROM "Applications"
WHERE type = "application"
GROUP BY status AS Status
SORT Status ASC
```

## Recruiters

[[Recruiters/Directory|Recruiter directory]]

## Starting points

- [[Templates/Application|New application template]]
- [[Templates/Company|New company template]]
- [[Templates/Activity|New activity template]]
- [[Templates/Research|New research template]]

## CV references

- [[CV/README|CV tuning workspace]]
- [[CV/References/README|CV references index]]
- [[Knowledge/Overview|Professional profile and CV knowledge base]]
