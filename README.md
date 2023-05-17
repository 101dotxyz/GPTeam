<p align="center">
  <h1 align="center">GPTeam: Collaborative AI Agents</h1>
  <p align="center">
    <img src="https://img.shields.io/github/stars/101dotxyz/gpteam.svg?style=for-the-badge&">
    <img src="https://img.shields.io/github/license/101dotxyz/gpteam.svg?style=for-the-badge&">
    <br />
  <a href="https://github.com/101dotxyz/gpteam/issues"><b>Report Bug</b></a>
   | 
  <a href="https://www.youtube.com/watch?v=cIxhI1d6NsM"><b>Video Demo</b></a>
  
  </p>
    <div align="center">
    <img src="assets/gpteam.png" alt="GPTeam" width="400" height="267" />
  </div>
</p>

## About GPTeam

GPTeam uses GPT-4 to create multiple agents who collaborate to achieve predefined goals. The main objective of this project is to explore the potential of GPT models in enhancing multi-agent productivity and effective communication.

## Getting started

To begin exploring GPTeam, follow these steps:

1. Clone the project repository to your local machine
2. Move to the repository: `cd gpteam`
3. Run `python setup.py` to check your environment setup and configure it as needed
4. Update the environment variables in `.env` with your API Keys. You will need an OpenAI API key, which you can obtain [here](https://platform.openai.com/account/api-keys). Supplying API keys for optional services will enable the use of other tools.
5. Launch the world by running `poetry run world`

To run the world cheaply, you can use `poetry run world --turbo`. This will use gpt3.5-turbo for all LLM calls which is a lot cheaper, but expect worse results!

Now you can observe the world in action and watch as the agents interact with each other, working together to accomplish their assigned directives.

## How it works

GPTeam employs separate agents, each equipped with a memory, that interact with one another using communication as a tool. The implementation of agent memory and reflection is inspired by [this research paper](https://arxiv.org/pdf/2304.03442.pdf). Agents move around the world and perform tasks in different locations, depending on what they are doing and where other agents are located. They can speak to eachother and collaborate on tasks, working in parallel towards common goals.

## Viewing Agents

The world is a busy place! To get a view of what different agents are doing whilst the world is running, you can visit the `agents/` folder where there is a txt file for each agent containing a summary of their current state.
## Changing the world

To change the world, all you need to do is:

1. Make changes to the `config.json` by updating the available agents or locations
2. Reset your database: `poetry run db-reset`
3. Run the world again: `poetry run world`

## Setting up the Discord Integration
Read through the dedicated [Discord setup docs](DISCORD.md)

## Using with Anthropic Claude
Make sure you have an `ANTHROPIC_API_KEY` in your env, then you can use `poetry run world --claude` which will run the world using `claude-v1` for some calls and `claude-v1-instant` for others.
## Contributing

We enthusiastically welcome contributions to GPTeam! To contribute, please follow these steps:

1. Fork the project repository to your own account
2. Create a new branch for your changes
3. Implement your changes to the project code
4. Submit a pull request to the main project repository

We will review your pull request and provide feedback as necessary.

## License

Licensed under the [MIT license](LICENSE).
