# Bug fixture: temporary cleanup

This directory is the initial Repository for `../../tasks/bug.md`. Copy it for every arm and run:

```powershell
python -m unittest discover -s tests -v
```

The baseline exercises only the successful path. The Bug task requires a new regression for the exception path without weakening the existing assertion.
