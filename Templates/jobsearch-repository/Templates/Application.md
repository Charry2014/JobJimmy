---
type: application
company: "[[Companies/company-name]]"
position: Position title
status: researching
priority: medium
fit:
location:
source:
publisher_type: unknown
recruiter:
advert_url:
date_found:
date_applied:
next_action:
next_action_date:
notion_id:
---

## Activity

Create an activity note in this application's `Activities` folder using
[[Templates/Activity|Activity template]], and set its `application` property to a
link to this note.

```dataview
TABLE WITHOUT ID
  date AS Date,
  kind AS Kind,
  file.link AS Activity,
  documents AS Documents
FROM "Applications/{{title}}/Activities"
WHERE type = "activity" AND application = this.file.link
SORT (substring(date,6) + substring(date,3,5) + substring(date,0,2)) DESC, file.name ASC
```

# Position title — Company

## Assessment

## Strengths

-

## Gaps

-

## Application

- CV:
- Cover letter:
- Job advert: [[Applications/{{title}}/Activities/{{title}}-research|Research — original job advert]]

<!-- Create the linked research subpage using Templates/Research. Set its
application property to this note and paste the full original advert there.
If copying this template manually, replace {{title}} with this note's filename.
-->

<!-- Cover-letter Markdown, ODT and PDF belong in this application’s CV/ folder,
using <compact-slug>-cover-letter.md/.odt/.pdf; see CV/README. -->

## Contacts

-

## Notes
