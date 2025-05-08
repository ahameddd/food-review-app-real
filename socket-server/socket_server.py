import asyncio
import websockets
import json
import random
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK's VADER lexicon if not already downloaded
try:
    nltk.download('vader_lexicon')
    logger.info("NLTK VADER lexicon downloaded successfully")
except Exception as e:
    logger.error(f"Error downloading NLTK lexicon: {e}")

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Store connected clients and their usernames
connected_clients = {}

# Sample reviews with detailed ratings
reviews = [
    {
        "user": "Alice",
        "review": "Great food and amazing ambiance!",
        "ratings": {
            "food": 5,
            "service": 4,
            "ambiance": 5,
            "value": 4
        },
        "timestamp": datetime.now().isoformat()
    },
    {
        "user": "Bob",
        "review": "Decent place, but service was slow.",
        "ratings": {
            "food": 3,
            "service": 2,
            "ambiance": 4,
            "value": 3
        },
        "timestamp": datetime.now().isoformat()
    }   
]

# WebSocket server configuration
HOST = '127.0.0.1'
PORT = 5001

async def broadcast_message(message, exclude=None):
    """Broadcast message to all connected clients except the excluded one"""
    logger.info(f"Broadcasting message to {len(connected_clients)} clients")
    for client in connected_clients:
        if client != exclude:
            try:
                await client.send(json.dumps(message))
                logger.info(f"Message sent to client {connected_clients[client]}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Client {connected_clients[client]} disconnected during broadcast")
                await handle_disconnect(client)

async def handle_disconnect(websocket):
    """Handle client disconnection"""
    if websocket in connected_clients:
        username = connected_clients[websocket]
        del connected_clients[websocket]
        logger.info(f"Client {username} disconnected")
        await broadcast_message({
            "type": "system",
            "message": f"{username} has left the chat",
            "timestamp": datetime.now().isoformat()
        })

async def handle_message(websocket, message):
    """Handle incoming messages"""
    try:
        data = json.loads(message)
        logger.info(f"Received message from {connected_clients[websocket]}: {data}")
        
        if data["type"] == "join":
            username = data["username"]
            connected_clients[websocket] = username
            logger.info(f"New client joined: {username}")
            await broadcast_message({
                "type": "system",
                "message": f"{username} has joined the chat",
                "timestamp": datetime.now().isoformat()
            })
            
        elif data["type"] == "review":
            # Process the review with sentiment analysis
            text = data["review"]
            sentiment_score = sia.polarity_scores(text)
            sentiment = "Positive" if sentiment_score['compound'] > 0 else "Negative" if sentiment_score['compound'] < 0 else "Neutral"
            
            review_data = {
                "type": "review",
                "user": data["username"],
                "restaurant": data["restaurant"],
                "review": text,
                "ratings": data["ratings"],
                "sentiment": sentiment,
                "timestamp": data["timestamp"]
            }
            
            # Add to reviews list
            reviews.append(review_data)
            logger.info(f"New review added from {data['username']}")
            
            # Broadcast to all clients
            await broadcast_message(review_data)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "message": "Invalid JSON format"
        }))
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "message": str(e)
        }))

async def send_reviews(websocket):
    """Handle WebSocket connection"""
    logger.info("New connection established")
    
    try:
        # Send initial reviews
        logger.info(f"Sending {len(reviews)} initial reviews")
        for review in reviews:
            await websocket.send(json.dumps({
                "type": "review",
                **review
            }))
            await asyncio.sleep(0.5)  # Small delay between initial reviews
        
        # Handle incoming messages
        async for message in websocket:
            await handle_message(websocket, message)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client connection closed")
        await handle_disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in send_reviews: {e}")
        await handle_disconnect(websocket)

async def main():
    try:
        async with websockets.serve(send_reviews, HOST, PORT):
            logger.info(f"WebSocket server started on ws://{HOST}:{PORT}")
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
