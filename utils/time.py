async def msg_created_time(*args) -> str:
    """You can get time

    Returns:
        str: time
    """
    return str(args[0].created_at)[0:-13]