# Licensing and third-party acknowledgements

JobJimmy's original code, documentation and Markdown templates are licensed under
[MIT](LICENSE). The notice uses the collective name “JobJimmy contributors”.
Third-party software, services and artwork retain their own terms; the project
license does not relicense them or imply their endorsement of JobJimmy.

## Software used with JobJimmy

These tools and packages are installed separately, not vendored in this checkout.
Links below lead to upstream terms; check the license shipped with the version
you install. See [Dependencies](Documentation/Dependencies.md) for required versus
optional components and installation details.

| Software / upstream project | Role | Upstream license or terms |
| --- | --- | --- |
| Python / Python Software Foundation | Script runtime and standard library | [PSF License Version 2 and incorporated-software notices](https://docs.python.org/3/license.html) |
| Git / Git project | Version control | [GNU GPL v2; upstream exceptions and notices apply](https://github.com/git/git/blob/master/COPYING) |
| uv / Astral | Ephemeral Python environments | [MIT or Apache-2.0](https://github.com/astral-sh/uv#license) |
| LibreOffice / The Document Foundation | ODT editing and PDF export | [MPL-2.0; additional component licenses](https://www.libreoffice.org/licenses/) |
| Obsidian | Optional vault interface | [Proprietary license](https://obsidian.md/license); free to use is not open source |
| Dataview / obsidian-dataview project | Obsidian dashboard queries | [MIT](https://github.com/blacksmithgu/obsidian-dataview/blob/master/LICENSE.txt); only plugin configuration and queries are supplied here |
| Kilo Code | Optional AI assistant | [Upstream license](https://github.com/Kilo-Org/kilocode/blob/main/LICENSE); check the specific extension/CLI release used |
| Visual Studio Code / Microsoft | Optional editor | [Microsoft distribution terms](https://code.visualstudio.com/license); the [Code - OSS source](https://github.com/microsoft/vscode/blob/main/LICENSE.txt) is MIT |
| PyMuPDF and MuPDF / Artifex | Optional PDF layout and comparison checks | [GNU AGPL or commercial license](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) |
| certifi / certifi project; Mozilla certificate collection | Optional TLS certificate trust bundle | [MPL-2.0 notice](https://github.com/certifi/python-certifi/blob/master/LICENSE) |
| POSIX shell / chosen shell distributor | Runs `tools/py` | Implementation-specific; for example [GNU Bash is GPL](https://www.gnu.org/software/bash/) |

PyMuPDF's optional status does not waive its license requirements. When using,
combining or redistributing it, comply with the applicable AGPL terms or obtain
a suitable commercial license. JobJimmy's MIT license grants no exception.
If you bundle any dependencies, retain their required copyright/license notices
and satisfy any source-distribution obligations; this table is not a replacement
for the notices in their distributions.

## External services

- **OpenRouter** provides model routing and the optional translation endpoint.
  Use is governed by [OpenRouter's terms](https://openrouter.ai/terms) and any
  applicable downstream model/provider terms.
- **TypeSafe AI** provides the optional Jev evaluation service. It is accessed through
  [OpenRouter’s Jev integration](https://openrouter.ai/docs/guides/community/jev)
  with an OpenRouter key and billing; no separate TypeSafe account is required.
  Applicable provider terms still apply; no model weights are included.
- **GitHub**, or another Git host you choose, provides optional repository hosting
  under that host's own terms. No hosting account is included.

Provider names acknowledge integrations, not sponsorship. Accounts, usage fees
and service terms are separate from this repository's license.

## CV template artwork: provenance review outstanding

`CV/Templates/CV Template.ott` contains eight SVGs, nine PNGs and one JPEG under
`Pictures/`, plus a generated thumbnail. Some SVGs contain
`MsftOfcResponsive_Fill_0066ff` classes and `Icons_` identifiers, suggesting
Microsoft Office stock artwork. This is a provenance clue, not verified
ownership or permission. No accompanying artwork license was found in the
archive. The remaining raster artwork's source is also unverified.

**The embedded artwork and thumbnail are excluded from JobJimmy's MIT grant.**
Do not assume that attribution alone establishes redistribution rights.
[Microsoft's creative-content guidance](https://support.microsoft.com/en-us/office/foundations-experiences/what-am-i-allowed-to-use-premium-creative-content-for)
distinguishes use within Office documents from general reuse. Confirm the actual
sources and applicable permissions, or replace the artwork with original or
appropriately licensed assets, before treating this template as cleared for
open-source redistribution. This review remains on the release checklist.

No font files are bundled in the template archive. Font references do not grant
font licenses; install fonts under their own terms and check embedding rights
when distributing generated documents. Private user-supplied documents, photos,
adverts and templates are not licensed by this project's MIT grant.
