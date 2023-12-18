# Setup

- See Makefile for setup and other commands
- Adding another dependency: E.g., adding type type checking for sts like so: `poetry add --group dev boto3-stubs[essential,sagemaker,sagemaker-runtime,sts]`
  - Note that if adding a sub-package, you do still have to include all existing subpackages (comma-separated, without quotes or whitespace). Otherwise, they will be replaced by new sub-package.
