Contributing Guide
==================

Thank you for your interest in the AIPC Platform Python SDK!

Development Environment Setup
-----------------------------

1. Clone the repository:

.. code-block:: bash

   git clone https://github.com/camthink-ai/ne503-aipc-sdks.git
   cd sdk-python

2. Create a virtual environment:

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate

3. Install development dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

Code Standards
--------------

We use the following tools to ensure code quality:

- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking

Run checks:

.. code-block:: bash

   # Format code
   black hailo_ipc_sdk tests

   # Lint code
   flake8 hailo_ipc_sdk tests

   # Type check
   mypy hailo_ipc_sdk

Testing
-------

Run all tests:

.. code-block:: bash

   pytest tests/

Run specific tests:

.. code-block:: bash

   pytest tests/test_inference.py

Generate coverage report:

.. code-block:: bash

   pytest --cov=hailo_ipc_sdk --cov-report=html tests/

Submitting Code
---------------

1. Create a new branch:

.. code-block:: bash

   git checkout -b feature/my-feature

2. Commit changes:

.. code-block:: bash

   git add .
   git commit -m "feat: add new feature"

3. Push the branch:

.. code-block:: bash

   git push origin feature/my-feature

4. Create a Pull Request

Commit Message Convention
~~~~~~~~~~~~~~~~~~~~~~~~~

Use Conventional Commits format:

- ``feat:``: New feature
- ``fix:``: Bug fix
- ``docs:``: Documentation update
- ``style:``: Code formatting
- ``refactor:``: Code refactoring
- ``test:``: Testing related
- ``chore:``: Build/tooling related

Documentation
-------------

Build documentation:

.. code-block:: bash

   cd docs
   make html

View documentation:

.. code-block:: bash

   open _build/html/index.html

Reporting Issues
----------------

If you find a bug or have a feature suggestion, please create an issue on GitHub:

https://github.com/camthink-ai/ne503-aipc-sdks/issues

License
-------

This project is licensed under the MIT License.
