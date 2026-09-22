def lambda_handler(event, context):
    object_key = event.get("object_key", "")

    allowed_extensions = [".jpg", ".jpeg", ".png"]

    if not any(object_key.lower().endswith(ext) for ext in allowed_extensions):
        raise Exception("Unsupported image format")

    return {
        "status": "VALID",
        "object_key": object_key
    }