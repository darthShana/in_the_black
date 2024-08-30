import json
import logging
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing import Annotated, Literal

from langgraph.constants import END
from langgraph.graph import StateGraph
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver

from my_agent.tools.ask_human import AskHuman
from my_agent.tools.document_classifier import document_classifier_tool
from my_agent.tools.generate_end_of_year_reports import generate_end_of_year_reports_tool
from my_agent.tools.process_bank_export import classify_transactions_tool, save_classified_transactions_tool, load_transactions_tool, load_transactions_tool_name, \
    classify_transactions_tool_name
from my_agent.utils.nodes import create_tool_node_with_fallback
log = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    transactions: dict[str, list[dict]]
    statement_filter: dict


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


class GraphConfig(TypedDict):
    access_token: str


llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful book keeper for Residential Rental Property company "
            "Use the provided tools to process various financial documents given into transactions"
            "All transactions need to be classified into a transaction type before they can be saved"
            "Use the ask_human tool when a tool requires input or confirmation from the user do NOT guess"
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())


def update_transactions(state: State):
    if messages := state.get("messages", []):
        ai_message = messages[-1]
        if isinstance(ai_message, ToolMessage):
            log.info("node update_transactions")
            return {'transactions': json.loads(ai_message.content)}


# We define a fake node to ask the human
def ask_human(state: State):
    pass


def route_tool_results(state: State) -> Literal["assistant", "update_transactions"]:
    if messages := state.get("messages", []):
        ai_message = messages[-1]
        if isinstance(ai_message, ToolMessage) and (
                ai_message.name == load_transactions_tool_name or
                ai_message.name == classify_transactions_tool_name
        ):
            return "update_transactions"

    return "assistant"


tools = [
    load_transactions_tool,
    document_classifier_tool,
    classify_transactions_tool,
    save_classified_transactions_tool,
    generate_end_of_year_reports_tool
]


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # If tool call is asking Human, we return that node
    # You could also add logic here to let some system know that there's something that requires Human input
    # For example, send a slack message, etc
    elif last_message.tool_calls[0]["name"] == "AskHuman":
        return "ask_human"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define a new graph
workflow = StateGraph(State, config_schema=GraphConfig)
assistant_runnable = assistant_prompt | llm.bind_tools(tools + [AskHuman])

workflow.set_entry_point("assistant")
workflow.add_node("assistant", Assistant(assistant_runnable))
workflow.add_node("tools", create_tool_node_with_fallback(tools))
workflow.add_node("ask_human", ask_human)
workflow.add_node("update_transactions", update_transactions)

workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "assistant",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "tools",
        # We may ask the human
        "ask_human": "ask_human",
        # Otherwise we finish.
        "end": END,
    },
)
workflow.add_conditional_edges(
    "tools",
    route_tool_results,
    {
        "assistant": "assistant",
        "update_transactions": "update_transactions"
    }
)
workflow.add_edge("ask_human", "assistant")
workflow.add_edge("update_transactions", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory, interrupt_before=["ask_human"],)
