from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores.weaviate import Weaviate
import os
import weaviate

from app.core.config import settings
from app.services.rag_service import WEAVIATE_CLASS_NAME

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY


class LLMService:
    def __init__(self, weaviate_client: weaviate.Client):
        self.weaviate_client = weaviate_client
        self.model = ChatGoogleGenerativeAI(model="gemini-pro")

    async def generate_qna_from_portfolios(
        self, portfolio_ids: list[int], user_id: int
    ) -> str:
        vectorstore = Weaviate(
            client=self.weaviate_client,
            index_name=WEAVIATE_CLASS_NAME,
            text_key="text",
        )

        # This part might need refinement to actually use portfolio_ids and user_id
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

        chain = (
            {"context": RunnablePassthrough()}
            | prompt
            | self.model
            | StrOutputParser()
        )

        result = await chain.ainvoke(context)
        return result
