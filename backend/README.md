# Omi Backend Setup

This README provides a quick setup guide for the Omi backend. For a comprehensive step-by-step guide with detailed explanations, please refer to the [Backend Setup Documentation](https://docs.omi.me/docs/developer/backend/Backend_Setup).

## Quick Setup Steps

1. Install the google-cloud-sdk
   - Mac: `brew install google-cloud-sdk`
   - Windows: `choco install gcloudsdk`
   - Nix envdir: It should be pre-installed

2. You will need to have your own Google Cloud Project with Firebase enabled. If you've already set up Firebase for the Omi app, you're good to go. If not, please refer to the [Firebase Setup Guide](https://firebase.google.com/docs/projects/learn-more).
   - **IMPORTANT:** Make sure you have the [`Cloud Resource Manager API`](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com), [`Firebase Management API`](https://console.cloud.google.com/apis/library/firebase.googleapis.com), and [`Cloud Firestore API`](https://console.developers.google.com/apis/api/firestore.googleapis.com/overview) enabled in the [Google Cloud API Console](https://console.cloud.google.com/apis/dashboard) **before proceeding to the next steps**. Failure to enable these APIs will result in authentication errors.

### 2a. Choose Your Database

This backend can run on either Google Firestore (default) or a self-hosted PostgreSQL database.

-   **For Firestore**: No extra steps are needed. Continue with the setup.
-   **For PostgreSQL**:
    1.  Make sure you have Docker installed.
    2.  Run a local PostgreSQL instance using Docker:
        ```bash
        docker run --name omi-postgres -e POSTGRES_USER=omi_user -e POSTGRES_PASSWORD=omi_password -e POSTGRES_DB=omi_db -p 5432:5432 -d postgres
        ```
    3.  In your `.env` file (created in a later step), you will set `DATABASE_CHOICE=postgres`.

3. Run the following commands one by one to authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project <project-id>
   gcloud auth application-default login --project <project-id>
   ```
   Replace `<project-id>` with your Google Cloud Project ID.
   This should generate the `application_default_credentials.json` file in the `~/.config/gcloud` directory. This file is read automatically by gcloud in Python.

4. Install Python
   - Mac: `brew install python`
   - Windows: `choco install python`
   - Nix envdir: It should be pre-installed

5. Install `pip` if it doesn't exist (follow instructions on [pip installation page](https://pip.pypa.io/en/stable/installation/))

6. Install `git` and `ffmpeg`
   - Mac: `brew install git ffmpeg`
   - Windows: `choco install git.install ffmpeg`
   - Nix envdir: These should be pre-installed

7. Install `opus` (required for audio processing)
   - Mac: `brew install opus`
   - Windows: You should already have it if you're on Windows 10 version 1903 and above

8. Move to the backend directory: `cd backend`

9. Create your environment file: `cp .env.template .env`.
   - **IMPORTANT**: If you are using PostgreSQL, open the `.env` file and set `DATABASE_CHOICE=postgres`. Ensure the `POSTGRES_URL` matches your setup.

10. Set up Redis
    - [Upstash](https://console.upstash.com/) is recommended - sign up and create a free instance

11. Add the necessary API keys in the `.env` file:
    - [OpenRouter API Key](https://openrouter.ai/keys) for LLM calls. Set this as `OPENROUTER_API_KEY`.
    - **Embedding Provider**: Choose one of the following options by setting `EMBEDDING_PROVIDER`:
      - **`openai`** (default): [OpenAI API Key](https://platform.openai.com/api-keys) - Set as `OPENAI_API_KEY`
      - **`sentence-transformer`**: Local embeddings (no API key needed) - Configure `SENTENCE_TRANSFORMER_MODEL`
    - [Deepgram API Key](https://console.deepgram.com/api-keys)
    - Redis credentials from your [Upstash Console](https://console.upstash.com/)
    - Set `ADMIN_KEY` to a temporary value (e.g., `123`) for local development
    - **Note on Vector Database**: This setup now uses **ChromaDB**, which runs locally and stores its data in the `backend/_chroma_db/` directory. No API keys or cloud setup are required for the vector database.

12. Install Python dependencies (choose one of the following approaches):

    **Option A: Using a virtual environment (recommended)**
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate the virtual environment
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate

    # Install dependencies within the virtual environment
    pip install -r requirements.txt
    ```
    You should see `(venv)` at the beginning of your command prompt when the virtual environment is active.

    **Option B: Direct installation**
    ```bash
    # Install dependencies globally
    pip install -r requirements.txt
    ```

13. Sign up on [ngrok](https://ngrok.com/) and follow the steps to configure it
    - During onboarding, get your authentication token and run `ngrok config add-authtoken <your-token>`

14. During the onboarding flow, under the `Static Domain` section, Ngrok should provide you with a static domain and a command to point your localhost to that static domain. Replace the port from 80 to 8000 in that command and run it in your terminal:
    ```bash
    ngrok http --domain=example.ngrok-free.app 8000
    ```

15. Start the backend server:
    ```bash
    uvicorn main:app --reload --env-file .env
    ```

16. Troubleshooting: If you get any error mentioning "no internet connection" while downloading models, add the following lines in the `utils/stt/vad.py` file after the import statements:
    ```python
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    ```

17. Now try running the server again: `uvicorn main:app --reload --env-file .env`

18. In your Omi app's environment, set `API_BASE_URL` to the URL provided by ngrok (e.g., `https://example.ngrok-free.app`)

19. Your app should now be using your local backend

20. If you used a virtual environment, when you're done, deactivate it by running:
    ```bash
    deactivate
    ```

## Additional Resources

- [Full Backend Setup Documentation](https://docs.omi.me/developer/backend/Backend_Setup)
- [Omi Documentation](https://docs.omi.me/)
- [Community Support](https://discord.gg/omi)
