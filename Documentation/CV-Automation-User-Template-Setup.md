# Set up the included CV template

[Home](../README.md) · [Choose a document approach](Documents.md)

This walkthrough preserves the supplied layout while filling your permanent
details. For a different layout or an existing CV, start with the documents guide.

## What you are creating

Before using the CV automation, create a personal LibreOffice Writer document containing the information and formatting that normally stay the same between applications.

Start from `CV Template.ott` and save your personal copy as an OpenDocument Text document such as:

```text
JobSearch/Templates/personal-master.odt
```

The `.ott` file is the reusable blank template supplied with the tool. Your `.odt` file is your private working template. It will contain your photograph, contact information, LinkedIn link, education, languages, and interests. The automation will copy this document for each application and populate only the sections that need tailoring.

Do not edit or overwrite the original `.ott` file.

## 1. Open the template and save your personal copy

1. Open `CV/Templates/CV Template.ott` in LibreOffice Writer.
2. Writer should create a new untitled document from the template rather than opening the template for editing.
3. Choose **File > Save As**.
4. Save it inside `JobSearch/Templates/` as `personal-master.odt`. Do not save
   personal details into the public `CV/Templates/` directory.
5. Select **ODF Text Document (.odt)** as the file type.
6. If LibreOffice asks whether to use the ODF format, choose **Use ODF Format**.

From this point onward, edit the `.odt` document. Keep the blank `.ott` available in case you need to start again.

If you produce CVs in more than one language, create a separate personal template for each language, for example:

```text
CV template EN.odt
CV template DE.odt
```

This is preferable to translating the permanent sections on every application. Education descriptions, language proficiency terms, nationality wording, and hobbies can then be written and formatted appropriately for each output language.

## 2. Add your photograph

The upper-left area on page 1 contains the photograph frame.

1. Select the blank photograph or placeholder image.
2. Right-click and choose **Replace > Image**, or use the equivalent Replace Image command in your version of LibreOffice.
3. Select a professional portrait from your computer.
4. Use Writer's crop controls if necessary so your face is centred and the image fills the existing frame.

Do not delete the frame and insert an unrelated floating image. Replacing the existing image preserves the intended size, position, wrapping, and alignment.

Use a reasonably high-resolution photograph, but avoid an unnecessarily large source file. Check that the image remains sharp when the document is exported to PDF.

## 3. Enter your name

Replace:

```text
{{FULL_NAME}}
```

with your full name.

Keep the name on one line. Do not change its font, size, weight, colour, or alignment. If a long name does not fit, first try a normal professional form of the name rather than reducing the font size.

Leave `{{TAGLINES}}` unchanged. The tagline is tailored to the position and will be supplied by the automation for each application.

## 4. Add your LinkedIn profile hyperlink

The LinkedIn logo at the upper right is an image containing a hyperlink. The URL is not displayed as text.

1. Select the LinkedIn logo carefully.
2. Open the hyperlink editor using **Insert > Hyperlink** or the hyperlink command in the right-click menu.
3. Replace the existing example target with the full HTTPS URL of your LinkedIn profile, for example:

   ```text
   https://www.linkedin.com/in/your-profile/
   ```

4. Apply the change without replacing or moving the logo.
5. Test it with Writer's follow-link action, normally Ctrl-click on Windows and Linux or Command-click on macOS.

The logo should remain in its existing position and should open the correct public profile. Do not paste the LinkedIn URL visibly into the document.

## 5. Complete the contact row

The row beneath the header contains four fields. Replace only the placeholder text and preserve the icons, table cells, spacing, and alignment.

### Email

Replace:

```text
{{EMAIL}}
```

with the email address you want employers to use.

Use one address only. A reasonably short professional address fits the layout best.

### Telephone

Replace:

```text
{{PHONE}}
```

with your telephone number. Use an international format if you are applying across countries.

### Location

Replace:

```text
{{LOCATION}}
```

with the location you want to disclose, normally a town or city and country. A complete postal address is neither required nor recommended for this layout.

### Nationalities

Replace:

```text
{{NATIONALITIES}}
```

with the nationality or nationalities you want shown. If there is more than one, separate them with a vertical bar or another short form that fits the existing cell.

Do not press Enter inside any of these four cells. Each value should remain on one line. If something does not fit, shorten the wording rather than changing table widths, icon sizes, or font sizes.

## 6. Leave the tailored sections unchanged

The following placeholders belong to the automation and must remain in the document:

