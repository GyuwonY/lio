from typing import TypedDict, Annotated, List
import operator
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import StrOutputParser, Document
from langchain.load.serializable import Serializable
from langgraph.graph import StateGraph, END


class Retriever(Serializable):
    """A placeholder for retriever objects to satisfy typing."""

    class Config:
        arbitrary_types_allowed = True

    async def ainvoke(self, query: str) -> List[Document]:
        raise NotImplementedError


class AgentState(TypedDict):
    """Represents the state of our agent."""

    question: str
    generation: str
    context: Annotated[List[str], operator.add]
    tone_examples: List[str]
    # Retrievers are now part of the state, passed in at invocation time
    portfolio_retriever: Retriever
    qna_retriever: Retriever


async def retrieve_context(state: AgentState):
    """Retrieve context from user-specific retrievers passed in the state."""
    question = state["question"]
    portfolio_retriever = state["portfolio_retriever"]
    qna_retriever = state["qna_retriever"]

    # Invoke the retrievers passed in the state
    portfolio_docs, qna_docs = await asyncio.gather(
        portfolio_retriever.ainvoke(question),
        qna_retriever.ainvoke(question),
    )
    context = [doc.page_content for doc in portfolio_docs + qna_docs]
    # Pass the question along to the next node
    return {"context": context, "question": question}


async def generate_answer(state: AgentState):
    """Generate an answer using the retrieved context and tone examples."""
    question = state["question"]
    context = state["context"]
    tone_examples = "\n".join(f"- {ex}" for ex in state["tone_examples"])

    prompt = ChatPromptTemplate.from_template(
        """You are a chatbot named 'lio'. You must answer the visitor's questions on behalf of the user.
        Please answer the questions kindly and clearly, referring to the given context and the tone examples below.
        If you don't know something, honestly say you don't know.

        Tone Examples:
        {tone_examples}

        Context:
        {context}

        Question: {question}

        Answer:"""
    )
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    chain = prompt | llm | StrOutputParser()
    generation = await chain.ainvoke(
        {"context": context, "question": question, "tone_examples": tone_examples}
    )
    return {"generation": generation}


def create_agent_graph():
    """Create and compile the agent graph. The graph is static and reusable."""
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_answer)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()
