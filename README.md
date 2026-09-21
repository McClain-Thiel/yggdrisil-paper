# yggdrisil-paper

ICLR 2027 paper source. Open `main.tex` to start writing.

```text
main.tex                    Paper entry point and package imports
references.bib              Verified references
iclr2027_conference.sty      Official ICLR 2027 layout
iclr2027_conference.bst      Official ICLR bibliography style
fancyhdr.sty, natbib.sty     Dependencies bundled with the official template
sections/                   Abstract, main sections, statements, and appendix
figures/                    Finished figure assets used by the paper
code/                       All figure, table, and one-off analysis scripts
```

## Writing

Edit the files in `sections/`. The title and section text are explicit draft
placeholders; no research claims or results have been filled in. Keep reusable
LaTeX macros in `main.tex` until there is a reason to split them out.

Add verified references to `references.bib`, cite them with `\citep{key}` or
`\citet{key}`, and uncomment the two bibliography lines in `main.tex` when
adding the first citation. They are initially disabled so an empty bibliography
does not break the starter build. The appendix follows the bibliography.

Put finished figure assets in `figures/` and commit them, including figure PDFs.
Keep all executable utilities in `code/`; see `code/README.md` for conventions.
Tables can live directly in the section that uses them until separate files help.

## Interactive notebook

`notebooks/pair.py` contains the working tutorial, the backpack search example,
and the draft genome-minimization and related-work sections. Its inline
dependencies pin marimo and the tested Yggdrisil commit.

```sh
uv run --no-project --with marimo==0.24.2 marimo edit --sandbox notebooks/pair.py
```

To execute it as a script, use `uv run --script notebooks/pair.py`. Each search
writes a fresh SQLite graph under `notebooks/runs/`, which is ignored by Git.
The illustrative LLM policy is not executed and requires no provider credentials.

## Build locally

Requires a LaTeX distribution with pdfLaTeX and latexmk. Run from the repository root:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The PDF is `build/main.pdf`. Build files are ignored by Git.

## Overleaf

Upload the project source and select `main.tex` as the main document and pdfLaTeX
as the compiler. Include the root style files, `references.bib`, `sections/`, and
`figures/`. The `code/` directory is optional for compilation; committed figure
assets make the paper independent of the local script environment.

## Template source

Downloaded on 2026-09-09 from the [official ICLR 2027 template archive](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip),
linked by the [ICLR author guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines).
The four bundled `.sty`/`.bst` files are copied byte-for-byte from that archive.
The example manuscript, example references, and optional notation collection
are omitted from this writing project.

Archive SHA-256: `0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e`.

The official guidelines checked on 2026-09-09 list:

- Abstract deadline: September 18, 2026, 23:59 Anywhere on Earth.
- Full-paper deadline: September 25, 2026, 23:59 Anywhere on Earth.
- Initial submission: at most nine pages of main text, with references and
  appendices excluded. The limit rises to ten pages for rebuttal/camera-ready.
- Anonymous submission: keep `\iclrfinalcopy` commented out.
- Required AI use statement; recommended ethics and reproducibility statements,
  placed before the references and excluded from the main-text page limit.

Complete the statement placeholders from the actual work before submission.
See the [AI policy for authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)
for the disclosure requirements. Recheck the official guidelines before submitting.
