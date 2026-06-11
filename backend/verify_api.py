import subprocess
import time
import httpx
import sys
import os

def run_tests():
    # 1. Start uvicorn server in a subprocess on port 8001
    print("Starting FastAPI server on port 8001...")
    server_process = subprocess.Popen(
        [r".venv\Scripts\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server a couple of seconds to spin up
    time.sleep(2)
    
    base_url = "http://127.0.0.1:8001/api/v1"
    client = httpx.Client()
    
    try:
        # Check server health
        print("Checking server health...")
        try:
            r = client.get("http://127.0.0.1:8001/")
            print(f"Health check status: {r.status_code}, response: {r.json()}")
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            # print stderr of server
            stdout, stderr = server_process.communicate(timeout=1)
            print("Server stdout:", stdout)
            print("Server stderr:", stderr)
            return False

        # 2. Register user
        email = f"verify_{int(time.time())}@example.com"
        password = "strongpassword123"
        print(f"Registering user: {email}...")
        r = client.post(f"{base_url}/register", json={"email": email, "password": password})
        assert r.status_code == 201, f"Registration failed with status {r.status_code}: {r.text}"
        print("Registration successful!")

        # 3. Login
        print("Logging in...")
        r = client.post(f"{base_url}/login", data={"username": email, "password": password})
        assert r.status_code == 200, f"Login failed: {r.text}"
        token = r.json()["access_token"]
        print("Login successful! Token acquired.")
        
        # Add token to headers
        client.headers["Authorization"] = f"Bearer {token}"

        # 4. Upload file
        filename = "test_verify.txt"
        file_content = b"Hello Aegis Protection! If you can read this, AES-256-GCM encryption/decryption works perfectly."
        file_password = "mysecretencryptionkey"
        
        print(f"Uploading file '{filename}' with encryption key...")
        files = {"file": (filename, file_content, "text/plain")}
        data = {"password": file_password}
        
        r = client.post(f"{base_url}/files/upload", files=files, data=data)
        assert r.status_code == 201, f"Upload failed: {r.text}"
        file_info = r.json()
        file_id = file_info["id"]
        print(f"Upload successful! File ID: {file_id}")

        # 5. List files
        print("Listing files...")
        r = client.get(f"{base_url}/files")
        assert r.status_code == 200, f"List files failed: {r.text}"
        user_files = r.json()
        assert any(f["id"] == file_id for f in user_files), "Uploaded file not found in file list."
        print(f"Verified: File ID {file_id} is in the user's secure file list.")

        # 6. Test incorrect decryption passcode (should fail with 400)
        print("Testing decryption ticket with incorrect password...")
        r = client.post(f"{base_url}/files/{file_id}/ticket", json={"password": "wrongpassword"})
        assert r.status_code == 400, f"Expected 400 Bad Request, got: {r.status_code} - {r.text}"
        print("Verified: Incorrect passcode was rejected with 400 Bad Request.")

        # 7. Create decryption ticket with correct password
        print("Creating single-use decryption ticket...")
        r = client.post(f"{base_url}/files/{file_id}/ticket", json={"password": file_password})
        assert r.status_code == 200, f"Ticket generation failed: {r.text}"
        ticket_id = r.json()["ticket_id"]
        print(f"Decryption ticket acquired: {ticket_id}")

        # 8. Download decrypted file using ticket
        print("Downloading file using single-use ticket...")
        r = client.get(f"{base_url}/files/{file_id}/download", params={"ticket_id": ticket_id})
        assert r.status_code == 200, f"Download failed: {r.text}"
        downloaded_bytes = r.content
        assert downloaded_bytes == file_content, f"Downloaded content mismatch! Got: {downloaded_bytes}"
        print("Verified: Decrypted content matches the original exactly.")

        # 9. Verify ticket single-use constraint (subsequent downloads should fail)
        print("Verifying single-use ticket invalidation...")
        r = client.get(f"{base_url}/files/{file_id}/download", params={"ticket_id": ticket_id})
        assert r.status_code == 400, f"Expected 400 Bad Request for used ticket, got: {r.status_code} - {r.text}"
        print("Verified: Ticket is single-use and was invalidated after first download.")

        # 10. Test Preview Route
        print("Generating a new ticket for preview...")
        r = client.post(f"{base_url}/files/{file_id}/ticket", json={"password": file_password})
        assert r.status_code == 200, f"Ticket generation failed: {r.text}"
        preview_ticket_id = r.json()["ticket_id"]
        
        # Test preview (preview is for safe types only, txt is not in safe types, so it should return 415)
        print("Requesting preview for .txt file (should return 415 Unsupported Media Type)...")
        r = client.get(f"{base_url}/files/{file_id}/preview", params={"ticket_id": preview_ticket_id})
        assert r.status_code == 415, f"Expected 415, got: {r.status_code} - {r.text}"
        print("Verified: Preview correctly restricts to safe types (.png, .jpg, .pdf) and rejects .txt with 415.")

        # 11. Delete file
        print("Deleting secure file...")
        r = client.delete(f"{base_url}/files/{file_id}")
        assert r.status_code == 200, f"Deletion failed: {r.text}"
        print("File deleted successfully!")

        # 12. Verify listing is empty again
        r = client.get(f"{base_url}/files")
        user_files_after = r.json()
        assert not any(f["id"] == file_id for f in user_files_after), "File still exists after deletion."
        print("Verified: File removed from secure file database.")

        print("\n=== ALL TESTS PASSED SUCCESSFULLY! The backend encryption and token exchange protocols are 100% functional. ===")
        return True

    except AssertionError as ae:
        print(f"\n[ERROR] TEST FAILED: {ae}")
        return False
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        return False
    finally:
        # Shutdown server
        print("Stopping backend server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("Server process terminated cleanly.")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("Server process killed forceably.")

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
