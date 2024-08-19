import logging
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing import Annotated, Literal

from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver

from my_agent.tools.document_classifier import document_classifier_tool
from my_agent.tools.process_bank_export import classify_transactions_tool, save_classified_transactions_tool, load_transactions_tool, load_transactions_tool_name, \
    classify_transactions_tool_name, filter_transactions_tool, filter_transactions_tool_name
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
            "Use the ask_human tool to confirm with the human before saving"
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
            return {'transactions': ai_message.content}


def route_tool_results(state: State) -> Literal["assistant", "update_transactions"]:
    if messages := state.get("messages", []):
        ai_message = messages[-1]
        if isinstance(ai_message, ToolMessage) and (
                ai_message.name == load_transactions_tool_name or
                ai_message.name == filter_transactions_tool_name or
                ai_message.name == classify_transactions_tool_name
        ):
            return "update_transactions"

    return "assistant"


safe_tools = [
    load_transactions_tool,
    document_classifier_tool,
    filter_transactions_tool,
    classify_transactions_tool,
]
sensitive_tools = [
    save_classified_transactions_tool
]
sensitive_tool_names = {t.name for t in sensitive_tools}


def route_tools(state: State) -> Literal["safe_tools", "sensitive_tools", "__end__"]:
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"


# Define a new graph
workflow = StateGraph(State, config_schema=GraphConfig)
assistant_runnable = assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)

workflow.set_entry_point("assistant")
workflow.add_node("assistant", Assistant(assistant_runnable))
workflow.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
workflow.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
workflow.add_node("update_transactions", update_transactions)

# We now add a conditional edge
workflow.add_conditional_edges(
    "assistant",
    route_tools,
)
workflow.add_conditional_edges(
    "safe_tools",
    route_tool_results,
    {
        "assistant": "assistant",
        "update_transactions": "update_transactions"
    }
)
workflow.add_edge("sensitive_tools", "assistant")
workflow.add_edge("update_transactions", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory, interrupt_before=["sensitive_tools"],)
