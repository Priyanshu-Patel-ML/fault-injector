import os
from logzero import logger
from typing import Optional
from pymongo import MongoClient

__all__ = ["count_posts_direct", "cleanup_database_direct", "auto_cleanup_if_needed"]

def count_posts_direct(db_host: str, db_port: int = 27017, database_name: str = "post", collection_name: str = "post"):
    """Count posts directly via MongoDB connection"""
    try:
        client = MongoClient(f"mongodb://{db_host}:{db_port}/{database_name}", serverSelectionTimeoutMS=5000)
        collection = client[database_name][collection_name]
        total_count = collection.count_documents({})
        client.close()
        logger.info(f"📊 Total posts: {total_count}")
        return {"status": "success", "total_posts": total_count}
    except Exception as e:
        logger.error(f"Failed to count posts: {e}")
        return {"status": "error", "total_posts": -1, "message": str(e)}

def cleanup_database_direct(db_host: str, db_port: int = 27017, database_name: str = "post", 
                          collection_name: str = "post", keep_count: int = 10000, dry_run: bool = False):
    """Clean up database - keep only latest N records"""
    try:
        client = MongoClient(f"mongodb://{db_host}:{db_port}/{database_name}", serverSelectionTimeoutMS=5000)
        collection = client[database_name][collection_name]
        total_count = collection.count_documents({})
        logger.info(f"📊 Total posts before cleanup: {total_count}")
        
        if total_count <= keep_count:
            client.close()
            logger.info(f"✅ Only {total_count} posts, no cleanup needed")
            return {"status": "success", "posts_deleted": 0, "message": "No cleanup needed"}
        
        if dry_run:
            client.close()
            posts_to_delete = total_count - keep_count
            logger.info(f"🗑️ DRY RUN: Would delete {posts_to_delete} posts")
            return {"status": "success", "posts_deleted": 0, "dry_run": True, "would_delete": posts_to_delete}
        
        # Keep only latest N records (sorted by _id which contains timestamp)
        latest_posts = list(collection.find().sort("_id", -1).limit(keep_count))
        if len(latest_posts) == keep_count:
            oldest_id = latest_posts[-1]["_id"]
            result = collection.delete_many({"_id": {"$lt": oldest_id}})
            deleted_count = result.deleted_count
        else:
            deleted_count = 0
        
        client.close()
        logger.info(f"✅ Deleted {deleted_count} posts, kept {keep_count} latest posts")
        return {"status": "success", "posts_deleted": deleted_count, "posts_remaining": total_count - deleted_count}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "error", "posts_deleted": 0, "message": str(e)}

def auto_cleanup_if_needed(db_host: str, db_port: int = 27017, database_name: str = "post", 
                          collection_name: str = "post", threshold: int = 10000, keep_count: int = 10000):
    """
    Automatically cleanup database if record count exceeds threshold.
    This function checks first, then cleans up only if needed.
    Parameters:
    - threshold: If total records > threshold, trigger cleanup
    - keep_count: How many latest records to keep after cleanup
    """
    try:
        logger.info(f"🔍 Starting auto-cleanup check...")
        logger.info(f"📋 Database: {db_host}:{db_port}/{database_name}.{collection_name}")
        logger.info(f"📊 Threshold: {threshold}, Keep count: {keep_count}")
        
        # First, count current records
        count_result = count_posts_direct(db_host, db_port, database_name, collection_name)
        if count_result["status"] != "success":
            logger.error("❌ Failed to count posts, cannot proceed with cleanup")
            return count_result
        
        total_posts = count_result["total_posts"]
        logger.info(f"📊 Current post count: {total_posts}")
        
        if total_posts <= threshold:
            logger.info(f"✅ Post count ({total_posts}) is within threshold ({threshold}), no cleanup needed")
            return {
                "status": "success", 
                "cleanup_performed": False,
                "total_posts": total_posts,
                "posts_deleted": 0,
                "threshold": threshold,
                "message": f"No cleanup needed - {total_posts} posts within threshold of {threshold}"
            }
        
        # Cleanup needed
        posts_to_delete = total_posts - keep_count
        logger.info(f"🗑️ Post count ({total_posts}) exceeds threshold ({threshold})")
        logger.info(f"🧹 Starting cleanup: will delete {posts_to_delete} posts, keep latest {keep_count}")
        
        cleanup_result = cleanup_database_direct(db_host, db_port, database_name, collection_name, keep_count, dry_run=False)
        
        if cleanup_result["status"] == "success":
            logger.info(f"✅ Auto-cleanup completed successfully!")
            logger.info(f"📊 Deleted: {cleanup_result['posts_deleted']} posts")
            logger.info(f"📊 Remaining: {cleanup_result.get('posts_remaining', 'unknown')} posts")
            return {
                "status": "success",
                "cleanup_performed": True,
                "total_posts_before": total_posts,
                "posts_deleted": cleanup_result["posts_deleted"],
                "posts_remaining": cleanup_result.get("posts_remaining", total_posts - cleanup_result["posts_deleted"]),
                "threshold": threshold,
                "keep_count": keep_count,
                "message": f"Cleanup completed - deleted {cleanup_result['posts_deleted']} posts"
            }
        else:
            logger.error(f"❌ Auto-cleanup failed: {cleanup_result.get('message', 'Unknown error')}")
            return {
                "status": "error",
                "cleanup_performed": False,
                "total_posts_before": total_posts,
                "threshold": threshold,
                "message": f"Cleanup failed: {cleanup_result.get('message', 'Unknown error')}"
            }
    except Exception as e:
        logger.error(f"Auto-cleanup failed with exception: {e}")
        return {
            "status": "error", 
            "cleanup_performed": False, 
            "message": f"Exception during auto-cleanup: {str(e)}"
        }