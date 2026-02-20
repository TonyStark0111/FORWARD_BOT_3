import asyncio
import logging
from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError

from SilentXForward import database
from config import BUFFER_DELAY, FORWARD_DELAY_SECONDS, MAX_QUEUE_RETRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

message_queue: asyncio.Queue = asyncio.Queue()
message_buffer = defaultdict(list)
buffer_tasks = {}




async def handle_flood(func, **kwargs):
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            return await func(**kwargs)
        except FloodWait as e:
            logger.warning("FloodWait detected. Sleeping for %ss.", e.value)
            await asyncio.sleep(e.value + 1)
        except RPCError as e:
            retry_count += 1
            logger.error("RPCError (attempt %s/%s): %s", retry_count, max_retries, e)
            if retry_count >= max_retries:
                raise
            await asyncio.sleep(2**retry_count)
        except Exception as e:
            retry_count += 1
            logger.error("Unexpected error (attempt %s/%s): %s", retry_count, max_retries, e)
            if retry_count >= max_retries:
                raise
            await asyncio.sleep(2**retry_count)

    raise RuntimeError(f"Failed after {max_retries} retries")


async def forward_single_message(client, message, chat_id):
    try:
        kwargs = {
            "chat_id": chat_id,
            "from_chat_id": message.chat.id,
            "message_id": message.id,
        }

        if message.caption:
            kwargs["caption"] = message.caption
            if message.caption_entities:
                kwargs["caption_entities"] = message.caption_entities

        await handle_flood(client.copy_message, **kwargs)
        logger.info("Forwarded message %s from %s to %s", message.id, message.chat.id, chat_id)
        return True
    except Exception as e:
        logger.error("Error forwarding message %s to %s: %s", message.id, chat_id, e)
        return False


async def forward_buffered_messages(client, messages, chat_id):
    try:
        sorted_messages = sorted(messages, key=lambda m: m.id)
        success_count = 0

        for msg in sorted_messages:
            if await forward_single_message(client, msg, chat_id):
                success_count += 1
                await asyncio.sleep(FORWARD_DELAY_SECONDS)

        logger.info("Forwarded %s/%s buffered messages to %s", success_count, len(messages), chat_id)
        return success_count == len(messages)

    except Exception as e:
        logger.error("Error forwarding buffered messages to %s: %s", chat_id, e)
        return False


async def process_queue(client):
    while True:
        try:
            payload = await message_queue.get()
            if not payload:
                message_queue.task_done()
                continue

            messages, target_ids, retry_count = payload
            failed_targets = []

            for chat_id in target_ids:
                try:
                    success = await forward_buffered_messages(client, messages, chat_id)
                    if not success:
                        failed_targets.append(chat_id)
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    logger.warning("FloodWait for chat %s. Waiting %ss", chat_id, e.value)
                    await asyncio.sleep(e.value + 1)
                    failed_targets.append(chat_id)
                except Exception as e:
                    logger.error("Error forwarding to %s: %s", chat_id, e)
                    failed_targets.append(chat_id)

            if failed_targets:
                if retry_count < MAX_QUEUE_RETRIES:
                    logger.info(
                        "Re-queuing for %s failed target(s), retry %s/%s",
                        len(failed_targets),
                        retry_count + 1,
                        MAX_QUEUE_RETRIES,
                    )
                    await message_queue.put((messages, failed_targets, retry_count + 1))
                else:
                    logger.error(
                        "Dropping %s target(s) after max retry (%s)",
                        len(failed_targets),
                        MAX_QUEUE_RETRIES,
                    )

            message_queue.task_done()

        except Exception as e:
            logger.error("Queue processing error: %s", e)
            await asyncio.sleep(1)


async def start_processor(client):
    task = asyncio.create_task(process_queue(client))
    logger.info("Message processor started")
    return {"main_processor": task}


async def process_buffered_messages(buffer_key):
    await asyncio.sleep(BUFFER_DELAY)

    messages = message_buffer.pop(buffer_key, [])
    buffer_tasks.pop(buffer_key, None)
    if not messages:
        return

    source_chat_id = messages[0].chat.id

    try:
        mappings = await database.get_all_targets_for_source(source_chat_id)
        if not mappings:
            return

        message_count = len(messages)
        for mapping in mappings:
            target_ids = mapping.get("target_ids", [])
            if target_ids:
                await message_queue.put((messages.copy(), target_ids, 0))
                logger.info(
                    "Queued buffered group (%s message(s)) from %s for %s target(s)",
                    message_count,
                    source_chat_id,
                    len(target_ids),
                )

    except Exception as e:
        logger.error("Error processing buffered messages: %s", e)


@Client.on_message(filters.channel)
async def forward_content(client, message):
    try:
        source_chat_id = message.chat.id

        # Group album messages by media_group_id; process single messages immediately.
        if message.media_group_id:
            buffer_key = (source_chat_id, message.media_group_id)
            message_buffer[buffer_key].append(message)

            if buffer_key in buffer_tasks:
                buffer_tasks[buffer_key].cancel()
            buffer_tasks[buffer_key] = asyncio.create_task(process_buffered_messages(buffer_key))
            return

        mappings = await database.get_all_targets_for_source(source_chat_id)
        if not mappings:
            return

        for mapping in mappings:
            target_ids = mapping.get("target_ids", [])
            if target_ids:
                await message_queue.put(([message], target_ids, 0))

    except Exception as e:
        logger.error("Error in forward_content handler: %s", e, exc_info=True)
