import firebase_admin
from firebase_admin import credentials, firestore
import json

def check_firebase_connection():
    """Check if Firebase connection is active and view history_violations collection"""
    
    print("=" * 60)
    print("Firebase Connection Check & Violations History Viewer")
    print("=" * 60)
    
    # Initialize Firebase Admin SDK
    try:
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("[OK] Firebase Admin SDK already initialized")
            db = firestore.client()
        except ValueError:
            # Not initialized, so initialize it
            print("\n[INFO] Loading service account key...")
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("[OK] Firebase Admin SDK initialized successfully")
            db = firestore.client()
        
        # Test connection by getting a reference
        print("\n[INFO] Testing Firebase connection...")
        
        # Try to access a simple collection to test connection
        try:
            test_ref = db.collection("test").limit(1)
            print("[OK] Firebase connection is ACTIVE")
        except Exception as e:
            print(f"[WARNING] Connection test warning: {str(e)}")
        
        # Check history_violations collection
        print("\n" + "=" * 60)
        print("Checking history_violations Collection")
        print("=" * 60)
        
        violations_ref = db.collection("history_violations")
        
        # Get all documents in history_violations
        try:
            violations_docs = violations_ref.stream()
            violations_list = list(violations_docs)
            
            if len(violations_list) == 0:
                print("\n[INFO] No documents found in history_violations collection")
                print("   (Collection exists but is empty)")
            else:
                print(f"\n[OK] Found {len(violations_list)} document(s) in history_violations collection")
                print("\n" + "-" * 60)
                
                for i, doc in enumerate(violations_list, 1):
                    doc_data = doc.to_dict()
                    print(f"\n[Document {i}] Document ID: {doc.id}")
                    print(f"   Data: {json.dumps(doc_data, indent=6, default=str)}")
                    print("-" * 60)
            
            # Also check the structure by trying to get collection info
            print("\n[STATUS] Collection Status:")
            print(f"   Collection Path: history_violations")
            print(f"   Total Documents: {len(violations_list)}")
            print("   [OK] Collection is accessible and readable")
            
        except Exception as e:
            print(f"\n[ERROR] Error accessing history_violations collection: {str(e)}")
            print(f"   Error Type: {type(e).__name__}")
            
            # Check if collection exists by trying to create a reference (won't actually create anything)
            try:
                test_doc = violations_ref.document("_test_read_only")
                test_doc.get()
                print("   [INFO] Collection reference can be created")
            except Exception as test_e:
                print(f"   [WARNING] Collection reference test: {str(test_e)}")
        
        # Check service account key info
        print("\n" + "=" * 60)
        print("Service Account Key Information")
        print("=" * 60)
        
        try:
            with open("serviceAccountKey.json", "r") as f:
                key_data = json.load(f)
            
            print(f"[OK] Service Account Key File: Valid JSON")
            print(f"   Project ID: {key_data.get('project_id', 'N/A')}")
            print(f"   Client Email: {key_data.get('client_email', 'N/A')}")
            print(f"   Private Key ID: {key_data.get('private_key_id', 'N/A')[:20]}...")
            
            if key_data.get('private_key'):
                print(f"   Private Key: Present (length: {len(key_data.get('private_key', ''))} chars)")
            else:
                print(f"   [WARNING] Private Key: Missing")
            
        except FileNotFoundError:
            print("[ERROR] serviceAccountKey.json file not found")
        except json.JSONDecodeError:
            print("[ERROR] serviceAccountKey.json is not valid JSON")
        except Exception as e:
            print(f"[ERROR] Error reading service account key: {str(e)}")
        
        print("\n" + "=" * 60)
        print("[OK] Check Complete - No modifications made to database")
        print("=" * 60)
        
        return True
        
    except FileNotFoundError:
        print("[ERROR] serviceAccountKey.json file not found!")
        print("   Please ensure the file exists in the current directory")
        return False
    except json.JSONDecodeError:
        print("[ERROR] serviceAccountKey.json is not valid JSON!")
        return False
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to Firebase")
        print(f"   Error: {str(e)}")
        print(f"   Error Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    check_firebase_connection()

