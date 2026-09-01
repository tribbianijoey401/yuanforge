# Refactor fixture: parser boundaries

This directory is the initial Repository for `../../tasks/refactor.md`. Copy it for every arm and run:

```powershell
python -m unittest discover -s tests -v
```

The fixture starts green; evaluation judges whether any extraction preserves the public API while improving a real boundary, rather than merely changing file shape.
