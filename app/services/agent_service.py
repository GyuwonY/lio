from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain_community.vectorstores.weaviate import Weaviate
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
import asyncio

from app.db.session import weaviate_client
from app.services.rag_service import WEAVIATE_CLASS_NAME as PORTFOLIO_CLASS
QNA_CLASS = "ConfirmedQnA" 

# --- 1. Tools (Retriever는 비동기 메서드를 지원) ---
portfolio_vectorstore = Weaviate(client=weaviate_client, index_name=PORTFOLIO_CLASS, text_key="text")
qna_vectorstore = Weaviate(client=weaviate_client, index_name=QNA_CLASS, text_key="text")

portfolio_retriever = portfolio_vectorstore.as_retriever()
qna_retriever = qna_vectorstore.as_retriever()

# Retriever Tool 생성
portfolio_tool = create_retriever_tool(
    portfolio_retriever, "portfolio_search", "Search for information in the user's portfolio."
)
qna_tool = create_retriever_tool(
    qna_retriever, "qna_search", "Search for answers in the user's confirmed QnA list."
)
tools = [portfolio_tool, qna_tool]

# --- 2. Agent State ---
class AgentState(TypedDict):
    question: str
    generation: str
    context: Annotated[List[str], operator.add]
    tone_examples: List[str]

# --- 3. Nodes ---
async def retrieve_context(state):
    """RAG를 통해 컨텍스트를 비동기적으로 검색하는 노드"""
    question = state["question"]
    # 두 retriever를 비동기적으로 동시에 실행
    portfolio_docs, qna_docs = await asyncio.gather(
        portfolio_retriever.ainvoke(question),
        qna_retriever.ainvoke(question)
    )
    context = [doc.page_content for doc in portfolio_docs + qna_docs]
    return {"context": context}

async def generate_answer(state):
    """검색된 컨텍스트와 어조를 바탕으로 답변을 비동기적으로 생성하는 노드"""
    question = state["question"]
    context = state["context"]
    tone_examples = "\n".join(f"- {ex}" for ex in state["tone_examples"])

    prompt = ChatPromptTemplate.from_template(
        """당신은 'lio'라는 이름의 챗봇입니다. 사용자를 대신하여 방문자의 질문에 답변해야 합니다.
        주어진 컨텍스트와 아래 어조 예시를 참고하여 질문에 대해 친절하고 명확하게 답변해주세요.
        모르는 내용에 대해서는 솔직하게 모른다고 답변하세요.

        어조 예시:
        {tone_examples}

        컨텍스트:
        {context}

        질문: {question}

        답변:"""
    )
    llm = ChatOpenAI(model="gpt-4o")
    
    chain = prompt | llm | StrOutputParser()
    generation = await chain.ainvoke({
        "context": context, 
        "question": question, 
        "tone_examples": tone_examples
    })
    return {"generation": generation}

# --- 4. Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_context)
workflow.add_node("generate", generate_answer)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

agent_executor = workflow.compile()
