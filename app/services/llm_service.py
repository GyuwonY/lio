from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores.weaviate import Weaviate

from app.db.session import weaviate_client
from app.services.rag_service import WEAVIATE_CLASS_NAME

async def generate_qna_from_portfolios(portfolio_ids: list[int], owner_id: int) -> str:
    """
    지정된 포트폴리오 내용을 기반으로 예상 질문과 답변을 비동기적으로 생성합니다.
    """
    vectorstore = Weaviate(client=weaviate_client, index_name=WEAVIATE_CLASS_NAME, text_key="text")
    
    # Retriever의 비동기 검색 메서드 사용
    docs = await vectorstore.asimilarity_search("포트폴리오 요약", k=10)
    context = "\n".join([doc.page_content for doc in docs])

    template = """
    당신은 전문 채용 담당자입니다. 주어진 포트폴리오 내용을 바탕으로, 면접에서 나올 법한 예상 질문과 그에 대한 모범 답변을 3개 생성해주세요.
    각 Q&A는 "Q:"로 시작하고 "A:"로 시작해야 하며, 명확하게 구분되어야 합니다.

    포트폴리오 내용:
    {context}

    예상 질문 및 답변:
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI(model="gpt-3.5-turbo")
    
    chain = (
        {"context": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    # 체인을 비동기적으로 실행
    result = await chain.ainvoke(context)
    return result
