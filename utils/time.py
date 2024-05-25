def msg_created_time(args) -> str:
    """You can get time

    Returns:
        str: time
    """
    return str(args.created_at)[0:-13]