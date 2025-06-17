import os
import threading

from dotenv import load_dotenv

from models.conversation import Conversation

# Import configured LLM clients from centralized config
from utils.llm.clients import llm_mini, embeddings

load_dotenv('../../.env')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../' + os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

from database._client import get_users_uid
import database.conversations as conversations_db
from utils.conversations.process_conversation import save_structured_vector
from database.redis_db import has_migrated_retrieval_conversation_id, save_migrated_retrieval_conversation_id

if __name__ == '__main__':
    def single(uid, memory, update):
        save_structured_vector(uid, memory, update)
        save_migrated_retrieval_conversation_id(memory.id)


    uids = get_users_uid()
    for uid in uids:
        memories = conversations_db.get_conversations(uid, limit=2000)
        threads = []
        for memory in memories:
            if has_migrated_retrieval_conversation_id(memory['id']):
                print('Skipping', memory['id'])
                continue

            threads.append(threading.Thread(target=single, args=(uid, Conversation(**memory), True)))
            if len(threads) == 20:
                [t.start() for t in threads]
                [t.join() for t in threads]
                threads = []

        [t.start() for t in threads]
        [t.join() for t in threads]