```text
{{TAGLINES}}
{{PROFILE_PARAGRAPHS}}
{{EXPERTISE_1_TITLE}}
{{EXPERTISE_1_BULLET}}
{{EXPERTISE_2_TITLE}}
{{EXPERTISE_2_BULLET}}
{{ROLE_FIRST_COMPANY}}
{{ROLE_FIRST_TITLE}}
{{ROLE_FIRST_DATES}}
{{ROLE_FIRST_LOCATION}}
{{ROLE_FIRST_BULLET}}
{{ROLE_REPEAT_COMPANY}}
{{ROLE_REPEAT_TITLE}}
{{ROLE_REPEAT_DATES}}
{{ROLE_REPEAT_LOCATION}}
{{ROLE_REPEAT_BULLET}}
```

These tokens provide the positions and formatting prototypes used to create the job-specific content. Do not reword them, add spaces inside them, delete their paragraphs, or replace them with example CV text.

In particular:

- Profile is generated for each application.
- The two Expertise and Achievements groups can have different titles and bullets for different roles.
- Work Experience is selected and rewritten from the user's experience database for each application.
- The first-role and repeat-role blocks carry different layout details and must both remain available as prototypes.

The merge behaviour, ownership split and validation rules are defined in
`CV/Templates/CV-Template-Population-Agent-Instructions.md`.

Everything else in the document is yours and stays as you formatted it. The
automation copies your personalised template for every application, so your
name, contacts, LinkedIn link, photograph, education, languages and hobbies are
already present in each generated CV. It will never fill or change those fields.

The template may look sparse before automation. That is expected; the generated
content will fill the reserved areas.

## 7. Complete Education

On the final page, replace:

```text
{{EDUCATION_ENTRIES}}
```

with your permanent education information.

You may format this in the way that represents your background most clearly. For example, one line can contain the institution and country, qualification, classification, and subject. If you have more than one relevant qualification, use one compact paragraph per entry.

Keep this section concise. It must share page 3 with any remaining work experience, Languages, and Sports and Hobbies. Preserve the Education heading, icon, blue rule, margins, and general type style.

## 8. Complete Languages

Replace:

```text
{{LANGUAGES}}
```

with your language skills.

A compact single-line format works well, for example:

```text
English (native) | German (business fluent) | French (conversational)
```

You may bold the language names if desired. Use accurate, conventional proficiency descriptions and keep the section on one or two lines.

## 9. Complete Sports and Hobbies

Replace:

```text
{{SPORTS_AND_HOBBIES}}
```

with a short description of your interests.

Use whichever form feels appropriate: a short natural sentence or a compact comma-separated list. One paragraph is normally sufficient. Avoid a long explanation because this section must remain on page 3.

## 10. Preserve the document structure

Do not change the following unless you deliberately redesign the template and retest the automation:

- fixed section headings;
- blue rules and section icons;
- page size or margins;
- paragraph and character styles;
- the contact table;
- page breaks;
- placeholder spelling;
- first-role and repeat-role prototype blocks;
- hidden bookmarks used by the merge process.

When replacing permanent placeholder text, select the placeholder text itself rather than deleting the entire paragraph, table cell, image frame, or section.

Do not paste formatted content directly from a website or another CV. Use **Paste Special > Unformatted Text** when necessary, then apply the formatting already present in the template. This avoids importing unrelated fonts, spacing, colours, hyperlinks, and paragraph styles.

## 11. Check the personal template

Before using the document with the automation, verify all of the following:

- The file is an `.odt`, not an `.ott`.
- Your full name is correct and remains on one line.
- Your photograph is clear, centred, and contained within the original frame.
- The LinkedIn logo opens your profile.
- Email, telephone, location, and nationalities each fit on one line.
- Education, Languages, and Sports and Hobbies contain no placeholder tokens.
- All job-specific placeholders listed in section 6 are still present and spelled exactly as shown.
- No identity placeholder tokens (`{{FULL_NAME}}`, `{{EMAIL}}`, `{{PHONE}}`, `{{LOCATION}}`, `{{NATIONALITIES}}`) remain anywhere in the document.
- No icons, rules, headings, or table cells have moved.
- The document still contains three pages.
- Education, Languages, and Sports and Hobbies remain on page 3.
- The file opens normally after being closed and reopened in LibreOffice Writer.

It is useful to export one test PDF and inspect every page before running the first real application.

## 12. Store the personal template privately

Your `.odt` contains your photograph and personal contact details. Keep it under `JobSearch/Templates/`, inside the independent private repository.

The public repository should contain only the blank `.ott` distribution template. Add personal `.odt` files and generated CV documents to `.gitignore` so they cannot be committed accidentally.

The automation should copy your personal `.odt` for each application. It should never modify the personal master directly. If an automated run fails or produces poor pagination, you can then regenerate the application from the unchanged master.
