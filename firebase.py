import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase Initialization
def initialize_firebase():
    """
    Initialize Firebase with a service account key.
    Avoids re-initializing if Firebase is already initialized.
    """
    try:
        cred = credentials.Certificate('serviceAccount.json')  # Update path to your credentials file
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully.")
    except ValueError:
        logger.info("Firebase already initialized.")

# Initialize Firestore client
def get_firestore_client():
    """
    Returns the Firestore client.
    Ensures Firebase is initialized before accessing Firestore.
    """
    initialize_firebase()
    return firestore.client()

# Grievance Management Functions
def add_grievance(data):
    """
    Adds a new grievance to the Firestore 'grievances' collection.
    Args:
        data (dict): Grievance details (category, description, anonymous, etc.).
    Returns:
        str: Document ID of the new grievance.
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection('grievances').add(data)
        logger.info(f"Grievance added successfully with ID: {doc_ref[1].id}")
        return doc_ref[1].id
    except Exception as e:
        logger.error(f"Error adding grievance: {e}")
        raise

def get_all_grievances():
    """
    Fetches all grievances from the Firestore 'grievances' collection.
    Returns:
        list: List of grievances.
    """
    try:
        db = get_firestore_client()
        grievances = db.collection('grievances').stream()
        grievance_list = [{"id": g.id, **g.to_dict()} for g in grievances]
        logger.info(f"Fetched {len(grievance_list)} grievances successfully.")
        return grievance_list
    except Exception as e:
        logger.error(f"Error fetching grievances: {e}")
        return []

def update_grievance(grievance_id, updates):
    """
    Updates a specific grievance document in Firestore.
    Args:
        grievance_id (str): Document ID of the grievance.
        updates (dict): Fields to update (e.g., status, response).
    """
    try:
        db = get_firestore_client()
        grievance_ref = db.collection('grievances').document(grievance_id)
        grievance_ref.update(updates)
        logger.info(f"Grievance updated successfully: {grievance_id}")
    except Exception as e:
        logger.error(f"Error updating grievance: {e}")
        raise

def get_grievance_by_id(grievance_id):
    """
    Fetches a specific grievance by its ID.
    Args:
        grievance_id (str): Document ID of the grievance.
    Returns:
        dict: Grievance data.
    """
    try:
        db = get_firestore_client()
        grievance_ref = db.collection('grievances').document(grievance_id)
        grievance = grievance_ref.get()
        if grievance.exists:
            logger.info(f"Grievance fetched successfully: {grievance_id}")
            return grievance.to_dict()
        else:
            logger.warning(f"Grievance not found: {grievance_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching grievance: {e}")
        return None
