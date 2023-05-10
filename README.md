# Multi-Agent GPT: Collaborative AI Agents
[![GitHub Repo stars](https://img.shields.io/github/stars/101xyz/ai?style=social)](https://github.com/101xyz/ai/stargazers)
[![Twitter Follow](https://img.shields.io/twitter/follow/101dotxyz?style=social)](https://twitter.com/101dotxyz)

Multi-Agent GPT is an innovative project that leverages GPT models to generate dynamic, text-based dialogues between multiple agents as they collaborate to achieve predefined goals. The main objective of this project is to explore the potential of GPT models in enhancing multi-agent productivity and effective communication.

## How it works

Multi-Agent GPT employs separate agents, each equipped with a memory, that interact with one another using communication as a tool. The implementation of agent memory and reflection is inspired by [this research paper](https://arxiv.org/pdf/2304.03442.pdf).

## Getting started

To begin exploring Multi-Agent GPT, follow these steps:

1. Clone the project repository to your local machine
2. Move to the repository: `cd multiagent-gpt`
3. Run `python setup.py` to check your environment setup and configure it as needed
4. Update the environment variables in `.env` with your API Keys. You will need an OpenAI API key, which you can obtain [here](https://platform.openai.com/account/api-keys). Supplying additional API keys will enable the use of other tools
5. Launch the world simulation by running `poetry run world`

Now you can observe the world simulation in action and watch as the agents interact with each other, working together to accomplish their assigned directives.

## Changing the world

To change the world, all you need to do is:

1. Make changes to the `config.json` by updating the available agents or locations
2. Reset your database: `x`
3. Run the world again: `poetry run world`

## Contributing

We enthusiastically welcome contributions to Multi-Agent GPT! To contribute, please follow these steps:

1. Fork the project repository to your own account
2. Create a new branch for your changes
3. Implement your changes to the project code
4. Submit a pull request to the main project repository

We will review your pull request and provide feedback as necessary.

## License

The Multi-Agent GPT project is licensed under the MIT License. For more information, refer to the `LICENSE` file.