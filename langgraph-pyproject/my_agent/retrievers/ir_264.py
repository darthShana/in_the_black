import logging
import os
from decimal import Decimal

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_pinecone import PineconeVectorStore
from langchain_voyageai import VoyageAIEmbeddings
from langchain_anthropic import ChatAnthropic
from pinecone import Pinecone
from pydantic import BaseModel, Field

from my_agent.model.user import Asset

log = logging.getLogger(__name__)
pinecone = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
embeddings = VoyageAIEmbeddings(voyage_api_key=os.environ["VOYAGE_API_KEY"], model="voyage-large-2")
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
db = PineconeVectorStore.from_existing_index(
    index_name='ir264-2024', embedding=embeddings
)


class DepreciationResult(BaseModel):
    """Results from a depreciation calculation"""
    final_answer: Decimal = Field(description="the final answer")
    reasoning: str = Field(description="a description on how the final answer was calculated")


def calculate_depreciation(asset: Asset, year: int) -> dict:
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    retriever = db.as_retriever()

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    results = rag_chain.invoke({"input": f"""
        how i can calculate the depreciation on a particular year after installation for a heat pump purchases on {asset.installation_date.strftime("%B %Y")}, 
        using the diminishing value method. 
        Specify the Estimated useful life, Which is the number of years the item can be depreciated.
        Specify how to handle partial years of use, Assuming the tax year 1 April to 31 March
        Provide an Example if possible
        """}
    )

    print(results['answer'])

    prompt_template = PromptTemplate.from_template("""
    Given the following Rules:
    {rules}
    
    Answer the query:
    calculate the depreciation on a {asset_type} which occurred in the specific tax year ending March {year_to_calculate}? (Not cumulative)
    It was installed in {installation_date}, at the time of installation it was valued at ${installation_value}, round to 2 decimal places at each step
    
    Extract the result in json format marking the json as ```json with: 
    depreciation in a field 'depreciation', 
    the opening residual value of the asset in a filed 'opening_value',
    the rate used for depreciation in a field 'rate'
    any explanation in the field 'reasoning'. 
    :
    """)
    chain = prompt_template | llm
    result = chain.invoke({
        "rules": results['answer'],
        "asset_type": asset.asset_type,
        "year_to_calculate": year,
        "installation_date": asset.installation_date.strftime("%B %Y"),
        "installation_value": asset.installation_value,
    })
    log.info(result)
    return parse_json_markdown(result.content)

