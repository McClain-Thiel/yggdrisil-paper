# /// script
# dependencies = [
#     "marimo",
#     "numpy==2.5.3",
# ]
# requires-python = ">=3.13"
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("# Ready to pair\n\nYour shared Python notebook is running. We can edit cells here together from Codex.")
    return


@app.cell
def _():
    import numpy

    return


@app.cell
def _():
    print("test")
    return


@app.cell
def _():
    print("this a test")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
