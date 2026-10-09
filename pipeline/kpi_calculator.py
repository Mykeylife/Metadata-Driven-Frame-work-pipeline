import datetime

def compute_user_kpis(cursor, valid_users: list) -> list:
    """Processes user metrics transformations and generates aggregate reporting footprints."""
    if not valid_users:
        return []
        
    processed_metrics = []
    calculated_at = datetime.datetime.utcnow().isoformat()
    
    for username in valid_users:
        username_length = len(username) if username else 0
        processed_metrics.append((username, username_length, calculated_at))
        
    return processed_metrics
