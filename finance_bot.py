# bot_builder.py

import pandas as pd
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA


class PersonalFinanceBot:
    def __init__(self, retriever):
        self.llm = Ollama(model="llama3")
        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=retriever,
            return_source_documents=False
        )

    def ask(self, query: str) -> str:
        return self.qa.run(query)


def build_finance_bot(df: pd.DataFrame) -> PersonalFinanceBot:
    def row_to_text(row) -> str:
        try:
            date_str = pd.to_datetime(row['Date']).strftime('%B %d, %Y')
        except Exception:
            date_str = str(row['Date'])

        return (
            f"On {date_str}, "
            f"{'you received' if str(row['Type']).lower() == 'income' else 'you spent'} ₹{row['Amount']} "
            f"via {row['Method']} for \"{row['Category']}\". "
            f"Remark: {row['Remark']}. This was categorized as {row['Type']}."
        )

    texts = [row_to_text(row) for _, row in df.iterrows()]
    documents = [Document(page_content=text) for text in texts]

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model="llama3")
    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever()

    return PersonalFinanceBot(retriever)
