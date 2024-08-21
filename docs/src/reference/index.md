(api)=

# API Reference

This page gives an overview of all public openfactcheck objects, functions and methods. All classes and functions exposed in `openfactcheck.*` namespace are public.

The following subpackages are public.

% TODO: FIX THIS

- `openfactcheck`: Contains the main `OpenFactCheck` class and the main functions to run the fact-checking pipeline.
- `openfactcheck.lib`: Contains the common classes and functions.
- `openfactcheck.utils`: Contains utility functions.
- `openfactcheck.evalator`: Contains the three core modules of the library: `ResponseEvaluator`, `LLMEvaluator` and `CheckerEvaluator`.
- `openfactcheck.solvers`: Contains some default solvers.
- `openfactcheck.data`: Contains the LLM evaluation datasets.
- `openfactcheck.templates`: Contains the default configuration templates and gold datasets.
- `openfactcheck.app` contain the UI streamlit app.

```{warning}
The API is still under heavy development and may change in future versions.
```

```{toctree}
:maxdepth: 2

core
lib
evaluator
solvers
```
