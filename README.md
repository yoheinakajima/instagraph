# InstaGraph 🌐

Hello there, adventurous coder! Welcome to InstaGraph, your go-to application for converting text or URLs into insightful knowledge graphs. Curious about the relationships between entities in a complex topic? Feed the text to InstaGraph and voila! A beautiful knowledge graph is at your fingertips.

Powered by OpenAI's GPT-3.5, this Flask application turns your text into a vividly colored graph, making it easier to visualize relationships between various entities. Enough talking—let's get started!

## Table of Contents 📚

- [Features](#features-)
- [Installation](#installation-)
- [Usage](#usage-)
- [Contributing](#contributing-)
- [License](#license-)

## Features 🌟

- Dynamic Text to Graph conversion.
- Color-coded graph nodes and edges.
- Responsive design—use it on any device.
- Super-duper user-friendly!

## Installation 🛠️

To get started, you'll need Python and pip installed. Then you can install the required packages with:

```bash
pip install -r requirements.txt
```
#### 1. Clone the repository
```bash
git clone https://github.com/yoheinakajima/instagraph.git
```
#### 2. Navigate to the project directory
```bash
cd instagraph
```
#### 3. Install the required Python packages
```bash
pip install -r requirements.txt
```
#### 4. Set up your OpenAI API Key
Add your OpenAI API key to your environment variables:
```bash
export OPENAI_API_KEY=your-api-key-here
```
#### 5. Run the Flask app
```bash
python main.py
```
   Navigate to `http://localhost:8080` to see your app running.

## Usage 🎉

### Web Interface

- Open your web browser and navigate to `http://localhost:8080`.
- Type your text or paste a URL in the input box.
- Click "Submit" and wait for the magic to happen!

### API Endpoints

1. **GET Response Data**: `/get_response_data`

    - Method: `POST`
    - Data Params: `{"user_input": "Your text here"}`
    - Response: GPT-3.5 processed data

2. **GET Graph Data**: `/get_graph_data`

    - Method: `POST`
    - Response: Graph Data

## Contributing 🤝

Best way to chat with me is on Twitter at [https://twitter.com/yoheinakajima](@yoheinakajima). I usually only code on the weekends or at night, and in pretty small chunks. I have lots ideas on what I want to add here, but obviously this would move faster with everyone. Not sure I can manage Github well given my time constraints, so please reach out if you want to help me run the Github. Now, here are a few ideas on what I think we should add based on comments...
- Store knowlege graph
- Pull knowledge graph from storage
- Show history
- Ability to combine two graphs
- Ability to expand on a graph (either paragraph description of node or new nodes)
- Fuzzy matching of nodes for combining graphs (vector match + LLM confirmation)

There are a lot of "build a chart" tools out there, so instead of doing user account and custom charts, it sounds more fun for me to work on building the largest knowlege graph ever...

## License 📝

MIT License. See [LICENSE.md](LICENSE.md) for more information.

---

Enjoy using InstaGraph! 🎉
