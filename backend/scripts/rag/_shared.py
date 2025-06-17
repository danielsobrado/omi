import json
import os
from typing import List

import numpy as np
import plotly.graph_objects as go
import umap
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
import chromadb

from models.conversation import Conversation

load_dotenv('../../.env')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '../../' + os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# --- ChromaDB Client Initialization ---
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_chroma_db')
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(
    name=os.getenv("CHROMA_COLLECTION_NAME", "omi_conversations")
)

import database.conversations as conversations_db
import database.memories as facts_d

uid = 'viUv7GtdoHXbK1UBCDlPuTDuPgJ2'

openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

def query_vectors(query: str, uid: str, k: int = 1000) -> List[List]:
    """Queries ChromaDB and returns [id, vector] pairs."""
    xq = openai_embeddings.embed_query(query)
    
    results = collection.query(
        query_embeddings=[xq],
        n_results=k,
        where={'uid': uid},
        include=["metadatas", "embeddings"]
    )
    
    data = []
    if results['ids'][0]:
        for i in range(len(results['ids'][0])):
            memory_id = results['metadatas'][0][i]['memory_id']
            vector = results['embeddings'][0][i]
            data.append([memory_id, vector])
            
    print('Found:', len(data), 'vectors')
    return data


def get_memories(ignore_cached: bool = False):
    if not os.path.exists('memories.json') or ignore_cached:
        memories = conversations_db.get_conversations(uid, limit=1000)
        if ignore_cached:
            return memories

        with open('memories.json', 'w') as f:
            f.write(json.dumps(memories, indent=4, default=str))

    with open('memories.json', 'r') as f:
        return json.loads(f.read())


def get_all_markers(data, data_points, target):
    return go.Scatter(
        x=data_points[target:, 0],
        y=data_points[target:, 1],
        mode='markers',
        marker=dict(size=8, opacity=0.5, color='blue'),
        text=[f"{item[0]}" for item in data[5:]],
        hoverinfo='text',
        name='Other Memories'
    )


def get_top_markers(data, data_points, target):
    return go.Scatter(
        x=data_points[:target, 0],
        y=data_points[:target, 1],
        mode='markers',
        marker=dict(size=10, opacity=0.8, color='green'),
        text=[f"Top {i + 1}: {item[0]}" for i, item in enumerate(data[:5])],
        hoverinfo='text',
        name='Top Matches'
    )


def get_query_marker(query_point, query):
    return go.Scatter(
        x=[query_point[0]],
        y=[query_point[1]],
        mode='markers',
        marker=dict(
            symbol='x',
            size=12,
            color='red',
            line=dict(width=2)
        ),
        text=[query],
        hoverinfo='text',
        name='Query'
    )


def generate_html_visualization(fig, file_name: str = 'embedding_visualization.html'):
    fig.update_layout(
        title=f'Embedding Visualization',
        xaxis_title='UMAP Dimension 1',
        yaxis_title='UMAP Dimension 2',
        width=800,
        height=600,
        showlegend=True
    )

    # Generate HTML
    html_content = f'''
        <html>
            <head>
                <title>Embedding Visualization</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body>
                <div id="plotDiv"></div>
                <script>
                    var plotlyData = {fig.to_json()};
                    Plotly.newPlot('plotDiv', plotlyData.data, plotlyData.layout);
                </script>
            </body>
        </html>
        '''

    with open(file_name, 'w') as f:
        f.write(html_content)

    print(f"HTML file '{file_name}' has been generated.")
