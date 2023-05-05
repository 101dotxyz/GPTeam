# Multi-Agent GPT

Multi-Agent GPT is a collaborative project that uses GPT models to generate text-based dialogues between multiple agents as they work towards predefined goals. The project is aimed at exploring the capabilities of GPT models for multi-agent productivity and communication.

## How it works

---

## Getting started

To get started with Multi-Agent GPT, you can follow these steps:

1. Clone the project repository to your local machine
2. Install the required dependencies by running `pip install -r requirements.txt`
3. Set your OpenAI API key as an environment variable called `OPENAI_API_KEY`
4. Run the project by running `python main.py`

By default, the project will generate a dialogue between two agents, Agent A and Agent B. You can modify the dialogue by changing the prompts that are passed to each agent.

## Contributing

We welcome contributions to the Multi-Agent GPT project! If you would like to contribute, please follow these steps:

1. Fork the project repository to your own account
2. Create a new branch for your changes
3. Make your changes to the project code
4. Write tests for your changes
5. Submit a pull request to the main project repository

We will review your pull request and provide feedback as needed.

## License

The Multi-Agent GPT project is licensed under the MIT License. See the `LICENSE` file for more information.

## Acknowledgements

We would like to thank OpenAI for providing access to the GPT-3 language model and for their support of the project. We would also like to thank the contributors to the project for their hard work and dedication.


### We have the prod db set up now.

If you're using prod make sure to get the url and key,
and populate the .env file with them and also make sure
database/supabase.py is using the prod url and key


### If you want to set up a local supabase instance
`supabase login` 
`supabase init`
`supabase start`

Then replace the SUPABASE_DEV_URL and SUPABASE_DEV_KEY in the .ev file with the values you are given

`supabase db reset`

This will use the migration file in supabase/migrations/initial_schema to set up the tables and columns

### To seed the db
`poetry run db-seed-small` or `poetry run db-seed`

### To run the src/testing.py file:
`poetry run test`


### Next steps
I have implemented a simple planning process
Now the agents need tools. I haven't done that