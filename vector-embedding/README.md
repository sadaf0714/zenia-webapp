First, ensure Python is installed on your machine (skip this step if it's already installed).

Follow these steps to install and run the project:

1. **Install and Run the Project:**
    - Clone the repository using the following command: `git clone {repository_url}`
    - Navigate to the `src` folder by executing the following command: `cd .\vector-embedding\src\`

2. **(Optional)Sett up Local OpenAI Server:**
    - Follow the instructions [here](https://github.com/keldenl/gpt-llama.cpp) to set up a Local OpenAI server.
    - Update the variables in `constant.py` with your credentials: `GPT_LAMMA_ACCESS_TOKEN=<your_token>`, `GPT_LAMMA_MODEL_NAME=<your_model_name>`

3. **Add API Key:**
    - Create a .env file in the `src` folder.
    - Add your OpenAI API key to this file as follows: `openai.api_key=<your_api_key>`
    - If you do not have an OpenAI key, you can obtain one from the official OpenAI website [here](https://platform.openai.com/account/api-keys)

4. **Install Dependencies:**
    - Install the required packages by running the following command: `pip install -r requirements.txt`.
    - Run the command in order to run the NLP part `python -m spacy download en_core_web_md`.

5. **Run the Project:**
    - Start the project by executing this command: `python main.py`

Once everything is set up, you can access the endpoint by opening your browser and navigating to: `http://127.0.0.1:3001/docs`

Now, you're all set and ready to go! Enjoy using the project!
