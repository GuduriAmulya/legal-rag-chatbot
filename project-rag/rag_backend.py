import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from collections import defaultdict

# Load environment variables
load_dotenv()
GROQ_KEY = os.getenv("GROQ_KEY")

# Load and preprocess PDF
book = PyMuPDFLoader("./sample_data/human_rights3.pdf")
book_pages = book.load()

def is_page_empty(page, min_text_length=0):
    return len(page.page_content.strip()) <= min_text_length

book_pages_filtered = [page for page in book_pages if not is_page_empty(page)]
documents = book_pages_filtered

# Split to chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False,
)
texts = text_splitter.split_documents(documents)

# Embeddings and Vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(texts, embeddings)
db_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Chat Model
chatgroq_model = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=GROQ_KEY
)

def get_msg_content(msg):
    return msg.content

contextualize_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
)

contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_system_prompt),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
])

contextualize_chain = (
    contextualize_prompt
    | chatgroq_model
    | get_msg_content
)

qa_system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context mentioned within delimeter ### to answer "
    "the question. If you don't know the answer, say that you "
    "Sorry, I am don't know."
    "\n\n"
    "###"
    "{context}"
    "###"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ]
)

qa_chain = (
    qa_prompt
    | chatgroq_model
    | get_msg_content
)

@chain
def history_aware_qa(input):
    if input.get('chat_history'):
        question = contextualize_chain.invoke(input)
    else:
        question = input['input']
    context = db_retriever.invoke(question)
    return qa_chain.invoke({
        **input,
        "context": context
    })

# Chat histories per session
session_chat_histories = defaultdict(InMemoryChatMessageHistory)
qa_with_history = RunnableWithMessageHistory(
    history_aware_qa,
    lambda session_id: session_chat_histories[session_id],
    input_messages_key="input",
    history_messages_key="chat_history",
)

def chatbot_response(user_input, session_id="default"):
    result = qa_with_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}},
    )
    return result