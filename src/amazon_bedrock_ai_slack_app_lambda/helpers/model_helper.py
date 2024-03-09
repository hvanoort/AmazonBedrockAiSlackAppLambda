def get_model(model_name):
    """
    Retrieve model information based on the provided model name.

    :param model_name: The name of the language model.
    :return: A dictionary containing information about the specified model.
    """
    model_info = {
        "amazon.titan-text-express-v1": {
            "name": "titan",
            "id": "amazon.titan-tg1-large",
            "accept": "*/*",
            "content_type": "application/json",
            "max_token_sample": 750,
        },
        "anthropic.claude-v2:1": {
            "name": "claude-v2",
            "id": "anthropic.claude-v2:1",
            "accept": "application/json",
            "content_type": "application/json",
            "max_token_sample": 750,
        },
        "anthropic.claude-instant-v1": {
            "name": "claude-instant",
            "id": "anthropic.claude-instant-v1",
            "accept": "application/json",
            "content_type": "application/json",
            "max_token_sample": 750,
        },
        "anthropic.claude-3-sonnet-20240229-v1:0": {
            "name": "claude-v3-sonet",
            "id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "accept": "application/json",
            "content_type": "application/json",
            "max_token_sample": 750,
            "temperature": 0.5
        },
        "meta.llama2-13b-chat-v1": {
            "name": "llama2",
            "id": "meta.llama2-13b-chat-v1",
            "accept": "application/json",
            "content_type": "application/json",
            "max_token_sample": 750,
        },
    }

    return model_info.get(model_name, None)
