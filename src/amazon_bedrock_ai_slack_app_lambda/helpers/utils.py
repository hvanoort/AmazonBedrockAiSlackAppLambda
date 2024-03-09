def get_sorted_messages(messages: list):
    """
    Sort a list of messages by their timestamp in ascending order.

    :param messages: A list of messages, each represented as a dictionary.
                     Each message dictionary should contain 'ts', 'user', and 'text' keys.
    :return: A new list of messages sorted by timestamp.
    """

    last_new_conversation_index = None
    for i in range(len(messages) - 1):
        if messages[i].get("text") == 'new-conversation':
            last_new_conversation_index = i
            break

    if last_new_conversation_index is not None:
        filtered_messages = [
            {"ts": msg["ts"], "user": msg["user"], "msg": msg["text"]}
            for msg in messages[:last_new_conversation_index]
            if "subtype" not in msg
        ]

        return sorted(filtered_messages, key=lambda x: float(x["ts"]))
    else:
        return sorted(
            [
                {"ts": msg["ts"], "user": msg["user"], "msg": msg["text"]}
                for msg in messages
                if "subtype" not in msg
            ],
            key=lambda x: float(x["ts"]),
        )


def validate_and_set(value, available_values, default_value, existing_value):
    """
    Validate a value against a set of available values. If the value is not in the available values,
    send an invalid message and return the default value.

    :param value: The value to validate.
    :param available_values: The set of available values.
    :param default_value: The default value to return if the validation fails.

    Returns:
        The existing value, validated value or default value.
    """

    if not value:
        return existing_value

    if value not in available_values:
        return None

    return value


def check_if_mentioning_bot(event, bot_user_id):
    """
    Check if a specific bot user is mentioned in the given event.

    Parameters:
    - event (dict): The event containing information about the message.
    - bot_user_id (str): The user ID of the bot to check for mentions.

    Returns:
    - bool: True if the bot is mentioned, False otherwise.
    """
    for block in event.get('blocks', []):
        elements = block.get("elements", [])
        for element in elements:
            if element.get("type") == "rich_text_section":
                user_elements = element.get("elements", [])
                for user_element in user_elements:
                    if (
                        user_element.get("type") == "user" and user_element.get("user_id") == bot_user_id
                    ):
                        return True

    return False


def get_thread_ts(channel_attr):
    """
    Determine if a message was sent in a channel/group/mpim or IM.

    Parameters:
    - channel_attr (dict): Channel attributes dictionary containing channel type and parent timestamp.

    Returns:
    - float or None: Timestamp if in a channel/group/mpim, otherwise None.
    """
    if channel_attr.get('channel_type') != 'im':
        return channel_attr.get('thread_ts') if channel_attr.get('thread_ts') else channel_attr.get('parent_ts')
    else:
        return None
