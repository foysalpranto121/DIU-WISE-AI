import sys
import traceback

try:
    from factory import create_app
    app = create_app()
    print("✓ App created successfully")

    with app.app_context():
        with app.test_client() as client:
            response = client.get('/')
            print(f"Status: {response.status_code}")
            print(f"Data: {response.data[:500]}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
