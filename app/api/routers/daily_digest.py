from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter
from datetime import date
import logging

from app.db.db_actions import Action
from app.service.aws_service import DynamoDB
from app.service.redis_service import redis_client
from app.task.digest_task import create_daily_digest

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

daily_digest_router = r = APIRouter()

database_action = Action()
dynamo_db = DynamoDB()


# Model for user interests input
class RequestBody(BaseModel):
    user_id: str = Field(..., description="user_id of the current user")
    categories: List[str] = Field(..., description="User's preferred categories")
    interests: str = Field(..., description="Specific interests of the user")


def todays_date():
    return date.today().strftime("%d-%m-%Y")


def get_task_id(user_id: str, date: str):
    return f"{user_id}-{date}"


def is_task_in_queue(task_id):
    # Check if the task ID is already in the queue
    return redis_client.exists(task_id)


@r.post("/dailydigest")
async def daily_digest(request: RequestBody):
    user_id = request.user_id
    categories = request.categories
    interests = request.interests
    date = todays_date()

    # if digest already exists then fetch
    digest = dynamo_db.get_digest(user_id, date)

    if digest:
        print("Digest found, returning digest")
        return digest

    # check if digest exists in Redis
    task_id = get_task_id(user_id, date)

    if is_task_in_queue(task_id):
        return {
            "digest": f"In Progress: Digest creation already in progress for {user_id} on {date}"
        }

    # Set a key in Redis to indicate the task is queued
    redis_client.set(task_id, "in_progress", ex=900)  # expire in 15 minutes

    print("Digest not found, creating new digest")
    # convert cs.ai -> cs.AI
    categories = list(
        map(lambda x: x.split(".")[0] + "." + x.split(".")[1].upper(), categories)
    )

    # get relevant papers -- Run the task
    create_daily_digest.apply_async(
        args=(categories, interests, user_id, date), queue="digestq", task_id=task_id
    )

    return {"digest": f"We've recieved your request for {user_id} on {date}"}
