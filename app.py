from flask import Flask, request, jsonify, render_template
import os
import streamlit as st
from langchain.chains import create_sql_query_chain
from langchain_google_genai import GoogleGenerativeAI
from sqlalchemy.exc import ProgrammingError
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain import hub
from langgraph.prebuilt import create_react_agent


# Database connection parameters
db_user = "root"
db_password = "365536"
db_host = "localhost:3306"
db_name = "test"

# Create SQLAlchemy engine
# db_uri = "mysql+mysqlconnector://root:365536@localhost:3306/genainosql"
db_uri = "mysql+mysqlconnector://sql12787708:KCcxsNAL1D@sql12.freesqldatabase.com:3306/sql12787708"

# Initialize SQLDatabase
db = SQLDatabase.from_uri(db_uri)

os.environ["GOOGLE_API_KEY"] = "AIzaSyCqSJfni-2eEiFbDl8CpQrXd8Pb_VnrjPc"

# Initialize LLM
#llm = GoogleGenerativeAI(model="gemini-1.5-flash-002",google_api_key="AIzaSyCqSJfni-2eEiFbDl8CpQrXd8Pb_VnrjPc")
llm = init_chat_model('gemini-2.5-flash',model_provider='google_genai')

toolkit = SQLDatabaseToolkit(db=db,llm=llm)
tools = toolkit.get_tools()
#print(tools)

prompt_template = hub.pull('langchain-ai/sql-agent-system-prompt')
prompt_template.messages[0].pretty_print()

system_message = prompt_template.format(dialect='mysql',top_k=5)
sql_agent = create_react_agent(llm,tools,prompt=system_message)
import io
import sys
def get_sql_agent_output(sql_agent_instance, user_query):
    """
    Streams events from a SQL agent, captures the string output of each message's
    .pretty_print() method, and returns these strings as a list.

    Args:
        sql_agent_instance: An initialized SQL agent object (e.g., from LangChain).
        user_query (str): The natural language query to send to the SQL agent.

    Returns:
        list: A list of strings, where each string is the captured output
              of a message's .pretty_print() method.
    """
    print(f"Processing query: '{user_query}'")
    collected_output_strings = [] # Initialize an empty list to store strings

    for event in sql_agent_instance.stream(
        {"messages": ('user', user_query)},
        stream_mode='values'
    ):
        if 'messages' in event and len(event['messages']) > 0:
            if 10 == len(event['messages']) :
                try:
                    print(f"YES")
                    message_object = event['messages'][-1]
                    old_stdout = sys.stdout
                    redirected_output = io.StringIO()
                    sys.stdout = redirected_output

                
                # Call pretty_print() which will now write to our buffer
                    message_object.pretty_print()
                # Get the captured string value
                    captured_string = redirected_output.getvalue()
                    collected_output_strings.append(captured_string)
                finally:
                # Always restore stdout, even if an error occurs
                    sys.stdout = old_stdout
        # You could add an else here if you want to log events that don't contain messages,
        # but it won't be part of the returned list.
            else:     
                print(f"NO")
            # message_object = event['messages'][-1]

            # Create a string buffer to capture output
            

    return collected_output_strings

app = Flask(__name__)

# Route to serve the HTML file
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the data submission from the HTML form
@app.route('/process_data', methods=['POST'])
def process_data():
    if request.is_json:
        data = request.get_json()
        input1 = data.get('input1')
                # --- Your Python Logic Here ---
        # Example: Concatenate the inputs or perform a calculation
        if input1 :
            output_message = get_sql_agent_output(sql_agent,{input1})
        else:
            output_message = "Please provide input text"
        # --- End of Your Python Logic ---
              
        original_message_list = output_message
        # Access the string from the list
        message_string = original_message_list[0]
        import re
        # Use a regular expression to find the part after "Ai Message =" and leading/trailing whitespace
        # match = re.search(r"Ai Message\s*=+[\s\n]*(.*)", message_string, re.DOTALL)
        parts = message_string.split("Ai Message")
        if len(parts) > 1:
            cleaned_message = parts[1].strip("= ") # Remove leading/trailing '=' and spaces
        else:
            cleaned_message = message_string
        
        
        return jsonify(output=cleaned_message)
    else:
        return jsonify(error="Request must be JSON"), 400

if __name__ == '__main__':
    # Ensure the 'templates' folder exists in the same directory as app.py
    # and index.html is inside that 'templates' folder.
    app.run(debug=True) # debug=True allows for automatic reloading on code changes      