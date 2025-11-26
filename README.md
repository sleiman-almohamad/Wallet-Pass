# Google Wallet Class Verifier

A simple Desktop GUI application to verify Google Wallet Classes by Pass ID (Object ID).

## Prerequisites

- **Python 3.12+**
- **uv** package manager
- **flet** library
- **Google Cloud Service Account Key**: The file `**********.json` must be present in the project root.

## Setup

1.  **Install Dependencies**:
    The project uses `uv` for dependency management.
    ```bash
    uv sync
    ```

2.  **Credentials**:
    Ensure your service account key file (`**********.json`) is in the project directory.

## Usage

1.  **Run the Application**:
    ```bash
    uv run main.py
    ```

2.  **Verify a Pass**:
    - Enter the **Pass ID** (Object ID) in the input field.
    - Click **Verify**.
    - The application will fetch and display the details of the Wallet Object and its associated Class.

